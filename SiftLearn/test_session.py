from core.learner_model import LearnerProfile
from core.knowledge_graph import KnowledgeGraph
from core.subject_graphs import PYTHON_GRAPH
from core.session import SiftSession


learner = LearnerProfile(
    name="Krishav",
    goal="Get an ML internship",
    subject="Python",
    available_minutes=30,
    current_level="Beginner",
    target_days=60
)


graph = KnowledgeGraph(
    PYTHON_GRAPH
)


session = SiftSession(
    learner=learner,
    knowledge_graph=graph
)


question = """
What does the % operator do in Python?
"""


answer = """
It divides two numbers and gives the result.
"""


result = session.process_answer(
    subject="Python",
    question=question,
    answer=answer
)


print("\n==============================")
print("SIFT ASSESSMENT")
print("==============================")

for key, value in result["assessment"].items():
    print(f"{key}: {value}")


print("\n==============================")
print("KNOWLEDGE STATE")
print("==============================")

for key, value in result["concept"].items():
    print(f"{key}: {value}")


print("\n==============================")
print("ADAPTIVE DECISION")
print("==============================")

for key, value in result["recommendation"].items():
    print(f"{key}: {value}")


print("\n==============================")
print("GENERATING INTERVENTION")
print("==============================")


intervention = session.generate_next_intervention(
    subject="Python",
    recommendation=result["recommendation"]
)


if intervention:
    print(intervention)
else:
    print("No intervention required.")

def test_create_learning_session_rejects_obvious_non_topic():
    from tempfile import mktemp
    import os
    from core.orchestrator import SiftOrchestrator
    from core.repository import SiftRepository
    from database.db import SiftDatabase

    path = mktemp(suffix=".db")
    try:
        sift = SiftOrchestrator(repository=SiftRepository(database=SiftDatabase(path)))
        learner_id, _ = sift.get_or_create_learner(
            name="Test Learner", goal="", subject="Python", available_minutes=30,
            current_level="Beginner", target_days=30,
        )
        try:
            sift.create_learning_session(learner_id, "Python", "idk")
            assert False, "obvious non-topic should be rejected"
        except ValueError as exc:
            assert "vague" in str(exc).lower()
    finally:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
