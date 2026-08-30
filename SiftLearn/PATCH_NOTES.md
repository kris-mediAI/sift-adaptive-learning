# Sift test hardening patch

## Production fix
- `session.py`: `_validate_assessment` is an instance method. It uses `self.engine` and `self.learner`, so `@staticmethod` was invalid and caused either `TypeError` or `NameError` during assessment/completion.

## Test isolation
- Added `test_support.isolated_sift.isolated_orchestrator()`.
- Each test module gets its own temporary SQLite database.
- Multiple orchestrators inside the same module share that module's database, so restart/persistence tests still exercise real persistence.
- Production `SiftRepository()` / `SiftDatabase()` defaults are unchanged.
- Active-intervention protection is unchanged.
