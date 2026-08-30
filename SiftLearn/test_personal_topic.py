"""Focused regression checks for learner-created topics."""
from tempfile import mktemp
import os

from core.orchestrator import SiftOrchestrator
from core.repository import SiftRepository
from database.db import SiftDatabase


def test_personal_topic_survives_reload():
    path = mktemp(suffix=".db")
    try:
        repo = SiftRepository(database=SiftDatabase(path))
        sift = SiftOrchestrator(repository=repo)
        learner_id, _ = sift.get_or_create_learner(
            name="Test Learner",
            goal="",
            subject="Python",
            available_minutes=30,
            current_level="Beginner",
            target_days=30,
        )
        result = sift.create_custom_topic(learner_id, "Python decorators")
        assert result["is_new"] is True
        session = sift.get_session(learner_id)
        assert session.focus_concept == "Python decorators"
        assert "Python decorators" in session.engine.knowledge_graph.graph

        # Force a new session object and ensure the user topic is restored.
        sift.sessions.pop(learner_id, None)
        restored = sift.get_session(learner_id)
        assert "Python decorators" in restored.engine.knowledge_graph.graph
        assert restored.focus_concept == "Python decorators"
    finally:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


def test_learning_input_rejects_vague_and_accepts_custom():
    from ai.topic_validator import validate_learning_input

    vague = validate_learning_input("Python", "idk", ["Variables", "Functions"])
    assert vague["accepted"] is False
    assert vague["needs_clarification"] is True

    custom = validate_learning_input("Python", "I don't understand recursion", ["Variables", "Functions"])
    assert custom["accepted"] is True
    assert custom["normalized_topic"]
