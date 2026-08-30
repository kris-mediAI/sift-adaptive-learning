from core.repository import SiftRepository
from core.learner_model import LearningRecord


print()
print("=" * 60)
print("SIFT FULL STATE PERSISTENCE TEST")
print("=" * 60)


repository = SiftRepository()


# ============================================================
# LOAD / CREATE LEARNER
# ============================================================

learner_id, learner = (
    repository.get_or_create_learner(
        name="Krishav",
        goal="Get an ML internship",
        subject="Python",
        available_minutes=20,
        current_level="Beginner",
        target_days=60
    )
)


print()
print("LEARNER")
print("-------")

print(
    learner.to_dict()
)


print()
print("LEARNER ID")
print("----------")

print(
    learner_id
)


# ============================================================
# CREATE REAL LEARNING RECORD
# ============================================================

record = LearningRecord(
    concept="Call Stack",
    strategy="visual_explanation",
    pre_mastery=30,
    post_mastery=68,
    learning_gain=38,
    intervention_type="teaching",
    completed=True
)


# ============================================================
# ADD THROUGH DOMAIN MODEL
# ============================================================

learner.record_learning(
    record
)


# ============================================================
# PERSONALIZATION
# ============================================================

learner.mistake_patterns = {
    "conceptual": 4,
    "procedural": 1
}


learner.concept_history = {
    "Call Stack": {
        "times_seen": 3,
        "best_score": 88,
        "current_mastery": 68
    }
}


learner.time_accuracy = {
    "estimated_minutes": 19,
    "actual_minutes": 17
}


# ============================================================
# SAVE
# ============================================================

repository.save_learner(
    learner_id,
    learner
)


print()
print("STATE SAVED")
print("-----------")

print(
    learner.to_dict()
)


# ============================================================
# SIMULATE APPLICATION RESTART
# ============================================================

print()
print("SIMULATING RESTART")
print("------------------")


new_repository = SiftRepository()


loaded = (
    new_repository.load_learner(
        learner_id
    )
)


# ============================================================
# SHOW RELOADED STATE
# ============================================================

print()
print("RELOADED LEARNER")
print("----------------")

print(
    loaded.to_dict()
)


# ============================================================
# LEARNING RECORD TYPE CHECK
# ============================================================

print()
print("LEARNING RECORD CHECK")
print("---------------------")


records_valid = (
    len(
        loaded.learning_records
    ) > 0
    and all(
        isinstance(
            record,
            LearningRecord
        )
        for record
        in loaded.learning_records
    )
)


print(
    "records reconstructed as LearningRecord:",
    "PASS" if records_valid else "FAIL"
)


# ============================================================
# PERSONALIZATION CHECK
# ============================================================

print()
print("PERSONALIZATION CHECK")
print("---------------------")


checks = {

    "mistake_patterns": (
        loaded.mistake_patterns
        == learner.mistake_patterns
    ),

    "concept_history": (
        loaded.concept_history
        == learner.concept_history
    ),

    "time_accuracy": (
        loaded.time_accuracy
        == learner.time_accuracy
    ),

    "learning_records": (
        len(
            loaded.learning_records
        )
        == len(
            learner.learning_records
        )
    )
}


all_passed = records_valid


for name, passed in checks.items():

    print(
        f"{name}: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    if not passed:
        all_passed = False


# ============================================================
# LEARNING RECORD CONTENT CHECK
# ============================================================

print()
print("LEARNING RECORD CONTENT")
print("----------------------")


if loaded.learning_records:

    loaded_record = (
        loaded.learning_records[-1]
    )

    expected_record = (
        learner.learning_records[-1]
    )

    record_checks = {

        "concept": (
            loaded_record.concept
            == expected_record.concept
        ),

        "strategy": (
            loaded_record.strategy
            == expected_record.strategy
        ),

        "pre_mastery": (
            loaded_record.pre_mastery
            == expected_record.pre_mastery
        ),

        "post_mastery": (
            loaded_record.post_mastery
            == expected_record.post_mastery
        ),

        "learning_gain": (
            loaded_record.learning_gain
            == expected_record.learning_gain
        ),

        "completed": (
            loaded_record.completed
            == expected_record.completed
        )
    }

    for name, passed in record_checks.items():

        print(
            f"{name}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

        if not passed:
            all_passed = False


# ============================================================
# GET-OR-CREATE CHECK
# ============================================================

print()
print("GET-OR-CREATE CHECK")
print("-------------------")


second_id, second_learner = (
    new_repository.get_or_create_learner(
        name="Krishav",
        goal="Get an ML internship",
        subject="Python",
        available_minutes=20,
        current_level="Beginner",
        target_days=60
    )
)


same_learner = (
    second_id == learner_id
)


print(
    "same learner ID:",
    "PASS" if same_learner else "FAIL"
)


if not same_learner:
    all_passed = False


# ============================================================
# FINAL RESULT
# ============================================================

print()
print("=" * 60)

if all_passed:

    print(
        "RESULT: PASS"
    )

    print()
    print(
        "Sift successfully persisted and reconstructed "
        "the complete learner state."
    )

else:

    print(
        "RESULT: FAIL"
    )

    print()
    print(
        "One or more persistence checks failed."
    )

print("=" * 60)