"""Offline integrity checks for the current Sift backend."""
import tempfile
from pathlib import Path
from core.scoring import clamp_score, update_mastery
from core.subject_graphs import get_subject_graph, get_supported_subjects
from ai.assessment import validate_assessment
from database.db import SiftDatabase


def check(name, fn):
    fn(); print(f"PASS  {name}")


def main():
    subjects = get_supported_subjects()
    check("registered subjects are unique and non-empty", lambda: assert_subjects(subjects))
    check("all subject graphs are non-empty", lambda: assert_graphs(subjects))
    check("scoring invariants", lambda: assert_scoring())
    check("assessment consistency", lambda: assert_assessment())
    check("SQLite WAL configuration", lambda: assert_db())
    print("\nSIFT BACKEND OFFLINE CHECKS: PASS")
    print("No Gemini or YouTube calls were made.")


def assert_subjects(subjects):
    assert subjects and len(subjects) == len(set(subjects))
    assert "Python" in subjects
    assert "Data Structures & Algorithms" in subjects
    assert all(get_subject_graph(s) for s in subjects)


def assert_graphs(subjects):
    assert all(get_subject_graph(s) for s in subjects)


def assert_scoring():
    assert clamp_score(120) == 100.0
    assert clamp_score(-10) == 0.0
    assert 0 <= update_mastery(50, 80) <= 100


def assert_assessment():
    result = validate_assessment({
        "score": 80, "correct": True, "concept": "Variables",
        "mistake_type": "conceptual", "misconception": "should be cleared",
        "confidence": 90, "explanation": "Good explanation.", "next_concept": "Functions",
    })
    assert result["mistake_type"] == "none" and result["misconception"] == ""


def assert_db():
    with tempfile.TemporaryDirectory() as directory:
        db = SiftDatabase(str(Path(directory) / "sift.db"))
        connection = db._connect()
        try:
            assert str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower() == "wal"
        finally:
            connection.close()


if __name__ == "__main__":
    main()
