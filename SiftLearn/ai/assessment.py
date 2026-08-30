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


def assess_answer(subject, question, answer):
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

    raw = generate(prompt)
    raw = _strip_json_fences(raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(
            "Gemini returned invalid assessment JSON."
        ) from error

    return validate_assessment(result)
