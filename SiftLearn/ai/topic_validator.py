"""AI-assisted topic/learning-intent validation for session creation."""

import json
import re


VAGUE_INPUTS = {
    "idk", "i don't know", "i dont know", "dont know", "don't know",
    "help", "help me", "anything", "whatever", "nothing", "???", "?",
    "teach me", "learn", "something", "no idea", "not sure", "unsure",
}


def _clean(text):
    return " ".join(str(text or "").strip().split())


def _parse(raw):
    text = str(raw).strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().lower() in {"```", "```json"}:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


def _fallback(subject, topic, syllabus_topics):
    """Safe offline fallback when Gemini is unavailable."""
    value = _clean(topic)
    lowered = value.casefold()
    if lowered in VAGUE_INPUTS or len(re.sub(r"[^a-zA-Z0-9]", "", value)) < 2:
        return {
            "accepted": False,
            "needs_clarification": True,
            "normalized_topic": "",
            "reason": "That is too vague to identify a learning topic.",
        }

    # Syllabus selections are known-good for the current subject.
    for item in syllabus_topics or []:
        if lowered == _clean(item).casefold():
            return {
                "accepted": True,
                "needs_clarification": False,
                "normalized_topic": _clean(item),
                "reason": "Selected from the subject syllabus.",
            }

    # Strong signals that this is a meaningful learning request even when it
    # does not exactly match a syllabus node.
    words = set(re.findall(r"[a-zA-Z0-9]+", lowered))
    subject_words = set(re.findall(r"[a-zA-Z0-9]+", subject.casefold()))
    request_words = {"learn", "understand", "explain", "practice", "prepare", "interview", "exam", "test", "problem", "with", "about"}
    if len(words & request_words) or words & subject_words or len(words) >= 2:
        return {
            "accepted": True,
            "needs_clarification": False,
            "normalized_topic": value,
            "reason": "Recognized as a specific learning request.",
        }

    return {
        "accepted": False,
        "needs_clarification": True,
        "normalized_topic": "",
        "reason": "Sift could not confidently identify a learning topic.",
    }


def validate_learning_input(subject, topic, syllabus_topics=None):
    """Determine whether user input is a meaningful learning request.

    Gemini is used when configured. A deterministic fallback keeps session
    creation functional in offline/test environments.
    """
    subject = _clean(subject)
    topic = _clean(topic)
    if not subject:
        raise ValueError("A subject is required.")
    if not topic:
        return _fallback(subject, topic, syllabus_topics)

    fallback = _fallback(subject, topic, syllabus_topics)
    # Obvious non-input is rejected deterministically. Likewise, explicit
    # learning-intent phrases such as "I don't understand recursion" are
    # already unambiguous enough to accept without making session creation
    # depend on an API round-trip. Gemini is reserved for ambiguous inputs
    # where semantic relevance actually needs to be checked.
    if topic.casefold() in VAGUE_INPUTS:
        return fallback
    if fallback["accepted"] and any(
        marker in topic.casefold()
        for marker in (
            "learn ", "understand ", "explain ", "practice ", "prepare ",
            "interview", "exam", "test", "i don't understand",
            "i dont understand", "help me with ", "teach me "
        )
    ):
        return fallback

    try:
        from ai.gemini import generate
        prompt = f"""
You are Sift's learning-intent validator. Determine whether a learner's input
is a meaningful request for a tutoring session under the subject below.

Subject: {subject}
Syllabus topics (examples, not a restriction): {json.dumps(list(syllabus_topics or [])[:30])}
Learner input: {topic}

Return ONLY JSON with exactly these fields:
{{
  "accepted": true|false,
  "needs_clarification": true|false,
  "normalized_topic": "short topic or learning objective",
  "reason": "short learner-facing reason"
}}

Rules:
- Reject meaningless, conversational, or empty inputs such as "idk", "help",
  "anything", "whatever", "???", or "I don't know" when they contain no
  actual learning intent.
- Accept a concrete topic even if it is not in the syllabus.
- Accept a learning goal such as "prepare for a DSA interview".
- Accept statements of difficulty such as "I don't understand recursion";
  normalize that to the underlying topic while preserving the difficulty in
  the reason if useful.
- The syllabus is guidance, not a cage.
- Do not reject a valid topic merely because it is not a listed syllabus item.
- If the input is too vague to know what to teach, set needs_clarification true.
- Never invent a topic unrelated to the learner's words.
- Keep normalized_topic under 100 characters.
"""
        result = _parse(generate(prompt))
        if not isinstance(result, dict):
            return fallback
        accepted = bool(result.get("accepted"))
        clarify = bool(result.get("needs_clarification"))
        normalized = _clean(result.get("normalized_topic"))
        reason = _clean(result.get("reason")) or fallback["reason"]
        if accepted and not normalized:
            return fallback
        if len(normalized) > 100:
            normalized = normalized[:100].rstrip()
        return {
            "accepted": accepted,
            "needs_clarification": clarify,
            "normalized_topic": normalized if accepted else "",
            "reason": reason[:240],
        }
    except Exception:
        return fallback
