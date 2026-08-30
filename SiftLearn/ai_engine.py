"""Legacy compatibility facade for Sift's canonical assessment engine.

New code should import ``ai.assessment.assess_answer`` directly.
This module remains temporarily so older callers do not break.
"""

from ai.assessment import assess_answer


def evaluate_answer(subject, question, answer):
    """Return the legacy result shape using the canonical assessor."""
    result = assess_answer(subject, question, answer)
    return {
        "score": result["score"],
        "concept": result["concept"],
        "misconception": result["misconception"],
        "explanation": result["explanation"],
        "next_action": result["next_concept"],
        "correct": result["correct"],
        "mistake_type": result["mistake_type"],
        "confidence": result["confidence"],
        "next_concept": result["next_concept"],
    }
