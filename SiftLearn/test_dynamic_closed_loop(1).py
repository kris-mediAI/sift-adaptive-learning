from test_support import isolated_orchestrator


print()
print("=" * 60)
print("SIFT REAL DYNAMIC CLOSED-LOOP TEST")
print("=" * 60)


# ============================================================
# 1. INITIALIZE
# ============================================================

print()
print("INITIALIZING")
print("------------")

sift = isolated_orchestrator()

print("orchestrator: PASS")


# ============================================================
# 2. GET LEARNER
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
print("learner_id:", learner_id)


# ============================================================
# 3. GET SESSION
# ============================================================

session = (
    sift.get_session(
        learner_id
    )
)


print()
print("SESSION")
print("-------")

if session is None:
    raise AssertionError(
        "Could not create learner session."
    )

print("session: PASS")


# ============================================================
# 4. CREATE ADAPTIVE RECOMMENDATION
# ============================================================

recommendation = {
    "action": "practice",
    "concept": "modulo operator",
    "mastery": 65.0,
    "confidence": 70.0,
    "priority": 25.0,
    "strategy": "practice_first",
    "target_concept": "modulo operator",
    "diagnosis": "direct_concept_gap",
}


print()
print("RECOMMENDATION")
print("--------------")
print(recommendation)


# ============================================================
# 5. MAKE SURE THERE IS NO ACTIVE TASK
# ============================================================

if (
    session.active_intervention
    is not None
):
    raise AssertionError(
        "A dynamic intervention is already active. "
        "Use a fresh learner/session or complete "
        "the existing task first."
    )


print()
print("ACTIVE TASK BEFORE")
print("-------------------")
print("None: PASS")


# ============================================================
# 6. GENERATE DYNAMIC TASK
# ============================================================

print()
print("GENERATING DYNAMIC TASK")
print("-----------------------")


result = (
    sift.generate_dynamic_task(
        learner_id=learner_id,
        recommendation=recommendation,
    )
)


if not isinstance(
    result,
    dict
):
    raise AssertionError(
        "generate_dynamic_task() "
        "did not return a dictionary."
    )


task = result.get(
    "task"
)


if not isinstance(
    task,
    dict
):
    raise AssertionError(
        "Generated result does not contain "
        "a valid task."
    )


question = task.get(
    "question"
)


if not question:
    raise AssertionError(
        "Generated task has no question."
    )


print()
print("GENERATED TASK")
print("--------------")
print(
    "title:",
    task.get(
        "title"
    )
)
print(
    "question:",
    question
)
print(
    "concept:",
    task.get(
        "concept"
    )
)
print(
    "strategy:",
    task.get(
        "strategy"
    )
)


# ============================================================
# 7. VERIFY ACTIVE INTERVENTION
# ============================================================

print()
print("ACTIVE INTERVENTION")
print("--------------------")


active = (
    session.active_intervention
)


if active is None:
    raise AssertionError(
        "Generated task was not made active."
    )


if (
    active.get(
        "dynamic"
    )
    is not True
):
    raise AssertionError(
        "Active intervention is not marked dynamic."
    )


active_task = (
    active.get(
        "intervention"
    )
)


if not isinstance(
    active_task,
    dict
):
    raise AssertionError(
        "Active intervention does not contain "
        "the generated task."
    )


if (
    active_task.get(
        "question"
    )
    != question
):
    raise AssertionError(
        "Active question does not match "
        "generated question."
    )


print(
    "active dynamic task: PASS"
)

print(
    "question matches: PASS"
)


# ============================================================
# 8. VERIFY INTERVENTION ID
# ============================================================

intervention_id = (
    active.get(
        "intervention_id"
    )
)


if intervention_id is None:
    raise AssertionError(
        "Active dynamic task has no persisted "
        "intervention_id."
    )


print(
    "intervention_id:",
    intervention_id
)

print(
    "exact persisted task linked: PASS"
)


# ============================================================
# 9. LOAD PRE-ANSWER STATE
# ============================================================

concept_name = (
    task.get(
        "concept"
    )
    or recommendation.get(
        "concept"
    )
)


concept_before = (
    session.concepts.get(
        concept_name
    )
)


if concept_before is None:
    raise AssertionError(
        "Target concept is not loaded."
    )


mastery_before = (
    concept_before.mastery
)

attempts_before = (
    concept_before.attempts
)

correct_before = (
    concept_before.correct_attempts
)

records_before = len(
    session.learner.learning_records
)


print()
print("STATE BEFORE ANSWER")
print("-------------------")
print(
    "mastery:",
    mastery_before
)
print(
    "attempts:",
    attempts_before
)
print(
    "correct attempts:",
    correct_before
)
print(
    "learning records:",
    records_before
)


# ============================================================
# 10. SUBMIT ANSWER THROUGH REAL PIPELINE
# ============================================================

print()
print("SUBMITTING ANSWER")
print("------------------")


# For the modulo task generated by the current test,
# the answer is expected to be 2.
#
# The important point is that we submit through:
#
#     complete_dynamic_task()
#
# NOT:
#
#     repository.complete_intervention()
#
# and NOT:
#
#     database.complete_intervention()
#

answer = "2"


completion_result = (
    sift.complete_dynamic_task(
        learner_id=learner_id,
        question=question,
        answer=answer,
    )
)


print(
    "completion returned: PASS"
)


print()
print("COMPLETION RESULT")
print("-----------------")
print(
    completion_result
)


