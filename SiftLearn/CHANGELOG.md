# Sift Backend Hardening Bundle

This bundle is built **on top of the supplied ~13,070-line Sift source export**.
It does not redesign the backend architecture and does not include UI files.

## Included fixes

### P0 — correctness
- Dynamic task history is loaded before dynamic generation and passed into novelty validation.
- Persisted dynamic tasks carry enough metadata to restore an unfinished task after a process restart.
- Assessment responses have a dedicated schema/type/range validation boundary.
- Assessment concepts are constrained to the learner's registered subject graph.
- Correct assessments cannot carry misconception evidence.
- SQLite connections use a timeout, busy timeout, WAL mode, and normal synchronous mode.
- Dynamic task completion continues to update the exact persisted intervention rather than inserting a duplicate completion row.

### P1 — architecture
- `ai_engine.py` is now a compatibility facade over the canonical `ai.assessment` implementation instead of maintaining a second assessment prompt.
- `core/scoring.py` now contains the canonical score/mastery helpers and `knowledge_model.py` uses them without changing the existing 40% evidence update behavior.
- Subject support remains sourced from `core.subject_graphs.py`.
- The orchestrator keeps repository/session/content/resource responsibilities behind one application boundary.
- The orchestrator now exposes contextual resource recommendations through the existing `ResourceEngine`.

### P2 — learning quality
- Assessment normalization prevents malformed AI evidence from entering the learner model.
- Existing mastery, retention, prerequisite, strategy-effectiveness, misconception, and novelty logic is preserved rather than replaced.
- Dynamic task novelty now has access to persisted historical tasks across restarts.

### P3 — production hardening
- Gemini generation has bounded transient-error retries with exponential backoff and logging.
- Gemini model and retry settings can be configured through environment variables:
  - `GEMINI_MODEL`
  - `GEMINI_MAX_RETRIES`
  - `GEMINI_RETRY_BACKOFF`
- Assessment schema validation can be imported without initializing Gemini, which makes offline tooling safer.
- `verify_backend_hardening.py` provides credential-free smoke checks.

## Intentionally NOT changed

- UI files
- existing adaptive-engine algorithms
- existing retention formulas
- existing strategy-selection algorithm
- existing resource quality scoring rules
- database schema design
- Gemini fallback behavior (strict generation remains strict; no fake fallback content was added)

## Verification performed in this bundle

- Python compilation of the bundle: PASS
- Four subject registry check: PASS
- All subject graphs non-empty: PASS
- Score/mastery bounds: PASS
- Assessment consistency: PASS
- SQLite WAL setup: PASS

The offline verification does not call Gemini or YouTube. Run the project's full existing test suite in your own `.venv` before replacing production files.
