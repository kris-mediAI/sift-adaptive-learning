from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent

def parse(path):
    ast.parse(path.read_text(encoding="utf-8")); print(f"PASS syntax: {path.relative_to(ROOT)}")

def contains(path, text):
    value = text in path.read_text(encoding="utf-8")
    print(("PASS" if value else "FAIL") + f" check: {text}")
    return value

for path in [ROOT/"app.py", ROOT/"ui"/"home.py", ROOT/"ui"/"components.py", ROOT/"ui"/"sidebar.py", ROOT/"ui"/"styles.py", ROOT/"core"/"session.py", ROOT/"core"/"orchestrator.py"]:
    parse(path)

assert contains(ROOT/"core"/"subject_graphs.py", '"modulo operator"')
assert contains(ROOT/"core"/"session.py", "_canonicalize_assessment_concept")
assert contains(ROOT/"app.py", "active_task(session)")
assert contains(ROOT/"app.py", "dynamic_answer_nonce")
assert contains(ROOT/"app.py", "sift.generate_dynamic_task(")
assert contains(ROOT/"app.py", "sift.complete_dynamic_task(")
assert contains(ROOT/"ui"/"components.py", "def track_visual")
assert contains(ROOT/"ui"/"components.py", "def sidebar_brand")
assert contains(ROOT/"ui"/"components.py", "def sidebar_profile")
assert "st.slider(" not in (ROOT/"ui"/"home.py").read_text(encoding="utf-8")
print("PASS check: Home has no permanent sliders")
print("\nSIFT FINAL UI/FLOW OFFLINE CHECKS: PASS")
