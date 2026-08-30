# test_task_completion_persistence.py

from core.orchestrator import SiftOrchestrator


print()
print("=" * 60)
print("SIFT TASK COMPLETION PERSISTENCE TEST")
print("=" * 60)


# ============================================================
# 1. INITIALIZE
# ============================================================

print()
print("INITIALIZING SIFT")
print("-----------------")

sift = SiftOrchestrator()

print("Sift initialized: PASS")


# ============================================================
# 2. GET / CREATE LEARNER
# ============================================================

print()
print("LEARNER")
print("-------")


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


print("learner_id:", learner_id)

if hasattr(learner, "to_dict"):
    print(
        learner.to_dict()
    )
else:
    print(
        learner
    )


# ============================================================
# 3. LOAD HISTORY BEFORE
# ============================================================

print()
print("TASK HISTORY BEFORE")
print("-------------------")


history_before = (
    sift.repository
    .load_dynamic_task_history(
        learner_id=learner_id
    )
)


print(history_before)


# ============================================================
# 4. CREATE TEST RECOMMENDATION
# ============================================================

recommendation = {
    "action": "practice",
    "concept": "modulo operator",
    "mastery": 69.0,
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
# 5. GENERATE DYNAMIC TASK
# ============================================================

print()
print("GENERATING TASK")
print("----------------")


generated = (
    sift.generate_dynamic_task(
        learner_id=learner_id,
        recommendation=recommendation,
    )
)


if not isinstance(
    generated,
    dict
):
    raise AssertionError(
        "generate_dynamic_task() "
        "did not return a dictionary."
    )


task = generated.get(
    "task"
)


if not isinstance(
    task,
    dict
):
    raise AssertionError(
        "Generated result does not contain "
        "a valid task dictionary."
    )


required_task_fields = {
    "title",
    "question",
    "concept",
    "strategy",
}


missing_fields = (
    required_task_fields
    - set(task.keys())
)


if missing_fields:
    raise AssertionError(
        "Generated task is missing fields: "
        + ", ".join(
            sorted(
                missing_fields
            )
        )
    )


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
    "concept:",
    task["concept"]
)

print(
    "strategy:",
    task["strategy"]
)


# ============================================================
# 6. VERIFY TASK WAS SAVED
# ============================================================

print()
print("CHECKING PERSISTENCE")
print("--------------------")


history_after_generation = (
    sift.repository
    .load_dynamic_task_history(
        learner_id=learner_id
    )
)


print(
    history_after_generation
)


if not history_after_generation:
    raise AssertionError(
        "Generated task was not persisted."
    )


saved_task = (
    history_after_generation[-1]
)


if saved_task.get(
    "question"
) != task.get(
    "question"
):
    raise AssertionError(
        "Persisted question does not match "
        "generated question."
    )


if saved_task.get(
    "concept"
) != task.get(
    "concept"
):
    raise AssertionError(
        "Persisted concept does not match "
        "generated concept."
    )


if saved_task.get(
    "strategy"
) != task.get(
    "strategy"
):
    raise AssertionError(
        "Persisted strategy does not match "
        "generated strategy."
    )


print(
    "task saved: PASS"
)


# ============================================================
# 7. VERIFY INITIAL COMPLETION STATE
# ============================================================

print()
print("INITIAL COMPLETION STATE")
print("------------------------")


if (
    "completed"
    not in saved_task
):
    raise AssertionError(
        "Task history does not expose "
        "the completed field."
    )


if (
    saved_task["completed"]
    is not False
):
    raise AssertionError(
        "Newly generated task should have "
        "completed=False."
    )


print(
    "completed=False: PASS"
)


# ============================================================
# 8. FIND THE ACTUAL DATABASE ROW
# ============================================================

print()
print("LOCATING DATABASE ROW")
print("---------------------")


connection = (
    sift.repository.db._connect()
)


