# Sift Backend — Compatibility Fixes

These are ONLY the three compatibility fixes found by the full pytest run.

1. `core/session.py`
   - Fixed `_validate_assessment()`'s accidental `@staticmethod` signature mismatch.
   - Existing callers using `self._validate_assessment(assessment)` now work.

2. `core/learning_record.py`
   - Keeps `core.learner_model.LearningRecord` as the canonical implementation.
   - Adds a compatibility facade so older callers may omit `learning_gain`.
   - No duplicate persistence model or second independent implementation is introduced.

3. `core/content_engine.py`
   - Restores the existing safe fallback as the default for direct/offline ContentEngine use.
   - Production orchestration can still explicitly use `allow_fallback=False`.

UI files are intentionally not included.
