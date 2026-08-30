"""
Sift pytest isolation harness v2.

TEST INFRASTRUCTURE ONLY.
Production Sift code is not modified.
"""

from __future__ import annotations

import inspect
import json
import re
import shutil
import tempfile
from pathlib import Path

_TMP_ROOT = Path(tempfile.mkdtemp(prefix="sift_pytest_"))
_DB_BY_TEST_FILE = {}
_CONTENT_COUNTER = {}
_PATCHED = False


def _caller_test_file() -> Path:
    for frame in inspect.stack()[2:]:
        path = Path(frame.filename)
        name = path.name.lower()
        if name.startswith("test_") and path.suffix.lower() == ".py":
            return path.resolve()
    return Path("<unknown-test>").resolve()


def _db_path() -> Path:
    test_file = _caller_test_file()
    if test_file not in _DB_BY_TEST_FILE:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", test_file.stem)
        _DB_BY_TEST_FILE[test_file] = _TMP_ROOT / f"{safe}.db"
    return _DB_BY_TEST_FILE[test_file]


def _concept(prompt: str) -> str:
    p = str(prompt).lower()
    if "modulo operator" in p or "%" in p:
        return "modulo operator"
    if "call stack" in p:
        return "Call Stack"
    if "variable" in p:
        return "Variables"
    if "loop" in p:
        return "Loops"
    if "function" in p:
        return "Functions"
    return "Variables"


def _fake_assessment(prompt: str) -> str:
    concept = _concept(prompt)
    p = str(prompt).lower()

    if concept == "modulo operator":
        correct = (
            "remainder" in p
            or "17 % 5 is 2" in p
            or "leaving 2" in p
        )
        score = 90 if correct else 40
        misconception = "" if correct else "Confuses modulo with ordinary division."
    else:
        correct = True
        score = 80
        misconception = ""

    return json.dumps({
        "score": score,
        "correct": correct,
        "concept": concept,
        "mistake_type": "none" if correct else "conceptual",
        "misconception": misconception,
        "confidence": 80,
        "explanation": f"Deterministic test assessment for {concept}.",
        "next_concept": "",
    })


def _fake_teaching(prompt: str) -> str:
    concept = _concept(prompt)
    m = re.search(r"Teaching strategy:\s*([A-Za-z_]+)", str(prompt), re.I)
    strategy = m.group(1) if m else "worked_example"

    return json.dumps({
        "title": f"{concept} practice",
        "strategy": strategy,
        "concept": concept,
        "explanation": f"A concise deterministic explanation of {concept}.",
        "task": f"Apply {concept} to one small example and explain your reasoning.",
        "success_signal": f"The learner correctly demonstrates {concept}.",
    })


def _fake_task(prompt: str) -> str:
    concept = _concept(prompt)
    key = _caller_test_file()
    n = _CONTENT_COUNTER.get(key, 0) + 1
    _CONTENT_COUNTER[key] = n

    # Different wording/scenario on every call keeps this compatible
    # with the real novelty validator.
    total = 41 + n * 13
    divisor = 3 + (n % 7)

    if concept == "modulo operator":
        question = (
            f"Scenario {n}: A data pipeline receives {total} records "
            f"and places {divisor} records in each full batch. "
            f"What does Python expression {total} % {divisor} return, "
            f"and what does that remainder mean?"
        )
    else:
        question = (
            f"Scenario {n}: Explain how {concept} behaves in this "
            f"new learning situation and give one concrete example."
        )

    return json.dumps({
        "title": f"{concept} scenario {n}",
        "question": question,
        "context": f"Fresh deterministic scenario {n} for {concept}.",
        "hints": [],
        "success_signal": f"The learner correctly demonstrates {concept}.",
        "expected_answer_type": "explanation",
        "difficulty": "medium",
        "question_type": "short_answer",
    })


def _fake_generate(prompt: str) -> str:
    text = str(prompt)
    lower = text.lower()

    if "student answer" in lower or "assessment engine" in lower:
        return _fake_assessment(text)

    if "personalized teaching engine" in lower:
        return _fake_teaching(text)

    if "adaptive learning content generator" in lower:
        return _fake_task(text)

    return _fake_assessment(text)


def _install():
    global _PATCHED
    if _PATCHED:
        return

    # 1. Isolate every SiftOrchestrator() that a legacy script creates.
    # Accept the CURRENT constructor, including resource_engine.
    import core.orchestrator as orchestrator_module
    from core.repository import SiftRepository
    from database.db import SiftDatabase

    original_init = orchestrator_module.SiftOrchestrator.__init__

    def isolated_init(
        self,
        repository=None,
        content_engine=None,
        gemini_provider=None,
        resource_engine=None,
        **kwargs,
    ):
        if repository is None:
            db = SiftDatabase(db_path=str(_db_path()))
            repository = SiftRepository(database=db)

        return original_init(
            self,
            repository=repository,
            content_engine=content_engine,
            gemini_provider=gemini_provider,
            resource_engine=resource_engine,
            **kwargs,
        )

    orchestrator_module.SiftOrchestrator.__init__ = isolated_init

    # 2. Mock ONLY the model's generate method for pytest.
    # The real ContentEngine, strict validation, novelty checking,
    # orchestration, persistence and adaptive logic remain active.
    from core.llm.gemini_provider import GeminiProvider
    GeminiProvider.generate = lambda self, prompt: _fake_generate(prompt)

    # Also patch already-imported direct aliases, where present.
    try:
        import ai.gemini as gemini_module
        gemini_module.generate = _fake_generate
    except Exception:
        pass

    try:
        import ai.assessment as assessment_module
        assessment_module.generate = _fake_generate
    except Exception:
        pass

    try:
        import ai.teaching as teaching_module
        teaching_module.generate = _fake_generate
    except Exception:
        pass

    _PATCHED = True


_install()


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(_TMP_ROOT, ignore_errors=True)
