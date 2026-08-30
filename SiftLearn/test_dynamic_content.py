from core.content_engine import ContentEngine
from core.learner_model import LearnerProfile
from core.knowledge_model import Concept


print()
print("=" * 60)
print("SIFT DYNAMIC CONTENT ENGINE TEST")
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
# RECOMMENDATION
# ============================================================

recommendation = {
    "action": "practice",

    "concept": "modulo operator",

    "mastery": 69,

    "confidence": 70,

    "priority": 25.4,

    "strategy": "practice_first",

    "target_concept": "modulo operator",

    "diagnosis": "direct_concept_gap"
}


# ============================================================
# ENGINE
# ============================================================

engine = ContentEngine()


# ============================================================
# BUILD SPEC
# ============================================================

spec = engine.build_task_spec(
    learner=learner,
    recommendation=recommendation,
    concept=concept
)


print()
print("TASK SPEC")
print("---------")

for key, value in spec.to_dict().items():

    print(
        f"{key}: {value}"
    )


# ============================================================
# CHECK SPEC
# ============================================================

print()
print("SPEC CHECKS")
print("-----------")

checks = {

    "concept":
        spec.concept
        == "modulo operator",

    "strategy":
        spec.strategy
        == "practice_first",

    "action":
        spec.action
        == "practice",

    "misconception":
        spec.misconception
        is not None,

    "difficulty":
        spec.difficulty
        in {
            "easy",
            "medium",
            "hard",
            "adaptive"
        },

    "question_type":
        spec.question_type
        in engine.QUESTION_TYPES,

    "novelty":
        spec.novelty
        in engine.NOVELTY_LEVELS,

    "constraints":
        len(spec.constraints)
        > 0
}


for name, passed in checks.items():

    print(
        f"{name}: "
        f"{'PASS' if passed else 'FAIL'}"
    )


# ============================================================
# FALLBACK GENERATION
# ============================================================

print()
print("OFFLINE TASK GENERATION")
print("-----------------------")

result = engine.generate(
    learner=learner,
    recommendation=recommendation,
    concept=concept
)


task = result["task"]


print(
    "title:",
    task["title"]
)

print(
    "question:",
    task["question"]
)

print(
    "difficulty:",
    task["difficulty"]
)

print(
    "question_type:",
    task["question_type"]
)

print(
    "concept:",
    task["concept"]
)

print(
    "strategy:",
    task["strategy"]
)


# ============================================================
# FINAL
# ============================================================

all_passed = all(
    checks.values()
)

print()
print("=" * 60)

if all_passed:
    print(
        "RESULT: PASS"
    )

    print()
    print(
        "Sift can now convert adaptive decisions "
        "into dynamic task specifications."
    )

    print(
        "The next step is connecting this "
        "specification to the actual Gemini "
        "content generator."
    )

else:
    print(
        "RESULT: FAIL"
    )

print("=" * 60)