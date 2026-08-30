"""Isolate each test module's SQLite state without changing production defaults."""

from __future__ import annotations

import hashlib
import inspect
import tempfile
from pathlib import Path

from core.orchestrator import SiftOrchestrator
from core.repository import SiftRepository
from database.db import SiftDatabase


_ROOT = Path(tempfile.mkdtemp(prefix="sift-tests-"))
_DATABASES: dict[str, Path] = {}


def _caller_key() -> str:
    for frame in inspect.stack()[2:]:
        filename = Path(frame.filename).resolve()
        if filename.parent != Path(__file__).resolve().parent:
            return str(filename)
    return "unknown-test"


def _database_path() -> Path:
    key = _caller_key()
    path = _DATABASES.get(key)
    if path is None:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        path = _ROOT / f"{digest}.db"
        _DATABASES[key] = path
    return path


def isolated_database():
    """Return the SQLite database isolated to the caller test module."""
    return SiftDatabase(db_path=str(_database_path()))


def isolated_repository():
    """Return a repository backed by the caller module's isolated database."""
    return SiftRepository(database=isolated_database())


def isolated_orchestrator(*, content_engine=None, gemini_provider=None, resource_engine=None):
    """Return an orchestrator backed by a database unique to the caller module.

    Multiple orchestrators created by the same test module share its isolated
    database, which preserves restart/persistence tests while preventing one
    test module from contaminating another.
    """
    repository = isolated_repository()
    return SiftOrchestrator(
        repository=repository,
        content_engine=content_engine,
        gemini_provider=gemini_provider,
        resource_engine=resource_engine,
    )
