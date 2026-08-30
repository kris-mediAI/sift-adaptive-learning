from datetime import datetime, timedelta, timezone

from core.knowledge_model import Concept
from core.knowledge_graph import KnowledgeGraph
from core.subject_graphs import PYTHON_GRAPH
from core.retention import RetentionEngine
from core.adaptive_engine import AdaptiveEngine
from core.learner_model import LearnerProfile


learner = LearnerProfile(
    name="Krishav",
    goal="Get an ML internship",
    subject="Python",
    available_minutes=30,
    current_level="Beginner",
    target_days=60
)


functions = Concept("Functions")

functions.update(85)
functions.update(90)


# Simulate the concept being studied 10 days ago.
functions.last_seen = (
    datetime.now(timezone.utc)
    - timedelta(days=10)
).isoformat()


graph = KnowledgeGraph(
    PYTHON_GRAPH
)

retention = RetentionEngine(
    review_threshold=65
)

engine = AdaptiveEngine(
    knowledge_graph=graph,
    retention_engine=retention
)


recommendation = engine.recommend(
    learner=learner,
    concepts=[functions],
    focus_concept="Functions"
)


print("\nSIFT DUE REVIEW")
print("----------------")

for key, value in recommendation.items():
    print(f"{key}: {value}")