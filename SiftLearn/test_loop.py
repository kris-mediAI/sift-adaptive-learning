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


# -----------------------------------------
# Initial student answer
# -----------------------------------------

question = """
What does the % operator do in Python?
"""

answer = """
It divides two numbers and gives the answer.
"""

result = session.process_answer(
    subject="Python",
    question=question,
    answer=answer
)

print("\n==============================")
print("INITIAL ASSESSMENT")
print("==============================")

print(result["assessment"])

print("\n==============================")
print("ADAPTIVE DECISION")
print("==============================")

print(result["recommendation"])


# -----------------------------------------
# Generate intervention
# -----------------------------------------

intervention = session.generate_next_intervention(
    subject="Python",
    recommendation=result["recommendation"]
)

print("\n==============================")
print("INTERVENTION")
print("==============================")

print(intervention)


# -----------------------------------------
# Simulate student's response
# -----------------------------------------

intervention_task = (
    intervention["task"]
    if isinstance(intervention, dict)
    else "What is 17 % 5?"
)

student_answer = """
17 % 5 is 2 because 5 goes into 17 three times
and 2 is left over.
"""


# -----------------------------------------
# Complete intervention
# -----------------------------------------

completed = session.complete_intervention(
    subject="Python",
    question=intervention_task,
    answer=student_answer
)

print("\n==============================")
print("POST-INTERVENTION ASSESSMENT")
print("==============================")

print(completed["assessment"])

print("\n==============================")
print("LEARNING RECORD")
print("==============================")

print(completed["learning_record"])

print("\n==============================")
print("STRATEGY EFFECTIVENESS")
print("==============================")

print(
    completed["strategy_effectiveness"]
)