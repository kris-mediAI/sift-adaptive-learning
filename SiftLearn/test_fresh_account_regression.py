"""Fresh-account regressions for the judge-critical first learning turn."""
import json

from core.content_engine import ContentEngine
from core.learner_model import LearnerProfile
from core.knowledge_model import Concept
from core.orchestrator import SiftOrchestrator
from core.repository import SiftRepository
from database.db import SiftDatabase


def _recommendation(concept):
    return {
        "action": "teach",
        "concept": concept,
        "mastery": 0,
        "confidence": 0,
        "priority": 100,
        "strategy": "worked_example",
        "target_concept": concept,
        "diagnosis": "direct_concept_gap",
    }


def test_fresh_account_dynamic_task_cannot_drift_to_unrelated_concept(tmp_path, monkeypatch):
    class Model:
        def __init__(self):
            self.calls = 0

        def generate(self, prompt):
            self.calls += 1
            low = prompt.lower()
            if "assessment engine" in low or "student answer" in low:
                return json.dumps({
                    "score": 0,
                    "correct": False,
                    "concept": "array indexing",  # deliberately wrong label
                    "mistake_type": "conceptual",
                    "misconception": "The response does not demonstrate recursion.",
                    "confidence": 95,
                    "explanation": "The answer does not provide enough evidence yet.",
                    "next_concept": "Recursion",
                    "strengths": [],
                    "gaps": ["recursion"],
                    "recommended_help": "explanation",
                })
            if self.calls == 1:
                # Deliberately semantically unrelated while structurally valid.
                return json.dumps({
                    "title": "Tracing Array Indexing",
                    "question": "Given fruits = ['apple', 'banana', 'cherry'], what is fruits[2]?",
                    "context": "Trace a list lookup.",
                    "hints": ["Indexing starts at zero."],
                    "success_signal": "Identifies the indexed value.",
                    "expected_answer_type": "short answer",
                    "difficulty": "easy",
                    "question_type": "short_answer",
                    "learning_guide": {
                        "explanation": "Array indexing selects an item by position.",
                        "worked_example": "A list lookup uses a zero-based position.",
                        "hint": "Start from index zero.",
                    },
                })
            return json.dumps({
                "title": "Recursion with a smaller problem",
                "question": "Explain how recursion solves a problem by reducing it to a smaller recursive case and stopping at a base case.",
                "context": "Focus on the recursive call and base case.",
                "hints": ["Name the base case."],
                "success_signal": "Explains recursive reduction and the stopping condition.",
                "expected_answer_type": "explanation",
                "difficulty": "easy",
                "question_type": "short_answer",
                "learning_guide": {
                    "explanation": "Recursion repeatedly solves a smaller version until a base case stops it.",
                    "worked_example": "Factorial reduces 4! to 4 × 3!, then continues toward 1!.",
                    "hint": "Identify the smaller call and the stopping case.",
                },
            })

    repo = SiftRepository(database=SiftDatabase(str(tmp_path / "fresh.db")))
    model = Model()
    monkeypatch.setattr("ai.gemini.generate", model.generate)
    engine = ContentEngine(model=model, strict=True, allow_fallback=True)
    sift = SiftOrchestrator(repository=repo, content_engine=engine)
    learner_id, _ = sift.get_or_create_learner("Fresh", "", "Python")
    sift.create_custom_topic(learner_id, "Recursion")
    result = sift.generate_dynamic_task(learner_id, _recommendation("Recursion"))
    assert result["task"]["concept"] == "Recursion"
    assert "recursion" in (result["task"]["question"] + result["task"]["context"]).lower()
    assert model.calls >= 2

    # A model that labels the answer with an unregistered/natural-language
    # concept must still attach the evidence to the active task target.
    completed = sift.complete_dynamic_task(learner_id, result["task"]["question"], "I am not sure")
    assert completed["assessment"]["concept"] == "Recursion"


def test_fresh_account_can_start_with_zero_prior_concepts(tmp_path):
    repo = SiftRepository(database=SiftDatabase(str(tmp_path / "fresh2.db")))
    sift = SiftOrchestrator(repository=repo, content_engine=ContentEngine(model=None, allow_fallback=True))
    learner_id, _ = sift.get_or_create_learner("Brand New", "Learn recursion", "Python")
    session = sift.create_session(learner_id)
    assert session.active_intervention is None
    sift.create_custom_topic(learner_id, "Recursion")
    rec = session.engine.recommend(session.learner, list(session.concepts.values()), focus_concept="Recursion")
    assert rec["concept"] == "Recursion"


def test_fresh_account_first_evaluation_recovers_after_transient_ai_failure(tmp_path, monkeypatch):
    import json
    calls = {"n": 0}
    def fake_generate(prompt):
        calls["n"] += 1
        low = str(prompt).lower()
        if "assessment engine" in low or "student answer" in low:
            # First assessment request fails; the repair request succeeds.
            if calls["n"] == 1:
                raise RuntimeError("503 service unavailable")
            return json.dumps({
                "score": 0, "correct": False, "concept": "array indexing",
                "mistake_type": "conceptual",
                "misconception": "The response does not demonstrate recursion.",
                "confidence": 95,
                "explanation": "That answer does not give enough evidence yet.",
                "next_concept": "Recursion", "strengths": [],
                "gaps": ["recursion"], "recommended_help": "explanation",
            })
        return json.dumps({
            "title": "Recursion task",
            "question": "Explain how recursion reduces a problem to a smaller recursive case and stops at a base case.",
            "context": "Focus on the recursive call and base case.",
            "hints": ["Name the stopping condition."],
            "success_signal": "Explains recursion and its base case.",
            "expected_answer_type": "explanation", "difficulty": "easy",
            "question_type": "short_answer",
            "learning_guide": {
                "explanation": "Recursion solves smaller versions until a base case stops the calls.",
                "worked_example": "Factorial reduces 4! to 3! and continues toward the base case.",
                "hint": "Find the smaller call and the stopping condition.",
            },
        })

    monkeypatch.setattr("ai.gemini.generate", fake_generate)
    repo = SiftRepository(database=SiftDatabase(str(tmp_path / "fresh3.db")))
    model = type("M", (), {"generate": staticmethod(fake_generate)})()
    sift = SiftOrchestrator(repository=repo, content_engine=ContentEngine(model=model, strict=True, allow_fallback=True))
    learner_id, _ = sift.get_or_create_learner("First Turn", "Learn recursion", "Python")
    sift.create_custom_topic(learner_id, "Recursion")
    task = sift.generate_dynamic_task(learner_id, _recommendation("Recursion"))["task"]
    result = sift.complete_dynamic_task(learner_id, task["question"], "idk")
    assert result["assessment"]["concept"] == "Recursion"
    assert result["assessment"]["score"] == 0
    assert result["learning_record"]["completed"] is True
    assert calls["n"] >= 2
