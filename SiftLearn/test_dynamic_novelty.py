from core.content_engine import (
    ContentEngine,
    ContentValidationError,
)
from core.learner_model import LearnerProfile
from core.knowledge_model import Concept


print()
print("=" * 60)
print("SIFT NOVELTY VALIDATION TEST")
print("=" * 60)


# ============================================================
# LEARNER
# ============================================================

learner = LearnerProfile(
    name="Krishav",
    goal="Get an ML internship",
    subject="Python",
    available_minutes=20,
    current_level="Beginner",
    target_days=60,
)


# ============================================================
# CONCEPT
# ============================================================

concept = Concept(
    "modulo operator",
    mastery=69,
)

concept.confidence = 70

concept.mistakes = [
    (
        "The student confuses modulo (%) "
        "with standard division (/)."
    )
]

concept.mistake_types = {
    "conceptual": 1
}


# ============================================================
# RECOMMENDATION
# ============================================================

recommendation = {
    "action": "practice",
    "concept": "modulo operator",
    "mastery": 69,
    "confidence": 70,
    "priority": 25,
    "strategy": "practice_first",
    "target_concept": "modulo operator",
    "diagnosis": "direct_concept_gap",
}


# ============================================================
# PREVIOUS TASK
# ============================================================

previous_tasks = [
    {
        "title": "Predicting Modulo Operation",

        "question": """
What is the exact output of the following
Python code snippet?

result = 17 % 5
print(result)
""",

        "context": "Python arithmetic operators.",
    }
]


# ============================================================
# ENGINE
# ============================================================

engine = ContentEngine(
    model=None,
    strict=True,
    allow_fallback=True,
)


# ============================================================
# SPEC
# ============================================================

spec = engine.build_task_spec(
    learner=learner,
    recommendation=recommendation,
    concept=concept,
    previous_tasks=previous_tasks,
)


print()
print("NOVELTY")
print("-------")

print(
    "novelty:",
    spec.novelty,
)


print()
print("PREVIOUS TASKS")
print("--------------")

print(
    spec.metadata[
        "previous_tasks"
    ]
)


# ============================================================
# BAD TASK
# ============================================================

bad_task = {
    "title": "Predicting Modulo Operation",

    "question": """
What is the exact output of the following
Python code snippet?

result = 17 % 5
print(result)
""",

    "context": "Python arithmetic operators.",

    "hints": [],

    "success_signal": (
        "The learner calculates the remainder."
    ),

    "expected_answer_type": "short answer",

    "difficulty": "medium",

    "question_type": "code_prediction",

    "concept": "modulo operator",

    "strategy": "practice_first",

    "action": "practice",
}


# ============================================================
# VALIDATE BAD TASK
# ============================================================

print()
print("TESTING DUPLICATE TASK")
print("----------------------")

try:

    engine.validate_task(
        bad_task,
        spec,
    )

    engine.validate_novelty(
        bad_task,
        spec,
        previous_tasks,
    )

    print(
        "duplicate rejection: FAIL"
    )

    raise SystemExit(1)

except ContentValidationError as exc:

    print(
        "duplicate rejection: PASS"
    )

    print(
        "reason:",
        exc,
    )


# ============================================================
# GOOD TASK
# ============================================================

good_task = {
    "title": "Modulo for Batch Rotation",

    "question": """
A data-processing script assigns rows to one
of four rotating groups. The row index starts
at 0. Write a Python expression using modulo
to determine which group an index belongs to,
and explain why modulo is useful here.
""",

    "context": (
        "Applying modulo to a different "
        "Python programming situation."
    ),

    "hints": [
        "Think about what remains after "
        "dividing the index by the number of groups."
    ],

    "success_signal": (
        "The learner correctly applies modulo "
        "to produce a repeating group index."
    ),

    "expected_answer_type": "code and explanation",

    "difficulty": "medium",

    "question_type": "code_prediction",

    "concept": "modulo operator",

    "strategy": "practice_first",

    "action": "practice",
}


# ============================================================
# VALIDATE GOOD TASK
# ============================================================

print()
print("TESTING NOVEL TASK")
print("------------------")

try:

    engine.validate_task(
        good_task,
        spec,
    )

    engine.validate_novelty(
        good_task,
        spec,
        previous_tasks,
    )

    print(
        "novelty acceptance: PASS"
    )

except ContentValidationError as exc:

    print(
        "novelty acceptance: FAIL"
    )

    print(
        "reason:",
        exc,
    )

    raise


# ============================================================
# FINAL
# ============================================================

print()
print("=" * 60)
print("RESULT: PASS")
print("=" * 60)

print()
print(
    "Sift now rejects obvious repeated tasks "
    "and accepts genuinely different tasks."
)