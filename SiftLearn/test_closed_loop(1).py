from test_support import isolated_orchestrator


print()
print("=" * 60)
print("SIFT CLOSED-LOOP LEARNING TEST")
print("=" * 60)


# ============================================================
# 1. INITIALIZE
# ============================================================

sift = isolated_orchestrator()


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
# 3. CREATE SESSION
# ============================================================

session = sift.create_session(
    learner_id
)


# ============================================================
# 4. INITIAL ASSESSMENT
# ============================================================

initial_question = """
What does the modulo operator (%) do in Python?
"""

initial_answer = """
The modulo operator performs normal division and gives
the division result.
"""


print()
print("=" * 60)
print("STEP 1: INITIAL ASSESSMENT")
print("=" * 60)


initial = sift.assess(
    learner_id=learner_id,
    question=initial_question,
    answer=initial_answer,
)


print()
print("ASSESSMENT")
print("----------")

print(
    initial
)


# ------------------------------------------------------------
# Validate assessment structure
# ------------------------------------------------------------

if not isinstance(
    initial,
    dict
):
    raise SystemExit(
        "FAIL: assessment result is not a dictionary."
    )

if "assessment" not in initial:
    raise SystemExit(
        "FAIL: assessment result has no 'assessment'."
    )

if "recommendation" not in initial:
    raise SystemExit(
        "FAIL: assessment result has no "
        "'recommendation'."
    )

assessment = (
    initial["assessment"]
)

recommendation = (
    initial["recommendation"]
)


if not isinstance(
    assessment,
    dict
):
    raise SystemExit(
        "FAIL: assessment is not a dictionary."
    )

if not isinstance(
    recommendation,
    dict
):
    raise SystemExit(
        "FAIL: recommendation is not a dictionary."
    )

required_assessment_fields = {
    "score",
    "correct",
    "concept",
    "mistake_type",
}

missing_assessment = (
    required_assessment_fields
    - assessment.keys()
)

if missing_assessment:
    raise SystemExit(
        "FAIL: assessment missing fields: "
        + ", ".join(
            sorted(
                missing_assessment
            )
        )
    )


required_recommendation_fields = {
    "action",
    "concept",
    "strategy",
}

missing_recommendation = (
    required_recommendation_fields
    - recommendation.keys()
)

if missing_recommendation:
    raise SystemExit(
        "FAIL: recommendation missing fields: "
        + ", ".join(
            sorted(
                missing_recommendation
            )
        )
    )


print()
print(
    "initial assessment: PASS"
)


# ============================================================
# 5. GENERATE DYNAMIC TASK
# ============================================================

print()
print("=" * 60)
print("STEP 2: GENERATE DYNAMIC TASK")
print("=" * 60)


generated = (
    sift.generate_dynamic_task(
        learner_id=learner_id,
        recommendation=recommendation,
    )
)


print()
print("GENERATED RESULT")
print("----------------")
print(
    generated
)


if not isinstance(
    generated,
    dict
):
    raise SystemExit(
        "FAIL: generated result is not a dictionary."
    )

if "task" not in generated:
    raise SystemExit(
        "FAIL: generated result has no task."
    )

task = (
    generated["task"]
)


if not isinstance(
    task,
    dict
):
    raise SystemExit(
        "FAIL: generated task is not a dictionary."
    )


required_task_fields = {
    "title",
    "question",
    "concept",
    "strategy",
}


missing_task = (
    required_task_fields
    - task.keys()
)

if missing_task:
    raise SystemExit(
        "FAIL: generated task missing fields: "
        + ", ".join(
            sorted(
                missing_task
            )
        )
    )


print()
print("TASK")
print("----")

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
# 6. ACTIVE INTERVENTION CHECK
# ============================================================

print()
print("ACTIVE INTERVENTION")
print("-------------------")


active = (
    session.active_intervention
)


print(
    active
)


if active is None:
    raise SystemExit(
        "FAIL: generated task did not become "
        "the active intervention."
    )

if not active.get(
    "dynamic",
    False
):
    raise SystemExit(
        "FAIL: active intervention is not "
        "marked as dynamic."
    )

if active.get(
    "concept"
) != task.get(
    "concept"
):
    raise SystemExit(
        "FAIL: active intervention concept "
        "does not match generated task."
    )

if active.get(
    "strategy"
) != task.get(
    "strategy"
):
    raise SystemExit(
        "FAIL: active intervention strategy "
        "does not match generated task."
    )

if active.get(
    "pre_mastery"
) is None:
    raise SystemExit(
        "FAIL: pre-mastery was not captured."
    )


