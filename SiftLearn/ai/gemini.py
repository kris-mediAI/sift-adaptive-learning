"""Central Gemini client with bounded retry handling."""

import logging
import os
import time

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = None

def _get_client():
    global client
    if client is not None:
        return client
    if not api_key:
        raise RuntimeError(
            "Gemini is not configured. Set GEMINI_API_KEY or GOOGLE_API_KEY."
        )
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError(
            "Gemini SDK is not installed. Run: python -m pip install google-genai"
        ) from exc
    client = genai.Client(api_key=api_key)
    return client

MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite",
)

MAX_RETRIES = max(
    0,
    int(os.getenv("GEMINI_MAX_RETRIES", "2")),
)

BASE_BACKOFF_SECONDS = max(
    0.1,
    float(os.getenv("GEMINI_RETRY_BACKOFF", "1.0")),
)


def _is_retryable(error):
    """Best-effort classification without depending on SDK internals."""
    status = getattr(error, "status_code", None)
    if status in {408, 409, 425, 429, 500, 502, 503, 504}:
        return True

    text = str(error).lower()
    return any(
        marker in text
        for marker in (
            "rate limit",
            "too many requests",
            "temporarily unavailable",
            "service unavailable",
            "deadline",
            "timed out",
            "timeout",
            "connection reset",
        )
    )


def generate(prompt):
    """Send a prompt to Gemini with bounded transient-error retries."""
    if not prompt or not str(prompt).strip():
        raise ValueError("Gemini prompt cannot be empty.")

    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = _get_client().models.generate_content(
                model=MODEL,
                contents=str(prompt),
            )

            text = getattr(response, "text", None)
            if not text or not text.strip():
                raise RuntimeError("Gemini returned empty text.")

            return text.strip()

        except Exception as error:
            last_error = error

            if attempt >= MAX_RETRIES or not _is_retryable(error):
                raise RuntimeError(
                    f"Gemini generation failed after {attempt + 1} attempt(s)."
                ) from error

            delay = BASE_BACKOFF_SECONDS * (2 ** attempt)
            logger.warning(
                "Transient Gemini failure; retrying in %.2fs (attempt %s/%s): %s",
                delay,
                attempt + 1,
                MAX_RETRIES + 1,
                error,
            )
            time.sleep(delay)

    raise RuntimeError("Gemini generation failed.") from last_error