# ============================================================
# 11. ACTIVE TASK MUST BE CLEARED
# ============================================================

print()
print("ACTIVE TASK AFTER ANSWER")
print("-------------------------")


if (
    session.active_intervention
    is not None
):
    raise AssertionError(
        "Active dynamic task was not cleared "
        "after completion."
    )


print(
    "active task cleared: PASS"
)


# ============================================================
# 12. VERIFY DATABASE COMPLETION
# ============================================================

print()
print("DATABASE COMPLETION")
print("-------------------")


connection = (
    sift.repository.db._connect()
)


try:

    row = connection.execute(
        """
        SELECT
            id,
            completed
        FROM interventions
        WHERE id = ?
        """,
        (
            intervention_id,
        )
    ).fetchone()

finally:

    connection.close()


if row is None:
    raise AssertionError(
        "Persisted intervention disappeared."
    )


if (
    int(
        row["completed"]
    )
    != 1
):
    raise AssertionError(
        "The exact dynamic task was not "
        "marked completed in the database."
    )


print(
    "exact task completed=True: PASS"
)


# ============================================================
# 13. VERIFY LEARNER STATE CHANGED / PROCESSED
# ============================================================

concept_after = (
    session.concepts.get(
        concept_name
    )
)


if concept_after is None:
    raise AssertionError(
        "Concept disappeared after completion."
    )


mastery_after = (
    concept_after.mastery
)

attempts_after = (
    concept_after.attempts
)

correct_after = (
    concept_after.correct_attempts
)

records_after = len(
    session.learner.learning_records
)


print()
print("STATE AFTER ANSWER")
print("------------------")
print(
    "mastery:",
    mastery_after
)
print(
    "attempts:",
    attempts_after
)
print(
    "correct attempts:",
    correct_after
)
print(
    "learning records:",
    records_after
)


# At minimum, the answer must have been processed.
if (
    attempts_after
    <= attempts_before
):
    raise AssertionError(
        "Learner attempt count did not increase."
    )


print(
    "assessment processed: PASS"
)


# ============================================================
# 14. VERIFY LEARNING RECORD
# ============================================================

if (
    records_after
    <= records_before
):
    raise AssertionError(
        "No new learning record was created."
    )


print(
    "learning record created: PASS"
)


# ============================================================
# 15. VERIFY PERSISTED TASK HISTORY
# ============================================================

print()
print("PERSISTED TASK HISTORY")
print("-----------------------")


history = (
    sift.repository
    .load_dynamic_task_history(
        learner_id=learner_id
    )
)


if not history:
    raise AssertionError(
        "No dynamic task history exists."
    )


matching_tasks = [
    item
    for item in history
    if item.get(
        "question"
    ) == question
]


if not matching_tasks:
    raise AssertionError(
        "Completed dynamic task was not found "
        "in persisted task history."
    )


persisted_task = (
    matching_tasks[-1]
)


if (
    persisted_task.get(
        "completed"
    )
    is not True
):
    raise AssertionError(
        "Persisted task history does not show "
        "completed=True."
    )


print(
    "task present in history: PASS"
)

print(
    "history completed=True: PASS"
)


# ============================================================
# 16. VERIFY NEXT ADAPTIVE DECISION
# ============================================================

print()
print("NEXT ADAPTIVE DECISION")
print("----------------------")


next_recommendation = (
    session.engine.recommend(
        learner=session.learner,
        concepts=list(
            session.concepts.values()
        ),
    )
)


if next_recommendation is None:
    raise AssertionError(
        "No next adaptive recommendation "
        "was produced."
    )


print(
    "next recommendation: PASS"
)

print(
    next_recommendation
)


# ============================================================
# 17. RESTART
# ============================================================

print()
print("SIMULATING RESTART")
print("------------------")


del sift


sift = isolated_orchestrator()


reloaded_id, reloaded_learner = (
    sift.get_or_create_learner(
        name="Krishav",
        goal="Get an ML internship",
        subject="Python",
        available_minutes=20,
        current_level="Beginner",
        target_days=60,
    )
)


if (
    reloaded_id
    != learner_id
):
    raise AssertionError(
        "Learner ID changed after restart."
    )


print(
    "learner survived restart: PASS"
)


# ============================================================
# 18. VERIFY COMPLETED TASK AFTER RESTART
# ============================================================

reloaded_history = (
    sift.repository
    .load_dynamic_task_history(
        learner_id=reloaded_id
    )
)


reloaded_matches = [
    item
    for item in reloaded_history
    if item.get(
        "question"
    ) == question
]


if not reloaded_matches:
    raise AssertionError(
        "Completed dynamic task disappeared "
        "after restart."
    )


reloaded_task = (
    reloaded_matches[-1]
)


if (
    reloaded_task.get(
        "completed"
    )
    is not True
):
    raise AssertionError(
        "Completed task did not survive restart."
    )


print(
    "completed task survived restart: PASS"
)


# ============================================================
# 19. FINAL RESULT
# ============================================================

print()
print("=" * 60)
print("RESULT: PASS")
print("=" * 60)

print()
print(
    """
REAL DYNAMIC CLOSED LOOP VERIFIED

Generate
    ↓
Activate
    ↓
Persist
    ↓
Learner answers
    ↓
Real completion pipeline
    ↓
Exact task completed
    ↓
Assessment processed
    ↓
Learner state updated
    ↓
Learning record created
    ↓
Next recommendation
    ↓
Restart
    ↓
Completed task survives

STEP 3 COMPLETE
"""
)