pre_mastery = float(
    active[
        "pre_mastery"
    ]
)


print()
print(
    "active dynamic task: PASS"
)

print(
    "pre_mastery:",
    pre_mastery
)


# ============================================================
# 7. ANSWER GENERATED TASK
# ============================================================

task_question = (
    task[
        "question"
    ]
)

task_answer = """
The modulo operator gives the remainder after division.
For example, 17 % 5 is 2 because 5 goes into 17 three
whole times and leaves 2.
"""


print()
print("=" * 60)
print("STEP 3: LEARNER ANSWERS GENERATED TASK")
print("=" * 60)

print()
print("QUESTION")
print("--------")
print(
    task_question
)

print()
print("ANSWER")
print("------")
print(
    task_answer
)

# ============================================================
# Capture pre-completion learning evidence
# ============================================================

concept_before_completion = session.concepts.get(
    task["concept"]
)

if concept_before_completion is None:
    raise SystemExit(
        "FAIL: task concept is not loaded before completion."
    )

before_attempts = int(
    getattr(
        concept_before_completion,
        "attempts",
        0
    )
)

before_correct_attempts = int(
    getattr(
        concept_before_completion,
        "correct_attempts",
        0
    )
)
# ============================================================
# 8. COMPLETE DYNAMIC TASK
# ============================================================

print()
print("=" * 60)
print("STEP 4: COMPLETE DYNAMIC TASK")
print("=" * 60)


completed = (
    sift.complete_dynamic_task(
        learner_id=learner_id,
        question=task_question,
        answer=task_answer,
    )
)


print()
print("COMPLETION RESULT")
print("-----------------")
print(
    completed
)


if not isinstance(
    completed,
    dict
):
    raise SystemExit(
        "FAIL: completion result is not a dictionary."
    )


# ============================================================
# 9. POST-ASSESSMENT CHECK
# ============================================================

print()
print("POST-INTERVENTION ASSESSMENT")
print("----------------------------")


completed_assessment = (
    completed.get(
        "assessment"
    )
)


print(
    completed_assessment
)


if not isinstance(
    completed_assessment,
    dict
):
    raise SystemExit(
        "FAIL: no post-intervention assessment."
    )


required_post_fields = {
    "score",
    "correct",
    "concept",
    "mistake_type",
}

missing_post = (
    required_post_fields
    - completed_assessment.keys()
)

if missing_post:
    raise SystemExit(
        "FAIL: post-assessment missing fields: "
        + ", ".join(
            sorted(
                missing_post
            )
        )
    )


print()
print(
    "post-assessment: PASS"
)


# ============================================================
# 10. CONCEPT UPDATE CHECK
# ============================================================

print()
print("UPDATED CONCEPT")
print("---------------")


updated_concept = (
    completed.get(
        "concept"
    )
)


print(
    updated_concept
)


if not isinstance(
    updated_concept,
    dict
):
    raise SystemExit(
        "FAIL: updated concept missing."
    )

if "mastery" not in updated_concept:
    raise SystemExit(
        "FAIL: updated concept has no mastery."
    )

post_mastery = float(
    updated_concept[
        "mastery"
    ]
)


print()
print(
    "post_mastery:",
    post_mastery
)


# Validate learning evidence.
#
# Mastery does not have to increase after every correct answer.
# A correct answer at the current mastery level can be
# confirming evidence. What must be recorded is the new attempt,
# correctness, and latest score.

if "attempts" not in updated_concept:
    raise SystemExit(
        "FAIL: updated concept has no attempts."
    )

if "correct_attempts" not in updated_concept:
    raise SystemExit(
        "FAIL: updated concept has no correct_attempts."
    )

if "last_score" not in updated_concept:
    raise SystemExit(
        "FAIL: updated concept has no last_score."
    )

if int(updated_concept["attempts"]) <= before_attempts:
    raise SystemExit(
        "FAIL: assessment attempt was not recorded."
    )

if int(updated_concept["correct_attempts"]) <= before_correct_attempts:
    raise SystemExit(
        "FAIL: correct evidence was not recorded."
    )

if float(updated_concept["last_score"]) != float(
    completed_assessment["score"]
):
    raise SystemExit(
        "FAIL: latest assessment score was not recorded."
    )

if not 0.0 <= post_mastery <= 100.0:
    raise SystemExit(
        "FAIL: mastery left the valid range."
    )

print("learning evidence: PASS")
print("mastery range: PASS")




# ============================================================
# 11. LEARNING GAIN CHECK
# ============================================================

