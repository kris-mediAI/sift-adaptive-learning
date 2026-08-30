from core.orchestrator import SiftOrchestrator
from core.content_engine import ContentEngine


print()
print("=" * 60)
print("SIFT REAL TASK HISTORY TEST")
print("=" * 60)


# ============================================================
# ORCHESTRATOR
# ============================================================

sift = SiftOrchestrator()


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


# ============================================================
# CONCEPT
# ============================================================

from core.knowledge_model import Concept


if "modulo operator" not in session.concepts:

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
    "mastery": concept.mastery,
    "confidence": concept.confidence,
    "priority": 25,
    "strategy": "practice_first",
    "target_concept": "modulo operator",
    "diagnosis": "direct_concept_gap",
}


# ============================================================
# HISTORY BEFORE GENERATION
# ============================================================

before = (
    sift.repository
    .load_dynamic_task_history(
        learner_id=learner_id,
        limit=20,
    )
)


print()
print("TASK HISTORY BEFORE")
print("-------------------")
print(
    before
)


# ============================================================
# GENERATE TASK
# ============================================================

print()
print("GENERATING TASK")
print("----------------")

result = sift.generate_dynamic_task(
    learner_id=learner_id,
    recommendation=recommendation,
)


task = result["task"]


print()
print("GENERATED TASK")
print("--------------")
print(
    "title:",
    task["title"],
)

print(
    "question:",
    task["question"],
)

print(
    "concept:",
    task["concept"],
)

print(
    "strategy:",
    task["strategy"],
)


# ============================================================
# HISTORY AFTER GENERATION
# ============================================================

after = (
    sift.repository
    .load_dynamic_task_history(
        learner_id=learner_id,
        limit=20,
    )
)


print()
print("TASK HISTORY AFTER")
print("------------------")
print(
    after
)


# ============================================================
# CHECK PERSISTENCE
# ============================================================

saved = any(
    item.get(
        "question"
    )
    == task.get(
        "question"
    )
    for item in after
)


print()
print("PERSISTENCE CHECK")
print("-----------------")
print(
    "generated task saved:",
    "PASS" if saved else "FAIL",
)


if not saved:
    raise SystemExit(
        "Generated task was not persisted."
    )


# ============================================================
# RESTART SIMULATION
# ============================================================

print()
print("SIMULATING RESTART")
print("------------------")


sift_reloaded = (
    SiftOrchestrator()
)


reloaded_learner = (
    sift_reloaded.repository
    .load_learner(
        learner_id
    )
)


if reloaded_learner is None:
    raise SystemExit(
        "Learner could not be reloaded."
    )


reloaded_history = (
    sift_reloaded.repository
    .load_dynamic_task_history(
        learner_id=learner_id,
        limit=20,
    )
)


print()
print("RELOADED TASK HISTORY")
print("---------------------")
print(
    reloaded_history
)


reloaded_saved = any(
    item.get(
        "question"
    )
    == task.get(
        "question"
    )
    for item in reloaded_history
)


print()
print("RESTART CHECK")
print("-------------")
print(
    "task survived restart:",
    "PASS"
    if reloaded_saved
    else "FAIL",
)


if not reloaded_saved:
    raise SystemExit(
        "Task history did not survive restart."
    )


# ============================================================
# CONTENT ENGINE HISTORY CHECK
# ============================================================

print()
print("CONTENT ENGINE HISTORY CHECK")
print("-----------------------------")


engine = (
    sift_reloaded.content_engine
)

spec = (
    engine.build_task_spec(
        learner=reloaded_learner,
        recommendation=recommendation,
        concept=concept,
        previous_tasks=reloaded_history,
    )
)


history_in_spec = (
    spec.metadata.get(
        "previous_tasks",
        [],
    )
)


print(
    "history passed into TaskSpec:",
    len(history_in_spec),
)


if not history_in_spec:
    raise SystemExit(
        "Persisted task history was not "
        "passed into TaskSpec."
    )


print()
print("=" * 60)
print("RESULT: PASS")
print("=" * 60)

print()
print(
    "Sift now persists generated dynamic tasks "
    "and reloads them for future novelty checks."
)

print()
print(
    "Real task history integration is working."
)