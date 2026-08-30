from core.content_engine import ContentEngine
from core.learner_model import LearnerProfile
from core.knowledge_model import Concept
from core.orchestrator import SiftOrchestrator
from core.repository import SiftRepository
from database.db import SiftDatabase


def _learner():
    return LearnerProfile("Test", "", "Python", 30, "Beginner", 30)


def _recommendation(concept="stack"):
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


def test_model_failure_uses_valid_teaching_fallback():
    class BrokenModel:
        def generate(self, prompt):
            raise RuntimeError("provider unavailable")

    engine = ContentEngine(model=BrokenModel(), strict=True, allow_fallback=True)
    concept = Concept("stack")
    result = engine.generate(_learner(), _recommendation(), concept, previous_tasks=[])
    task = result["task"]
    assert result["generated_by"] == "fallback"
    assert task["generation_fallback"] is True
    assert "LIFO" in task["learning_guide"]["explanation"]
    assert task["hints"]


def test_fallback_remains_novel_across_history():
    class BrokenModel:
        def generate(self, prompt):
            raise RuntimeError("provider unavailable")

    engine = ContentEngine(model=BrokenModel(), strict=True, allow_fallback=True)
    learner = _learner()
    concept = Concept("modulo operator")
    rec = _recommendation("modulo operator")
    first = engine.generate(learner, rec, concept, previous_tasks=[])["task"]
    history = [{"task": first}]
    second = engine.generate(learner, rec, concept, previous_tasks=history)["task"]
    assert first["question"] != second["question"]


def test_study_plan_preferences_persist_without_changing_evidence(tmp_path):
    repo = SiftRepository(database=SiftDatabase(str(tmp_path / "sift.db")))
    sift = SiftOrchestrator(repository=repo, content_engine=ContentEngine(model=None, allow_fallback=True))
    learner_id, _ = sift.get_or_create_learner("Test", "", "Python", 30, "Beginner", 30)
    session = sift.create_session(learner_id)
    session.get_or_create_concept("Variables").update(80)
    before = session.get_or_create_concept("Variables").to_dict()
    saved = sift.update_study_plan(learner_id, available_minutes=45, target_days=90)
    restored = sift.get_session(learner_id)
    after = restored.get_or_create_concept("Variables").to_dict()
    assert saved == {"available_minutes": 45, "target_days": 90}
    assert restored.learner.available_minutes == 45
    assert restored.learner.target_days == 90
    assert after["mastery"] == before["mastery"]
    assert after["attempts"] == before["attempts"]


def test_dynamic_task_survives_reload_and_completes(tmp_path, monkeypatch):
    repo = SiftRepository(database=SiftDatabase(str(tmp_path / "sift.db")))
    class DeterministicModel:
        def generate(self, prompt):
            import json
            if "assessment engine" in prompt.lower() or "student answer" in prompt.lower():
                return json.dumps({
                    "score": 90, "correct": True, "concept": "Variables",
                    "mistake_type": "none", "misconception": "",
                    "confidence": 90, "explanation": "Correct core idea.",
                    "next_concept": "", "strengths": ["Tracks the value"],
                    "gaps": [], "recommended_help": "advance",
                })
            return json.dumps({
                "title": "Variables task", "question": "If x=2 and x=5, what is x now?",
                "context": "Track assignment order.", "hints": ["Read the latest assignment."],
                "success_signal": "Identifies the latest value.", "expected_answer_type": "explanation",
                "difficulty": "easy", "question_type": "short_answer",
                "learning_guide": {
                    "explanation": "A later assignment changes the current value.",
                    "worked_example": "x=1 then x=4 means x is 4.",
                    "hint": "Use the latest assignment.",
                }
            })

    sift = SiftOrchestrator(repository=repo, content_engine=ContentEngine(model=DeterministicModel(), strict=True, allow_fallback=True))
    learner_id, _ = sift.get_or_create_learner("Test", "", "Python", 30, "Beginner", 30)
    session = sift.create_session(learner_id)
    concept = session.get_or_create_concept("Variables")
    result = sift.generate_dynamic_task(learner_id, _recommendation("Variables"))
    assert result["task"]["question"]
    sift.sessions.pop(learner_id)
    restored = sift.get_session(learner_id)
    assert restored.active_intervention is not None
    assert restored.active_intervention["intervention_id"] is not None
    completed = sift.complete_dynamic_task(learner_id, result["task"]["question"], "5")
    assert completed["learning_record"]["completed"] is True
