from core.learner_model import (
    LearnerProfile,
    LearningRecord,
)

from core.learning_record import (
    LearningRecord as CompatibilityLearningRecord
)

from core.knowledge_model import Concept


print()
print("=" * 60)
print("SIFT CLEANUP / CONSISTENCY TEST")
print("=" * 60)


# ============================================================
# 1. LEARNING RECORD SINGLE SOURCE OF TRUTH
# ============================================================

print()
print("LEARNING RECORD TYPE")
print("--------------------")

same_class = (
    LearningRecord
    is CompatibilityLearningRecord
)

print(
    "core.learning_record and "
    "core.learner_model:",
    "PASS" if same_class else "FAIL"
)


# ============================================================
# 2. LEGACY INTERVENTION TYPE NORMALIZATION
# ============================================================

print()
print("INTERVENTION TYPE NORMALIZATION")
print("--------------------------------")

legacy_record = LearningRecord(
    concept="Call Stack",
    strategy="visual_explanation",
    pre_mastery=30,
    post_mastery=68,
    learning_gain=38,
    intervention_type="teach",
    completed=True
)

print(
    "teach -> teaching:",
    (
        "PASS"
        if legacy_record.intervention_type
        == "teaching"
        else "FAIL"
    )
)

review_record = LearningRecord(
    concept="Functions",
    strategy="retrieval_practice",
    pre_mastery=88,
    post_mastery=91,
    learning_gain=3,
    intervention_type="retrieval_practice",
    completed=True
)

print(
    "retrieval_practice -> review:",
    (
        "PASS"
        if review_record.intervention_type
        == "review"
        else "FAIL"
    )
)


# ============================================================
# 3. LEARNING RECORD ROUND TRIP
# ============================================================

print()
print("LEARNING RECORD ROUND TRIP")
print("--------------------------")

serialized = (
    legacy_record.to_dict()
)

restored = (
    LearningRecord.from_dict(
        serialized
    )
)

checks = {
    "concept": (
        restored.concept
        == legacy_record.concept
    ),

    "strategy": (
        restored.strategy
        == legacy_record.strategy
    ),

    "pre_mastery": (
        restored.pre_mastery
        == legacy_record.pre_mastery
    ),

    "post_mastery": (
        restored.post_mastery
        == legacy_record.post_mastery
    ),

    "learning_gain": (
        restored.learning_gain
        == legacy_record.learning_gain
    ),

    "intervention_type": (
        restored.intervention_type
        == "teaching"
    ),

    "completed": (
        restored.completed
        == legacy_record.completed
    )
}

for name, passed in checks.items():

    print(
        f"{name}: "
        f"{'PASS' if passed else 'FAIL'}"
    )


# ============================================================
# 4. CORRECT ANSWER MUST NOT CREATE MISTAKE
# ============================================================

print()
print("CORRECT ANSWER MISTAKE TEST")
print("---------------------------")

concept = Concept(
    "modulo operator"
)

concept.update(
    score=30,
    mistake=(
        "Confuses modulo with division."
    ),
    mistake_type="conceptual"
)

before_mistakes = len(
    concept.mistakes
)

concept.update(
    score=100,
    mistake=None,
    mistake_type="none"
)

after_mistakes = len(
    concept.mistakes
)

print(
    "correct answer adds no mistake:",
    (
        "PASS"
        if before_mistakes
        == after_mistakes
        else "FAIL"
    )
)

print(
    "mistake count:",
    after_mistakes
)


# ============================================================
# 5. CORRECT ANSWER INCREASES EVIDENCE
# ============================================================

print()
print("CORRECT ANSWER EVIDENCE TEST")
print("----------------------------")

print(
    "correct_attempts increased:",
    (
        "PASS"
        if concept.correct_attempts == 1
        else "FAIL"
    )
)

print(
    "attempts increased:",
    (
        "PASS"
        if concept.attempts == 2
        else "FAIL"
    )
)


# ============================================================
# 6. MASTERy != LAST SCORE
# ============================================================

print()
print("MASTERY SEMANTICS")
print("------------------")

print(
    "latest score:",
    concept.last_score
)

print(
    "mastery:",
    concept.mastery
)

print(
    "mastery != latest score:",
    (
        "PASS"
        if concept.mastery
        != concept.last_score
        else "FAIL"
    )
)


# ============================================================
# 7. CONFIDENCE SEMANTICS
# ============================================================

print()
print("CONFIDENCE SEMANTICS")
print("--------------------")

print(
    "confidence:",
    concept.confidence
)

print(
    "confidence is estimate certainty:",
    (
        "PASS"
        if 0 <= concept.confidence <= 100
        else "FAIL"
    )
)


# ============================================================
# 8. STRATEGY EVIDENCE
# ============================================================

print()
print("STRATEGY EVIDENCE")
print("-----------------")

learner = LearnerProfile(
    name="Krishav",
    goal="Get an ML internship",
    subject="Python",
    available_minutes=20,
    current_level="Beginner",
    target_days=60
)

learner.record_learning(
    LearningRecord(
        concept="Call Stack",
        strategy="visual_explanation",
        pre_mastery=30,
        post_mastery=68,
        learning_gain=38,
        intervention_type="teaching",
        completed=True
    )
)

strategy_data = (
    learner.preferred_strategies[
        "visual_explanation"
    ]
)

print(
    "attempts:",
    strategy_data["attempts"]
)

print(
    "total improvement:",
    strategy_data[
        "total_improvement"
    ]
)

print(
    "average gain:",
    strategy_data[
        "average_gain"
    ]
)

print(
    "average gain correct:",
    (
        "PASS"
        if strategy_data[
            "average_gain"
        ] == 38
        else "FAIL"
    )
)


# ============================================================
# 9. LEARNER SERIALIZATION
# ============================================================

print()
print("LEARNER SERIALIZATION")
print("---------------------")

data = learner.to_dict()

restored_learner = (
    LearnerProfile.from_dict(
        data
    )
)

print(
    "learning record restored:",
    (
        "PASS"
        if len(
            restored_learner.learning_records
        ) == 1
        else "FAIL"
    )
)

print(
    "record is LearningRecord:",
    (
        "PASS"
        if isinstance(
            restored_learner.learning_records[0],
            LearningRecord
        )
        else "FAIL"
    )
)


# ============================================================
# 10. FINAL RESULT
# ============================================================

all_passed = True

all_checks = [
    same_class,

    legacy_record.intervention_type
    == "teaching",

    review_record.intervention_type
    == "review",

    all(checks.values()),

    before_mistakes
    == after_mistakes,

    concept.correct_attempts == 1,

    concept.attempts == 2,

    concept.mastery
    != concept.last_score,

    0 <= concept.confidence <= 100,

    strategy_data["average_gain"]
    == 38,

    len(
        restored_learner.learning_records
    ) == 1,

    isinstance(
        restored_learner.learning_records[0],
        LearningRecord
    )
]

all_passed = all(
    all_checks
)

print()
print("=" * 60)

if all_passed:
    print(
        "RESULT: PASS"
    )

    print()
    print(
        "Sift cleanup is consistent."
    )

    print(
        "The system is ready for the "
        "Learner Intelligence Layer."
    )

else:
    print(
        "RESULT: FAIL"
    )

    print()
    print(
        "Do not continue to the next layer yet."
    )

print("=" * 60)