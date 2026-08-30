from core.learner_model import LearnerProfile
from core.knowledge_model import Concept
from core.knowledge_graph import KnowledgeGraph
from core.subject_graphs import PYTHON_GRAPH
from core.adaptive_engine import AdaptiveEngine


learner = LearnerProfile(
    name="Krishav",
    goal="Get an ML internship",
    subject="Python",
    available_minutes=30,
    current_level="Beginner",
    target_days=60
)


# Strong prerequisite.
functions = Concept("Functions")
functions.update(85)


# Weak prerequisite.
call_stack = Concept("Call Stack")

call_stack.update(
    30,
    "Does not understand how previous calls remain active",
    "conceptual"
)


# Weak target concept.
recursion = Concept("Recursion")

recursion.update(
    40,
    "Cannot identify the base case",
    "conceptual"
)


concepts = [
    functions,
    call_stack,
    recursion
]


graph = KnowledgeGraph(
    PYTHON_GRAPH
)


engine = AdaptiveEngine(
    graph
)


recommendation = engine.recommend(
    learner,
    concepts,
    focus_concept="Recursion"
)


print("\nSIFT ADAPTIVE DECISION")
print("----------------------")

for key, value in recommendation.items():
    print(f"{key}: {value}")