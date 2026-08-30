from pathlib import Path
import ast
from datetime import date, timedelta

ROOT = Path(__file__).resolve().parent
FILES = ["app.py","core/session.py","core/learner_model.py","core/repository.py","database/db.py","ui/home.py","ui/components.py","ui/sidebar.py","ui/styles.py"]
for rel in FILES:
    ast.parse((ROOT/rel).read_text(encoding="utf-8")); print("PASS syntax:", rel)

session_text=(ROOT/"core/session.py").read_text(encoding="utf-8")
assert "multi_concept_aliases" in session_text
assert "def mark_learning_activity" in (ROOT/"core/learner_model.py").read_text(encoding="utf-8")
print("PASS assessment + streak architecture")

app=(ROOT/"app.py").read_text(encoding="utf-8")
components=(ROOT/"ui/components.py").read_text(encoding="utf-8")
assert "def render_session" in app and "complete_dynamic_task(" in app
assert "def track_visual" in components and "def sidebar_brand" in components and "def sidebar_profile" in components
assert "st.slider(" not in (ROOT/"ui/home.py").read_text(encoding="utf-8")
print("PASS UI/component integrity")

from core.learner_model import LearnerProfile
today=date.today(); x=LearnerProfile("x","g","Python",30,"Beginner",30)
x.mark_learning_activity(today-timedelta(days=2)); x.mark_learning_activity(today-timedelta(days=2)); x.mark_learning_activity(today-timedelta(days=1)); x.mark_learning_activity(today)
q=x.get_streak(); assert q["current"]==3 and q["longest"]==3 and q["total_active_days"]==3
print("PASS streak semantics")
print("\nSIFT FINAL PRODUCT OFFLINE CHECKS: PASS")
