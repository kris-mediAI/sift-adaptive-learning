from core.learner_model import LearnerProfile
from core.knowledge_model import Concept
from core.knowledge_graph import KnowledgeGraph
from core.retention import RetentionEngine
from core.adaptive_engine import AdaptiveEngine
from core.time_planner import TimeBudgetPlanner


learner = LearnerProfile(
    name="Krishav",
    goal="Get an ML internship",
    subject="Python",
    available_minutes=20,
    current_level="Beginner",
    target_days=60
)


functions = Concept("Functions")
functions.update(87)
functions.update(90)


call_stack = Concept("Call Stack")
call_stack.update(
    30,
    "Does not understand active function calls",
    "conceptual"
)


recursion = Concept("Recursion")
recursion.update(
    40,
    "Cannot identify the base case",
    "conceptual"
)


concepts = [
    functions,
    call_stack,
    recursion
]


graph = KnowledgeGraph(
    {
        "Functions": [],
        "Call Stack": ["Functions"],
        "Recursion": ["Functions", "Call Stack"]
    }
)


retention = RetentionEngine(
    review_threshold=65
)


engine = AdaptiveEngine(
    knowledge_graph=graph,
    retention_engine=retention
)


planner = TimeBudgetPlanner(
    adaptive_engine=engine
)


plan = planner.build_plan(
    learner=learner,
    concepts=concepts
)


print("\nSIFT STUDY PLAN")
print("----------------")

print(
    f"Available time: "
    f"{plan['available_minutes']} minutes"
)

print(
    f"Planned time: "
    f"{plan['total_minutes']} minutes"
)

print(
    f"\n{plan['message']}"
)

print("\nTASKS")
print("-----")

for index, task in enumerate(
    plan["tasks"],
    start=1
):
    print(
        f"\n{index}. "
        f"{task['concept']}"
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