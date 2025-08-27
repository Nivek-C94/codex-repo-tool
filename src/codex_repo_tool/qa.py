from __future__ import annotations
import json
import subprocess
from pathlib import Path

def _run(cmd: list[str]) -> dict:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return {"ok": p.returncode == 0, "stdout": p.stdout, "stderr": p.stderr, "code": p.returncode}

def run_tests(scope: str | None = None) -> dict:
    """
    Detects Python pytest or Node npm test and runs it.
    """
    if Path("pytest.ini").exists() or Path("pyproject.toml").exists() or Path("tests").exists():
        return _run(["pytest", "-q"] if scope is None else ["pytest", "-q", scope])
    if Path("package.json").exists():
        if scope:
            return _run(["npm", "run", "test", "--", scope])
        return _run(["npm", "test"])
    return {"ok": True, "stdout": "No test framework detected; skipping.", "stderr": "", "code": 0}

def lint_code(scope: str | None = None) -> dict:
    """
    Detects Python (ruff+black --check) or Node (eslint) linters.
    """
    if Path("pyproject.toml").exists() or Path("src").exists():
        r1 = _run(["ruff", "src", "tests"])
        if not r1["ok"]:
            return r1
        r2 = _run(["black", "--check", "src", "tests"])
        return r2
    if Path("package.json").exists():
        return _run(["npm", "run", "lint"] if scope is None else ["npm", "run", "lint", "--", scope])
    return {"ok": True, "stdout": "No linter detected; skipping.", "stderr": "", "code": 0}

def static_analysis(scope: str | None = None, mode: str = "style") -> dict:
    """
    Placeholder for security/style analyzers; returns success by default.
    """
    return {"ok": True, "stdout": f"Static analysis ({mode}) skipped in MVP.", "stderr": "", "code": 0}
