import os
import pytest

from core.content_engine import (
    ContentEngine,
    ContentValidationError,
)
from core.learner_model import LearnerProfile
from core.knowledge_model import Concept
from core.llm.gemini_provider import GeminiProvider


print()
print("=" * 60)
print("SIFT LIVE GEMINI CONTENT TEST")
print("=" * 60)


# ============================================================
# API KEY CHECK
# ============================================================

if not (
    os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
):
    print()
    print("RESULT: SKIPPED")
    print()
    print(
        "Set GEMINI_API_KEY or GOOGLE_API_KEY "
        "before running the live test."
    )
    pytest.skip("Live Gemini credentials are not configured in this environment.", allow_module_level=True)


# ============================================================
# LEARNER
# ============================================================

learner = LearnerProfile(
    name="Krishav",
    goal="Get an ML internship",
    subject="Python",
    available_minutes=20,
    current_level="Beginner",
    target_days=60
)


# ============================================================
# CONCEPT
# ============================================================

concept = Concept(
    "modulo operator",
    mastery=69
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
# ADAPTIVE DECISION
# ============================================================

recommendation = {
    "action": "practice",
    "concept": "modulo operator",
    "mastery": 69,
    "confidence": 70,
    "priority": 25,
    "strategy": "practice_first",
    "target_concept": "modulo operator",
    "diagnosis": "direct_concept_gap"
}


# ============================================================
# PROVIDER
# ============================================================

print()
print("INITIALIZING GEMINI")
print("-------------------")

provider = GeminiProvider()

print(
    "model:",
    provider.model_name
)


# ============================================================
# CONTENT ENGINE
# ============================================================

engine = ContentEngine(
    model=provider,
    strict=True,
    allow_fallback=False
)


# ============================================================
# GENERATE
# ============================================================

print()
print("GENERATING DYNAMIC TASK")
print("-----------------------")

result = engine.generate(
    learner=learner,
    recommendation=recommendation,
    concept=concept
)


spec = result["spec"]
task = result["task"]


# ============================================================
# SPEC
# ============================================================

print()
print("TASK SPEC")
print("---------")

print(
    "concept:",
    spec["concept"]
)

print(
    "action:",
    spec["action"]
)

print(
    "strategy:",
    spec["strategy"]
)

print(
    "difficulty:",
    spec["difficulty"]
)

print(
    "question_type:",
    spec["question_type"]
)

print(
    "misconception:",
    spec["misconception"]
)

print(
    "novelty:",
    spec["novelty"]
)


# ============================================================
# TASK
# ============================================================

print()
print("GENERATED TASK")
print("--------------")

print(
    "title:",
    task["title"]
)

print(
    "question:",
    task["question"]
)

print(
    "context:",
    task["context"]
)

print(
    "hints:",
    task["hints"]
)

print(
    "success_signal:",
    task["success_signal"]
)

print(
    "expected_answer_type:",
    task["expected_answer_type"]
)

print(
    "difficulty:",
    task["difficulty"]
)

print(
    "question_type:",
    task["question_type"]
)


# ============================================================
# VALIDATION
# ============================================================

print()
print("VALIDATION")
print("----------")

try:

    engine.validate_task(
        task,
        engine.build_task_spec(
            learner,
            recommendation,
            concept
        )
    )

    print(
        "strict validation: PASS"
    )

except ContentValidationError as exc:

    print(
        "strict validation: FAIL"
    )

    print(
        "error:",
        exc
    )

    raise


# ============================================================
# DYNAMIC CHECKS
# ============================================================

print()
print("DYNAMIC CONTENT CHECKS")
print("-----------------------")

checks = {

    "correct concept":
        task["concept"]
        == "modulo operator",

    "correct strategy":
        task["strategy"]
        == "practice_first",

    "question exists":
        len(
            task["question"]
        ) >= 10,

    "success signal exists":
        len(
            task["success_signal"]
        ) >= 5,

    "valid difficulty":
        task["difficulty"]
        in engine.DIFFICULTIES,

    "valid question type":
        task["question_type"]
        in engine.QUESTION_TYPES,

    "not fallback":
        not task.get(
            "generation_fallback",
            False
        )
}


for name, passed in checks.items():

    print(
        f"{name}: "
        f"{'PASS' if passed else 'FAIL'}"
    )


# ============================================================
# FINAL
# ============================================================

if not all(
    checks.values()
):
    print()
    print(
        "RESULT: FAIL"
    )

    raise SystemExit(1)


print()
print("=" * 60)
print("RESULT: PASS")
print("=" * 60)

print()
print(
    "Sift successfully generated and validated "
    "a live Gemini learning task."
)

print()
print(
    "We are ready to connect this into "
    "the orchestrator only after this test passes."
)