"""Offline checks for the current Sift technical learning-flow implementation."""
from pathlib import Path
import py_compile

ROOT=Path(__file__).resolve().parent
FILES=["app.py","ai/assessment.py","ai/teaching.py","core/adaptive_engine.py","core/content_engine.py","core/learner_model.py","core/orchestrator.py","core/progression.py","core/repository.py","core/session.py","database/db.py","ui/components.py","ui/home.py","ui/sidebar.py","ui/styles.py"]
for name in FILES:
    py_compile.compile(str(ROOT/name),doraise=True); print(f"PASS syntax: {name}")

app=(ROOT/"app.py").read_text(encoding="utf-8")
assert "def render_session" in app
assert "sift.complete_dynamic_task(" in app
assert "active_task(session)" in app
assert "last_generated" not in app
assert 'st.session_state.answer_box = ""' not in app
print("PASS Learn: single active-task source, dynamic completion, safe Streamlit state")

from core.knowledge_model import Concept
from core.learner_model import LearningRecord
from core.progression import concept_is_complete
c=Concept("Stacks",mastery=90); c.attempts=3; c.correct_attempts=3; c.last_score=90; c.confidence=80
records=[LearningRecord("Stacks","challenge",80,90,10,"challenge",True)]
assert concept_is_complete(c,records)
print("PASS progression: evidence-backed concept completion")
print("SIFT TECHNICAL UPGRADE OFFLINE CHECKS: PASS")
