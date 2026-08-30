from test_support import isolated_database
from core.knowledge_model import Concept


print("\nSIFT PERSISTENCE TEST")
print("====================")


db = isolated_database()


# ============================================================
# LEARNER
# ============================================================

learner_id = db.get_or_create_learner(
    name="Krishav",
    goal="Get an ML internship",
    subject="Python",
    available_minutes=20,
    current_level="Beginner",
    target_days=60
)

print(
    "\nLEARNER ID"
)

print(
    learner_id
)


# ============================================================
# CONCEPT
# ============================================================

concept = Concept(
    "Call Stack"
)


concept.update(
    68,
    "Does not understand active function calls",
    "conceptual"
)


print(
    "\nCURRENT CONCEPT"
)

print(
    concept.to_dict()
)


# ============================================================
# SAVE CONCEPT
# ============================================================

db.save_concept(
    learner_id,
    concept
)


# ============================================================
# ASSESSMENT
# ============================================================

assessment = {
    "concept": "Call Stack",
    "score": 68,
    "correct": True,
    "mistake_type": "none",
    "misconception": "",
    "confidence": 88,
    "explanation": (
        "The learner understands the active "
        "function call stack."
    ),
    "next_concept": "Recursion"
}


db.save_assessment(
    learner_id,
    assessment
)


# ============================================================
# LEARNING EVENT
# ============================================================

learning_event = {
    "concept": "Call Stack",
    "strategy": "visual_explanation",
    "intervention_type": "teaching",
    "pre_mastery": 30,
    "post_mastery": 68,
    "learning_gain": 38,
    "completed": True
}


db.save_learning_event(
    learner_id,
    learning_event
)


# ============================================================
# READ CURRENT CONCEPT
# ============================================================

saved_concept = db.get_concept(
    learner_id,
    "Call Stack"
)


print(
    "\nSAVED CONCEPT"
)

print(
    saved_concept
)


# ============================================================
# ALL CONCEPTS
# ============================================================

print(
    "\nALL CONCEPTS"
)

print(
    db.get_all_concepts(
        learner_id
    )
)


# ============================================================
# STRATEGY EFFECTIVENESS
# ============================================================

print(
    "\nSTRATEGY EFFECTIVENESS"
)

print(
    db.get_strategy_effectiveness(
        learner_id
    )
)


# ============================================================
# SUMMARY
# ============================================================

print(
    "\nLEARNER SUMMARY"
)

print(
    db.get_learner_summary(
        learner_id
    )
)