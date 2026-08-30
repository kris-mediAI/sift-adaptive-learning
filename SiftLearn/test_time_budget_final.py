from core.time_planner import TimeBudgetPlanner
from core.learner_model import LearnerProfile
from core.knowledge_model import Concept
from core.knowledge_graph import KnowledgeGraph
from core.retention import RetentionEngine
from core.adaptive_engine import AdaptiveEngine
from core.content_engine import ContentEngine


def make_engine():
    graph = KnowledgeGraph({"Functions": [], "Recursion": ["Functions"]})
    retention = RetentionEngine(review_threshold=65)
    return AdaptiveEngine(graph, retention)


def test_short_budgets_are_realistic():
    engine = make_engine()
    learner = LearnerProfile("Test", "Learn Python", "Python", 10, "Beginner", 30)
    fn = Concept("Functions")
    fn.update(20)
    rec = Concept("Recursion")
    rec.update(20)
    plan = TimeBudgetPlanner(engine).build_plan(learner, [fn, rec], 10)
    assert plan["total_minutes"] <= 10
    assert all(3 <= t["minutes"] <= 8 for t in plan["tasks"])


def test_budget_planner_leaves_overhead_for_longer_sessions():
    engine = make_engine()
    learner = LearnerProfile("Test", "Learn Python", "Python", 30, "Beginner", 30)
    fn = Concept("Functions")
    fn.update(20)
    rec = Concept("Recursion")
    rec.update(20)
    plan = TimeBudgetPlanner(engine).build_plan(learner, [fn, rec], 30)
    assert plan["total_minutes"] <= 28


def test_dynamic_prompt_receives_remaining_time():
    engine = make_engine()
    learner = LearnerProfile("Test", "Learn Python", "Python", 30, "Beginner", 30)
    concept = Concept("Functions")
    recommendation = {"concept": "Functions", "action": "teach", "strategy": "worked_example", "mastery": 20, "confidence": 0.2}
    content = ContentEngine(model=None, allow_fallback=True)
    result = content.generate(learner, recommendation, concept, remaining_minutes=7)
    assert result["spec"]["metadata"]["remaining_minutes"] == 7.0
    assert "remaining session time" in result["prompt"]