try:

    row = connection.execute(
        """
        SELECT
            id,
            learner_id,
            concept,
            strategy,
            action,
            title,
            explanation,
            task,
            completed,
            created_at
        FROM interventions
        WHERE learner_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            learner_id,
        )
    ).fetchone()

finally:

    connection.close()


if row is None:
    raise AssertionError(
        "Could not locate persisted "
        "intervention row."
    )


intervention_id = (
    row["id"]
)


print(
    "intervention_id:",
    intervention_id
)

print(
    "database row found: PASS"
)


# ============================================================
# 9. VERIFY DATABASE STARTS INCOMPLETE
# ============================================================

if (
    int(
        row["completed"]
    )
    != 0
):
    raise AssertionError(
        "Database task should initially "
        "have completed=0."
    )


print(
    "database completed=0: PASS"
)


# ============================================================
# 10. MARK TASK COMPLETED
# ============================================================

print()
print("MARKING TASK COMPLETED")
print("----------------------")


updated = (
    sift.repository
    .complete_intervention(
        intervention_id
    )
)


if updated is not True:
    raise AssertionError(
        "Repository failed to mark "
        "intervention completed."
    )


print(
    "repository completion update: PASS"
)


# ============================================================
# 11. VERIFY DATABASE COMPLETION
# ============================================================

connection = (
    sift.repository.db._connect()
)


try:

    completed_row = connection.execute(
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


if completed_row is None:
    raise AssertionError(
        "Intervention disappeared after update."
    )


if (
    int(
        completed_row["completed"]
    )
    != 1
):
    raise AssertionError(
        "Database completed value "
        "was not changed to 1."
    )


print(
    "database completed=1: PASS"
)


# ============================================================
# 12. VERIFY REPOSITORY HISTORY
# ============================================================

print()
print("CHECKING HISTORY AFTER COMPLETION")
print("----------------------------------")


history_after_completion = (
    sift.repository
    .load_dynamic_task_history(
        learner_id=learner_id
    )
)


print(
    history_after_completion
)


if not history_after_completion:
    raise AssertionError(
        "Task disappeared from history."
    )


completed_task = (
    history_after_completion[-1]
)


if (
    completed_task.get(
        "completed"
    )
    is not True
):
    raise AssertionError(
        "History does not report "
        "completed=True."
    )


print(
    "history completed=True: PASS"
)


# ============================================================
# 13. SIMULATE RESTART
# ============================================================

print()
print("SIMULATING RESTART")
print("------------------")


del sift


sift = SiftOrchestrator()


print(
    "new orchestrator created: PASS"
)


# ============================================================
# 14. RELOAD LEARNER
# ============================================================

print()
print("RELOADING LEARNER")
print("-----------------")


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
# 15. RELOAD TASK HISTORY
# ============================================================

print()
print("RELOADED TASK HISTORY")
print("---------------------")


reloaded_history = (
    sift.repository
    .load_dynamic_task_history(
        learner_id=reloaded_id
    )
)


for item in reloaded_history:
    print(
        item
    )


if not reloaded_history:
    raise AssertionError(
        "Task disappeared after restart."
    )


reloaded_task = (
    reloaded_history[-1]
)


# ============================================================
# 16. VERIFY CONTENT SURVIVED
# ============================================================

print()
print("VERIFYING TASK CONTENT")
print("----------------------")


if (
    reloaded_task.get(
        "question"
    )
    != task.get(
        "question"
    )
):
    raise AssertionError(
        "Question changed after restart."
    )


if (
    reloaded_task.get(
        "concept"
    )
    != task.get(
        "concept"
    )
):
    raise AssertionError(
        "Concept changed after restart."
    )


if (
    reloaded_task.get(
        "strategy"
    )
    != task.get(
        "strategy"
    )
):
    raise AssertionError(
        "Strategy changed after restart."
    )


print(
    "question survived: PASS"
)

print(
    "concept survived: PASS"
)

print(
    "strategy survived: PASS"
)


# ============================================================
# 17. VERIFY COMPLETION SURVIVED
# ============================================================

print()
print("VERIFYING COMPLETION")
print("--------------------")


if (
    reloaded_task.get(
        "completed"
    )
    is not True
):
    raise AssertionError(
        "completed=True did not survive restart."
    )


print(
    "completion survived restart: PASS"
)


# ============================================================
# 18. FINAL RESULT
# ============================================================

print()
print("=" * 60)
print("RESULT: PASS")
print("=" * 60)

print()
print(
    "Step 2 task-completion persistence is satisfied:"
)

print(
    """
Generate dynamic task
        ↓
Persist task
        ↓
completed = False
        ↓
Mark task completed
        ↓
completed = True
        ↓
Restart Sift
        ↓
Reload task
        ↓
completed = True
"""
)

print(
    "STEP 2 COMPLETE"
)