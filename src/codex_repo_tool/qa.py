from __future__ import annotations

import subprocess
from pathlib import Path

from .docker_sandbox import docker_available


def _run(cmd: list[str]) -> dict:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return {"ok": p.returncode == 0, "stdout": p.stdout, "stderr": p.stderr, "code": p.returncode}


def _docker_enabled() -> bool:
    return docker_available()


def _run_in_docker(cmd: list[str]) -> dict:
    return _run(cmd)


def run_tests(scope: str | None = None) -> dict:
    if Path("package.json").exists():
        if _docker_enabled():
            return _run_in_docker(["npm", "test"] if scope is None else ["npm", "test", scope])
        return _run(["npm", "test"] if scope is None else ["npm", "test", scope])
    if Path("pyproject.toml").exists() or Path("pytest.ini").exists():
        return _run(["pytest", "-q"] if scope is None else ["pytest", "-q", scope])
    return {"ok": True, "stdout": "No tests detected; skipping.", "stderr": "", "code": 0}


def lint_code(scope: str | None = None) -> dict:
    if Path("pyproject.toml").exists() or Path("ruff.toml").exists():
        if _docker_enabled():
            return _run_in_docker(["ruff", "check", "--fix", "."])
        return _run(["ruff", "check", "--fix", "."])
    if Path("package.json").exists():
        if _docker_enabled():
            return _run_in_docker(
                ["npm", "run", "lint"] if scope is None else ["npm", "run", "lint", "--", scope]
            )
        return _run(
            ["npm", "run", "lint"] if scope is None else ["npm", "run", "lint", "--", scope]
        )
    return {"ok": True, "stdout": "No linter detected; skipping.", "stderr": "", "code": 0}


def static_analysis(mode: str = "fast") -> dict:
    """Placeholder for security/style analyzers; returns success by default."""
    return {
        "ok": True,
        "stdout": f"Static analysis ({mode}) skipped in MVP.",
        "stderr": "",
        "code": 0,
    }
