from test_support import isolated_orchestrator


print()
print("=" * 60)
print("SIFT DYNAMIC ORCHESTRATOR TEST")
print("=" * 60)


# ============================================================
# ORCHESTRATOR
# ============================================================

sift = isolated_orchestrator()


# ============================================================
# LEARNER
# ============================================================

learner_id, learner = (
    sift.get_or_create_learner(
        name="Krishav",
        goal="Get an ML internship",
        subject="Python",
        available_minutes=20,
        current_level="Beginner",
        target_days=60,
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
# SESSION
# ============================================================

session = sift.create_session(
    learner_id
)


print()
print("LOADED CONCEPTS")
print("---------------")

for concept in session.concepts.values():
    print(
        concept.to_dict()
    )


# ============================================================
# MAKE SURE WE HAVE A CONCEPT
# ============================================================

if "modulo operator" not in session.concepts:

    from core.knowledge_model import Concept

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

    session.concepts[
        "modulo operator"
    ] = concept

else:

    concept = session.concepts[
        "modulo operator"
    ]


# ============================================================
# RECOMMENDATION
# ============================================================

recommendation = {
    "action": "practice",

    "concept": "modulo operator",

    "mastery": getattr(
        concept,
        "mastery",
        69
    ),

    "confidence": getattr(
        concept,
        "confidence",
        70
    ),

    "priority": 25,

    "strategy": "practice_first",

    "target_concept": "modulo operator",

    "diagnosis": "direct_concept_gap",
}


print()
print("ADAPTIVE DECISION")
print("-----------------")

for key, value in recommendation.items():

    print(
        f"{key}: {value}"
    )


# ============================================================
# DYNAMIC GENERATION
# ============================================================

print()
print("GENERATING DYNAMIC TASK")
print("-----------------------")

result = sift.generate_dynamic_task(
    learner_id=learner_id,
    recommendation=recommendation,
)


# ============================================================
# SPEC
# ============================================================

print()
print("TASK SPEC")
print("---------")

for key, value in result[
    "spec"
].items():

    print(
        f"{key}: {value}"
    )


# ============================================================
# TASK
# ============================================================

task = result[
    "task"
]

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
# CHECKS
# ============================================================

print()
print("ORCHESTRATOR CHECKS")
print("-------------------")

checks = {

    "content engine exists":
        sift.content_engine is not None,

    "Gemini model configured":
        bool(
            getattr(
                sift.content_engine.model,
                "model_name",
                None
            )
        ),

    "correct concept":
        task["concept"]
        == "modulo operator",

    "correct strategy":
        task["strategy"]
        == "practice_first",

    "correct action":
        task["action"]
        == "practice",

    "valid question":
        len(
            task["question"]
        ) >= 10,

    "validated difficulty":
        task["difficulty"]
        in sift.content_engine.DIFFICULTIES,

    "validated question type":
        task["question_type"]
        in sift.content_engine.QUESTION_TYPES,

    "not fallback":
        not task.get(
            "generation_fallback",
            False
        ),
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
        "=" * 60
    )

    print(
        "RESULT: FAIL"
    )

    print(
        "=" * 60
    )

    raise SystemExit(1)


print()
print(
    "=" * 60
)

print(
    "RESULT: PASS"
)

print(
    "=" * 60
)

print()
print(
    "Sift orchestrator can now request "
    "validated dynamic learning tasks."
)

print()
print(
    "Dynamic Content Engine integration "
    "is ready for the closed-loop test."
)