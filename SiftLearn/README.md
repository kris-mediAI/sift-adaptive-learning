
# Sift — Adaptive Learning

Sift is a session-first adaptive tutor. The product starts with a small set of broad learning areas, then lets the learner go as specific as needed with a custom topic. Sift uses demonstrated evidence—not a fixed lesson path—to choose the next explanation, difficulty, practice task, and review.

## Product surface

- **Sessions** — the primary workspace and entry point. Multiple sessions can exist for the same subject, each focused on a different topic.
- **Progress** — live evidence of demonstrated mastery and session-level progress.
- **History** — a transparent learning journal showing what the learner demonstrated, what Sift noticed, and why the next step changed.
- **Resources** — contextual help for the active session, including situation-aware tips and relevance-gated YouTube recommendations when configured.
- **Settings** — deliberately small set of useful preferences.

## Important architecture behavior

A learner can add:

- Data Structures & Algorithms
- Python
- Machine Learning
- Mathematics

Each track gets its own persisted learner/session ID through the existing
`SiftOrchestrator.get_or_create_learner(...)` and `create_session(...)`
path. The UI does not invent a second learning model.

Switching a track immediately changes the active learner/session in the UI.
It does not wait for a form submission.

The backend remains the source of truth for recommendations, assessment,
dynamic tasks, resources, mastery, and learning history.

## Run

```powershell
streamlit run app.py
```

## Replace

```text
app.py
ui/__init__.py
ui/components.py
ui/home.py
ui/sidebar.py
ui/styles.py
```

If your current `ui/home.py` is no longer referenced, it can remain in the
project, but this build does not depend on it.

## Final flow

Home is intentionally a clean dashboard. Long-term plan values stay visible as a summary, while the learner can change **today's available learning time** inside Learn without changing the long-term plan. That daily budget feeds the existing `TimeBudgetPlanner`.

Each completed learning intervention updates a persisted per-track streak. Multiple completions on the same day count once; a gap breaks the current streak while preserving the longest streak.

The diagnostic validator remains strict. LLM-generated concept labels are normalized to registered graph concepts before validation rather than bypassing the graph safety check.


## Final build notes

- Learn is backed by the persisted `SiftSession`/repository state. The UI does not maintain a second mastery model.
- Dynamic task generation retries the configured Gemini model, can fail over to a secondary stable model for transient failures, and then falls back to deterministic, concept-specific teaching/task content when AI is unavailable or returns invalid content.
- Generated tasks are semantically checked against their target concept, so a structurally valid but unrelated task is rejected and regenerated before reaching the learner.
- Assessment is anchored to the active dynamic task concept, preventing fresh-account first-turn failures caused by a model returning a related but unregistered concept label.
- Hints are progressive; the learner can request support without immediately revealing the answer.
- Study Plan is a separate planning surface. Daily minutes and horizon are preferences, while actual learning time is recorded from completed learning turns.
- The sidebar keeps Sessions, Progress, History, Resources, and Settings as the core navigation. There is no redundant permanent Learn/Study Plan destination. Planning controls live inside session creation where they are useful.
- Gemini configuration is optional for offline development; set `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) in the environment. `GEMINI_MODEL` defaults to `gemini-3.5-flash-lite` with `gemini-2.5-flash-lite` as a transient-failure fallback. Secrets are intentionally not shipped in `.env`.
- YouTube resources are optional. Without `YOUTUBE_API_KEY`, the resource layer reports no external search configuration rather than fabricating resources.

## Final reliability pass

See `FINAL_POLISH_NOTES.md` for the final stability, correctness, resource, and UI polish changes. The latest offline verification reports all core checks passing; external Gemini/YouTube calls are not required for the offline test suite.
