"""Central Gemini client with bounded retry handling."""

import logging
import os
import time

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

client = None

def _get_client():
    global client
    if client is not None:
        return client
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
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
FALLBACK_MODEL = os.getenv(
    "GEMINI_FALLBACK_MODEL",
    "gemini-2.5-flash-lite",
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
    code = getattr(error, "code", None)
    if status in {408, 409, 425, 429, 500, 502, 503, 504}:
        return True
    if code in {408, 409, 425, 429, 500, 502, 503, 504}:
        return True

    text = str(error).lower()
    return any(
        marker in text
        for marker in (
            "rate limit",
            "too many requests",
            "resource exhausted",
            "resource_exhausted",
            "temporarily unavailable",
            "service unavailable",
            "unavailable",
            "deadline",
            "timed out",
            "timeout",
            "connection reset",
            "connection aborted",
            "connection error",
            "empty text",
            "empty response",
        )
    )


def generate(prompt):
    """Send a prompt to Gemini with bounded retries and model failover.

    A fresh learner can hit a transient/model-specific quota issue even when
    the same application works for an existing learner. The client therefore
    retries the primary model and, for retryable failures only, makes one
    bounded attempt on the configured fallback model. Non-transient failures
    still surface immediately.
    """
    if not prompt or not str(prompt).strip():
        raise ValueError("Gemini prompt cannot be empty.")

    last_error = None
    models = [MODEL]
    if FALLBACK_MODEL and FALLBACK_MODEL != MODEL:
        models.append(FALLBACK_MODEL)

    for model_index, model_name in enumerate(models):
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = _get_client().models.generate_content(
                    model=model_name,
                    contents=str(prompt),
                )

                text = getattr(response, "text", None)
                if not text or not text.strip():
                    raise RuntimeError("Gemini returned empty text.")

                return text.strip()

            except Exception as error:
                last_error = error
                retryable = _is_retryable(error)

                if not retryable:
                    raise RuntimeError(
                        f"Gemini generation failed on {model_name} after {attempt + 1} attempt(s)."
                    ) from error

                if attempt < MAX_RETRIES:
                    delay = BASE_BACKOFF_SECONDS * (2 ** attempt)
                    logger.warning(
                        "Transient Gemini failure on %s; retrying in %.2fs (attempt %s/%s): %s",
                        model_name, delay, attempt + 1, MAX_RETRIES + 1, error,
                    )
                    time.sleep(delay)
                elif model_index + 1 < len(models):
                    logger.warning(
                        "Gemini primary model %s remained unavailable; failing over to %s: %s",
                        model_name, models[model_index + 1], error,
                    )
                    time.sleep(BASE_BACKOFF_SECONDS)

    raise RuntimeError("Gemini generation failed after retries and model failover.") from last_error
