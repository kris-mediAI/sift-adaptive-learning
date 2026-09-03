"""Canonical Sift assessment adapter and validation boundary."""

import json
import math

VALID_MISTAKE_TYPES = {
    "conceptual",
    "calculation",
    "misread",
    "careless",
    "prerequisite",
    "none",
}

REQUIRED_FIELDS = {
    "score",
    "correct",
    "concept",
    "mistake_type",
    "misconception",
    "confidence",
    "explanation",
    "next_concept",
}


def _strip_json_fences(raw):
    text = str(raw).strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().lower() in {"```", "```json"}:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _finite_number(value, field):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Assessment {field} must be numeric.") from exc
    if not math.isfinite(number):
        raise ValueError(f"Assessment {field} must be finite.")
    return number


def validate_assessment(result):
    """Validate and normalize assessment evidence before it enters Sift."""
    if not isinstance(result, dict):
        raise ValueError("Assessment response must be a JSON object.")

    missing = REQUIRED_FIELDS - result.keys()
    if missing:
        raise ValueError(
            "Assessment is missing fields: " + ", ".join(sorted(missing))
        )

    score = _finite_number(result["score"], "score")
    confidence = _finite_number(result["confidence"], "confidence")

    if not 0 <= score <= 100:
        raise ValueError("Assessment score must be between 0 and 100.")
    if not 0 <= confidence <= 100:
        raise ValueError("Assessment confidence must be between 0 and 100.")

    if not isinstance(result["correct"], bool):
        raise ValueError("Assessment correct must be boolean.")

    concept = str(result["concept"]).strip()
    if not concept:
        raise ValueError("Assessment concept cannot be empty.")

    mistake_type = str(result["mistake_type"]).strip().lower()
    if mistake_type not in VALID_MISTAKE_TYPES:
        raise ValueError(
            "Assessment mistake_type must be one of: "
            + ", ".join(sorted(VALID_MISTAKE_TYPES))
        )

    misconception = result["misconception"]
    explanation = result["explanation"]
    next_concept = result["next_concept"]
    strengths = result.get("strengths", [])
    gaps = result.get("gaps", [])
    recommended_help = result.get("recommended_help", "retry")

    if misconception is None:
        misconception = ""
    if explanation is None:
        explanation = ""
    if next_concept is None:
        next_concept = ""

    misconception = str(misconception).strip()
    explanation = str(explanation).strip()
    next_concept = str(next_concept).strip()

    if not isinstance(strengths, list):
        strengths = [str(strengths)] if strengths else []
    if not isinstance(gaps, list):
        gaps = [str(gaps)] if gaps else []
    strengths = [str(item).strip() for item in strengths if str(item).strip()][0:5]
    gaps = [str(item).strip() for item in gaps if str(item).strip()][0:5]
    recommended_help = str(recommended_help or "retry").strip().lower()
    if recommended_help not in {"hint", "explanation", "worked_example", "practice", "video", "retry", "advance"}:
        recommended_help = "retry"

    # A correct answer is never allowed to carry negative evidence.
    if result["correct"]:
        mistake_type = "none"
        misconception = ""

    return {
        "score": int(round(score)),
        "correct": result["correct"],
        "concept": concept,
        "mistake_type": mistake_type,
        "misconception": misconception,
        "confidence": int(round(confidence)),
        "explanation": explanation,
        "next_concept": next_concept,
        "strengths": strengths,
        "gaps": gaps,
        "recommended_help": (
            "advance" if result["correct"] and recommended_help == "retry"
            else recommended_help
        ),
    }


