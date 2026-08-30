from core.learner_model import LearnerProfile
from ai.teaching import generate_intervention


learner = LearnerProfile(
    name="Krishav",
    goal="Get an ML internship",
    subject="Python",
    available_minutes=30,
    current_level="Beginner",
    target_days=60
)


result = generate_intervention(
    subject="Python",
    concept="Call Stack",
    strategy="visual_explanation",
    learner=learner
)


print("\nSIFT INTERVENTION")
print("-----------------")

for key, value in result.items():
    print(f"\n{key}:")
    print(value)