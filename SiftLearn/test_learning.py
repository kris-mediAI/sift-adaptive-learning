from core.learner_model import LearnerProfile
from core.learning_record import LearningRecord


learner = LearnerProfile(
    name="Krishav",
    goal="Get an ML internship",
    subject="Python",
    available_minutes=30,
    current_level="Beginner",
    target_days=60
)


# Sift teaches Call Stack using a visual explanation.
record = LearningRecord(
    concept="Call Stack",
    strategy="visual_explanation",
    pre_mastery=30,
    post_mastery=68
)


learner.record_learning(record)


print("\nSIFT LEARNING RECORD")
print("--------------------")

print("Concept:", record.concept)
print("Strategy:", record.strategy)
print("Before:", record.pre_mastery)
print("After:", record.post_mastery)
print("Learning gain:", record.learning_gain)

print("\nSTRATEGY EVIDENCE")
print("-----------------")

print(
    learner.preferred_strategies
)

print(
    "\nVisual effectiveness:",
    learner.get_strategy_effectiveness(
        "visual_explanation"
    )
)