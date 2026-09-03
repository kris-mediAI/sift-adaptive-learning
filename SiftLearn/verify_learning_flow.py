from pathlib import Path
import ast

ROOT=Path(__file__).resolve().parent
app=ROOT/"app.py"
ast.parse(app.read_text(encoding="utf-8")); print("PASS app syntax")
text=app.read_text(encoding="utf-8")
checks={
 "single backend task source":"active_task(session)" in text,
 "dynamic answer nonce":"dynamic_answer_nonce" in text,
 "task generation":"sift.generate_dynamic_task(" in text,
 "task completion":"sift.complete_dynamic_task(" in text,
 "result-first transition":"if result:" in text and "active_task(session)" in text,
 "no answer widget mutation":'st.session_state.answer_box = ""' not in text,
 "no diagnostic widget mutation":'st.session_state.diagnostic_answer = ""' not in text,
 "safe error path":"Sift couldn't evaluate that turn." in text,
}
for name,passed in checks.items(): print(("PASS " if passed else "FAIL ")+name)
assert all(checks.values())
print("\nSIFT LEARNING FLOW OFFLINE CHECKS: PASS")
