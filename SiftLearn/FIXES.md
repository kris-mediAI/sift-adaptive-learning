
# SiftLearn Final UI + Closed-Loop Flow Fix

## Replace these files

Copy these files into the corresponding locations in your project:

```text
app.py
ui/__init__.py
ui/components.py
ui/home.py
ui/sidebar.py
ui/styles.py
core/session.py
core/subject_graphs.py
```

The `core` files are included because the diagnostic error is a backend
knowledge-graph validation issue, not merely a UI rendering issue.

## What was fixed

### 1. Diagnostic assessment concept mismatch

The UI diagnostic could send a valid answer into the backend, Gemini could
describe the concept naturally, and the session validator could then reject
that concept because it wasn't an exact graph node.

Example:

```text
Fundamental linear data structures
(Stack vs. Queue ordering principles)
```

The registered graph contains canonical nodes such as:

```text
Stacks
Queues
```

`core/session.py` now canonicalizes safe assessment labels to registered
subject-graph nodes before validation. It never creates an arbitrary graph
node from an LLM phrase.

### 2. Python modulo compatibility

`core/subject_graphs.py` explicitly registers:

```text
modulo operator
```

This matches the existing persisted/tested learning state and dynamic-task
pipeline.

### 3. Home is genuinely dynamic

Switching the active track now immediately changes:

- subject artwork
- active track label
- mastery
- study-plan values
- recommendation context
- adaptive banner text

### 4. Study-plan sliders are real controls

The Home page now exposes:

```text
Daily learning time (minutes/day)
Target timeline (days)
```

Changing either value immediately updates the active track's learner profile
and persists it through the existing repository.

Each subject keeps its own values.

### 5. No fake cross-track state

DSA, Python, ML, and Mathematics remain separate learning tracks. The UI
doesn't manufacture a combined mastery state that the backend doesn't own.

## Verify

Run:

```powershell
python verify_final_flow_patch.py
```

Then:

```powershell
streamlit run app.py
```

## Recommended flow test

1. Open DSA.
2. Submit the diagnostic.
3. Confirm there is no "concept is not part of graph" error.
4. Go Home.
5. Switch Python.
6. Confirm the artwork and study-plan values change.
7. Change Python's minutes/days.
8. Switch to DSA.
9. Confirm DSA retains its own values.
10. Switch back to Python.
11. Confirm Python retains the changed values.
12. Repeat with ML and Mathematics.
13. Complete a generated task and verify Progress/History update.

The patch does not modify the learning/scoring formulas. It makes the UI
use the existing backend correctly and prevents LLM concept wording from
escaping the registered knowledge graph.

## Final product flow update — 2026-08-26

- Fixed `_validate_assessment()` as an instance method. It uses the session's learner and graph, so it must not be a staticmethod.
- Kept strict graph validation and added deterministic normalization for common multi-concept DSA diagnostics such as stack-vs-queue wording.
- Home is now a clean learning-path dashboard; long-term study-plan sliders were removed from Home.
- Add Track / first-run subject selection is outside the creation form, so the selected subject changes immediately.
- Add Track now shows either a real Switch button for an existing track or the creation form for a new track.
- Added a per-day learning budget inside Learn. It does not mutate the long-term min/day plan.
- The per-day budget feeds the existing dependency-aware TimeBudgetPlanner.
- Added a lightweight real-time session countdown.
- Added persisted per-track learning streak state: current streak, longest streak, total active days, and last activity date.
- Streaks increment once per calendar day only when a completed learning intervention is recorded.