def assess_answer(subject, question, answer, fallback_concept=""):

    """Analyze a student's answer and return trusted structured evidence."""
    if not str(subject).strip():
        raise ValueError("Assessment subject cannot be empty.")
    if not str(question).strip():
        raise ValueError("Assessment question cannot be empty.")
    if not str(answer).strip():
        raise ValueError("Assessment answer cannot be empty.")

    prompt = f"""
You are the assessment engine inside Sift Learn.

Your job is to understand the student's actual knowledge,
not simply decide whether the answer is right or wrong.

Subject:
{subject}

Question:
{question}

Student answer:
{answer}

Current target concept (use this as the assessment anchor when provided):
{fallback_concept or "Use the concept most directly evidenced by the question."}

Return ONLY valid JSON.

Use exactly this structure:

{{
    "score": 0,
    "correct": false,
    "concept": "main concept being tested",
    "mistake_type": "conceptual|calculation|misread|careless|prerequisite|none",
    "misconception": "specific misunderstanding, or empty string if none",
    "confidence": 0,
    "explanation": "short explanation appropriate for this learner",
    "next_concept": "the most useful concept to work on next",
    "strengths": ["specific demonstrated understanding"],
    "gaps": ["specific missing or weak evidence"],
    "recommended_help": "hint|explanation|worked_example|practice|video|retry|advance"
}}

Rules:
- score must be an integer from 0 to 100.
- confidence must be an integer from 0 to 100.
- Give partial credit when appropriate.
- Identify the student's actual misconception when possible.
- If the student is correct, mistake_type must be "none".
- Do not invent a misconception when the answer is correct.
- Keep explanations concise.
- Focus on evidence from the student's answer.
- Do not invent facts that are not supported by the question or answer.
- List only observable strengths and gaps; do not reveal hidden chain-of-thought.
- Choose one recommended_help value that would best help the learner improve.
- Use "advance" only when the answer provides sufficient evidence to move forward.
"""

    # Lazy import keeps schema validation usable in tests/tools that
    # do not need a live Gemini connection.
    from ai.gemini import generate

    def _parse_and_validate(raw_text):
        cleaned = _strip_json_fences(raw_text)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Gemini returned invalid assessment JSON."
            ) from error
        return validate_assessment(parsed)

    # Gemini occasionally returns malformed/truncated structured output even
    # when the underlying request succeeds.  Treat that as a recoverable
    # formatting failure: make one fresh, explicit JSON-repair request before
    # surfacing an evaluation error to the learner.  The repaired response
    # still has to pass the same strict validation boundary.
    first_raw = None
    try:
        first_raw = generate(prompt)
        return _parse_and_validate(first_raw)
    except (ValueError, RuntimeError) as first_error:
        repair_prompt = f"""
You are repairing a structured assessment response for Sift.

Return ONLY one valid JSON object with exactly these fields:
score, correct, concept, mistake_type, misconception, confidence,
explanation, next_concept, strengths, gaps, recommended_help.

Original assessment request:
{prompt}

Previous model output:
{str(first_raw or first_error)[:12000]}

Do not add markdown fences, commentary, or extra keys.
Keep the assessment grounded in the student's question and answer.
"""
        try:
            return _parse_and_validate(generate(repair_prompt))
        except (ValueError, RuntimeError):
            # A learner saying they do not know is itself valid evidence.
            # If the AI service is temporarily unavailable, preserve the
            # learning loop for this explicit low-information case instead
            # of turning a transient infrastructure failure into a dead end.
            # The session layer still canonicalizes/validates the concept
            # against its registered graph before changing learner state.
            uncertainty = {
                "idk",
                "i don't know",
                "i dont know",
                "don't know",
                "dont know",
                "not sure",
                "no idea",
                "i have no idea",
                "skip",
                "pass",
            }
            normalized_answer = " ".join(str(answer).strip().lower().split())
            if fallback_concept and normalized_answer in uncertainty:
                return validate_assessment({
                    "score": 0,
                    "correct": False,
                    "concept": str(fallback_concept or "unknown").strip() or "unknown",
                    "mistake_type": "prerequisite",
                    "misconception": "The learner did not provide enough evidence to demonstrate the concept yet.",
                    "confidence": 100,
                    "explanation": "No problem — Sift will use this as a signal to slow down and teach the concept before checking again.",
                    "next_concept": str(fallback_concept or "").strip(),
                    "strengths": [],
                    "gaps": ["demonstrating the current concept"],
                    "recommended_help": "explanation",
                })
            raise first_error
