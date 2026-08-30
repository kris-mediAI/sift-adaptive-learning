from datetime import datetime, timedelta, timezone

from core.knowledge_model import Concept
from core.retention import RetentionEngine


concept = Concept("Functions")

# Learner demonstrates good knowledge.
concept.update(85)
concept.update(90)

print("\nCURRENT CONCEPT STATE")
print("---------------------")
print(concept.to_dict())


# Simulate that the learner last studied this
# concept 10 days ago.
concept.last_seen = (
    datetime.now(timezone.utc)
    - timedelta(days=10)
).isoformat()


retention = RetentionEngine(
    review_threshold=65
)

analysis = retention.explain(
    concept
)


print("\nSIFT RETENTION ANALYSIS")
print("-----------------------")

for key, value in analysis.items():
    print(f"{key}: {value}")