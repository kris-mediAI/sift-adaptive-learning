from core.orchestrator import SiftOrchestrator


print()
print("=" * 60)
print("SIFT ORCHESTRATOR TEST")
print("=" * 60)


# ============================================================
# 1. CREATE / LOAD LEARNER
# ============================================================

sift = SiftOrchestrator()

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
print(learner.to_dict())

print()
print("LEARNER ID")
print("----------")
print(learner_id)


# ============================================================
# 2. LOAD FULL SESSION STATE
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
# 3. ASSESSMENT
# ============================================================

question = """
What does the % operator do in Python?
"""

answer = """
It divides two numbers and gives the result.
"""

print()
print("=" * 60)
print("STEP 1: ASSESS")
print("=" * 60)

result = sift.assess(
    learner_id=learner_id,
    question=question,
    answer=answer,
)

print()
print("ASSESSMENT")
print("----------")

for key, value in result[
    "assessment"
].items():
    print(
        f"{key}: {value}"
    )


# ============================================================
# 4. ADAPTIVE DECISION
# ============================================================

print()
print("ADAPTIVE DECISION")
print("-----------------")

for key, value in result[
    "recommendation"
].items():
    print(
        f"{key}: {value}"
    )


# ============================================================
# 5. GENERATE INTERVENTION
# ============================================================

print()
print("=" * 60)
print("STEP 2: GENERATE INTERVENTION")
print("=" * 60)

intervention = (
    sift.generate_intervention(
        learner_id=learner_id,
        recommendation=result[
            "recommendation"
        ],
    )
)

print()
print("INTERVENTION")
print("------------")

if intervention:
    for key, value in intervention.items():
        print(
            f"{key}: {value}"
        )
else:
    print(
        "No intervention generated."
    )


# ============================================================
# 6. SIMULATE STUDENT RESPONSE
# ============================================================

follow_up_question = """
What is the result of 17 % 5,
and why?
"""

follow_up_answer = """
17 % 5 is 2 because 5 goes into 17
three times, which is 15, leaving 2.
"""


# ============================================================
# 7. COMPLETE INTERVENTION
# ============================================================

print()
print("=" * 60)
print("STEP 3: COMPLETE INTERVENTION")
print("=" * 60)

completion = (
    sift.complete_intervention(
        learner_id=learner_id,
        question=follow_up_question,
        answer=follow_up_answer,
    )
)

print()
print("POST-INTERVENTION ASSESSMENT")
print("----------------------------")

for key, value in completion[
    "assessment"
].items():
    print(
        f"{key}: {value}"
    )


print()
print("UPDATED CONCEPT")
print("---------------")

print(
    completion["concept"]
)


print()
print("LEARNING GAIN")
print("-------------")

print(
    completion["learning_gain"]
)


print()
print("STRATEGY")
print("--------")

print(
    completion["strategy"]
)


print()
print("STRATEGY EFFECTIVENESS")
print("----------------------")

print(
    completion[
        "strategy_effectiveness"
    ]
)


print()
print("NEXT RECOMMENDATION")
print("-------------------")

for key, value in completion[
    "next_recommendation"
].items():
    print(
        f"{key}: {value}"
    )


# ============================================================
# 8. BUILD STUDY PLAN
# ============================================================

print()
print("=" * 60)
print("STEP 4: BUILD NEXT STUDY PLAN")
print("=" * 60)

plan = sift.build_study_plan(
    learner_id=learner_id,
    available_minutes=20,
)

print()

for key in [
    "available_minutes",
    "total_minutes",
    "message",
]:
    if key in plan:
        print(
            f"{key}: {plan[key]}"
        )


print()
print("TASKS")
print("-----")

for index, task in enumerate(
    plan.get("tasks", []),
    start=1,
):
    if hasattr(
        task,
        "to_dict",
    ):
        task = task.to_dict()

    print()
    print(
        f"{index}. {task['concept']}"
    )

    print(
        f"   action: {task['action']}"
    )

    print(
        f"   time: {task['minutes']} min"
    )

    print(
        f"   priority: {task['priority']}"
    )

    print(
        f"   reason: {task['reason']}"
    )


# ============================================================
# 9. PERSISTENCE CHECK
# ============================================================

print()
print("=" * 60)
print("STEP 5: RESTART SIMULATION")
print("=" * 60)

new_sift = SiftOrchestrator()

reloaded_session = (
    new_sift.create_session(
        learner_id
    )
)

reloaded_state = (
    reloaded_session.get_state()
)

print()
print("RELOADED LEARNER")
print("----------------")

print(
    reloaded_state["learner"]
)


print()
print("RELOADED CONCEPTS")
print("-----------------")

for name, concept in (
    reloaded_state[
        "concepts"
    ].items()
):
    print(
        name,
        concept
    )


# ============================================================
# 10. FINAL SUMMARY
# ============================================================

print()
print("=" * 60)
print("SIFT ORCHESTRATOR COMPLETE")
print("=" * 60)

print()
print(
    "The complete adaptive pipeline executed:"
)

print(
    """
Assessment
    ↓
Knowledge Update
    ↓
Mistake Tracking
    ↓
Adaptive Decision
    ↓
Personalized Intervention
    ↓
Reassessment
    ↓
Learning Gain
    ↓
Strategy Evidence
    ↓
Persistence
    ↓
Study Plan
    ↓
Restart / Reload
"""
)

print(
    "Sift orchestrator test finished."
)

print("=" * 60)