print()
print("LEARNING GAIN")
print("-------------")


learning_gain = (
    completed.get(
        "learning_gain"
    )
)


print(
    learning_gain
)


if learning_gain is None:
    raise SystemExit(
        "FAIL: learning gain was not calculated."
    )


expected_gain = round(
    post_mastery - pre_mastery,
    2
)


if round(
    float(learning_gain),
    2
) != expected_gain:
    raise SystemExit(
        "FAIL: learning gain does not match "
        "post_mastery - pre_mastery."
    )


print()
print(
    "learning gain: PASS"
)


# ============================================================
# 12. LEARNING RECORD CHECK
# ============================================================

print()
print("LEARNING RECORD")
print("---------------")


learning_record = (
    completed.get(
        "learning_record"
    )
)


print(
    learning_record
)


if not isinstance(
    learning_record,
    dict
):
    raise SystemExit(
        "FAIL: LearningRecord missing."
    )


required_record_fields = {
    "concept",
    "strategy",
    "pre_mastery",
    "post_mastery",
    "learning_gain",
    "completed",
}


missing_record = (
    required_record_fields
    - learning_record.keys()
)

if missing_record:
    raise SystemExit(
        "FAIL: LearningRecord missing fields: "
        + ", ".join(
            sorted(
                missing_record
            )
        )
    )


if not learning_record[
    "completed"
]:
    raise SystemExit(
        "FAIL: LearningRecord is not marked completed."
    )


if learning_record[
    "concept"
] != task[
    "concept"
]:
    raise SystemExit(
        "FAIL: LearningRecord concept mismatch."
    )


if learning_record[
    "strategy"
] != task[
    "strategy"
]:
    raise SystemExit(
        "FAIL: LearningRecord strategy mismatch."
    )


print()
print(
    "LearningRecord: PASS"
)


# ============================================================
# 13. STRATEGY EVIDENCE CHECK
# ============================================================

print()
print("STRATEGY EFFECTIVENESS")
print("----------------------")


strategy_effectiveness = (
    completed.get(
        "strategy_effectiveness"
    )
)


print(
    strategy_effectiveness
)


if strategy_effectiveness is None:
    raise SystemExit(
        "FAIL: strategy effectiveness missing."
    )


print()
print(
    "strategy evidence: PASS"
)


# ============================================================
# 14. NEXT RECOMMENDATION CHECK
# ============================================================

print()
print("NEXT RECOMMENDATION")
print("-------------------")


next_recommendation = (
    completed.get(
        "next_recommendation"
    )
)


print(
    next_recommendation
)


if not isinstance(
    next_recommendation,
    dict
):
    raise SystemExit(
        "FAIL: next recommendation missing."
    )


required_next_fields = {
    "action",
    "concept",
    "strategy",
}


missing_next = (
    required_next_fields
    - next_recommendation.keys()
)

if missing_next:
    raise SystemExit(
        "FAIL: next recommendation missing fields: "
        + ", ".join(
            sorted(
                missing_next
            )
        )
    )


print()
print(
    "next recommendation: PASS"
)


# ============================================================
# 15. ACTIVE INTERVENTION CLEARED
# ============================================================

if (
    session.active_intervention
    is not None
):
    raise SystemExit(
        "FAIL: active intervention was not cleared."
    )


print()
print(
    "active intervention cleared: PASS"
)


# ============================================================
# 16. LEARNER STATE CHECK
# ============================================================

print()
print("LEARNER STATE")
print("-------------")


print(
    session.learner.to_dict()
)


if not session.learner.learning_records:
    raise SystemExit(
        "FAIL: learner has no learning records."
    )


latest_record = (
    session.learner.learning_records[
        -1
    ]
)


if latest_record.concept != (
    task["concept"]
):
    raise SystemExit(
        "FAIL: learner's latest record "
        "has the wrong concept."
    )


print()
print(
    "learner state update: PASS"
)


# ============================================================
# FINAL
# ============================================================

print()
print("=" * 60)
print("RESULT: PASS")
print("=" * 60)

print()
print(
    "Sift completed the closed-loop learning cycle:"
)

print(
    """
    Initial Assessment
          ↓
    Adaptive Decision
          ↓
    Gemini Dynamic Task
          ↓
    Learner Answer
          ↓
    Reassessment
          ↓
    Knowledge Update
          ↓
    Learning Gain
          ↓
    LearningRecord
          ↓
    Strategy Evidence
          ↓
    Next Recommendation
    """
)

print(
    "STEP 1 — CLOSED-LOOP LEARNING — SATISFIED"
)