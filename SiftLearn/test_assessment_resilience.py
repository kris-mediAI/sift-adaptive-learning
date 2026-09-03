import json

import pytest

from ai import assessment


def test_malformed_assessment_gets_one_repair_attempt(monkeypatch):
    calls = []
    valid = {
        "score": 20, "correct": False, "concept": "list indexing",
        "mistake_type": "conceptual",
        "misconception": "The index does not start at one.",
        "confidence": 90,
        "explanation": "Python indexing starts at zero.",
        "next_concept": "list indexing",
        "strengths": [], "gaps": ["zero-based indexing"],
        "recommended_help": "explanation",
    }

    def fake_generate(prompt):
        calls.append(prompt)
        return "not json" if len(calls) == 1 else json.dumps(valid)

    monkeypatch.setattr("ai.gemini.generate", fake_generate)
    result = assessment.assess_answer("Python", "What is scores[2]?", "I don't know")

    assert result["concept"] == "list indexing"
    assert len(calls) == 2
    assert "Previous model output" in calls[1]


def test_invalid_repair_still_respects_validation(monkeypatch):
    monkeypatch.setattr("ai.gemini.generate", lambda prompt: "not json")
    with pytest.raises(ValueError, match="invalid assessment JSON"):
        assessment.assess_answer("Python", "What is scores[2]?", "I don't know")


def test_uncertainty_answer_has_safe_local_fallback_when_concept_is_known(monkeypatch):
    monkeypatch.setattr("ai.gemini.generate", lambda prompt: "not json")
    result = assessment.assess_answer(
        "Python", "What is scores[2]?", "idk", fallback_concept="Lists"
    )
    assert result["score"] == 0
    assert result["correct"] is False
    assert result["concept"] == "Lists"
    assert result["recommended_help"] == "explanation"

