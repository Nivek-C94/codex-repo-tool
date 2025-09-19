from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable

from .docker_sandbox import docker_available


def _run(cmd: Iterable[str]) -> dict[str, object]:
    p = subprocess.run(list(cmd), capture_output=True, text=True)
    return {"ok": p.returncode == 0, "stdout": p.stdout, "stderr": p.stderr, "code": p.returncode}


def _docker_enabled() -> bool:
    return docker_available()


def _run_in_docker(cmd: Iterable[str]) -> dict[str, object]:
    return _run(cmd)


def run_tests(scope: str | None = None) -> dict[str, object]:
    if Path("package.json").exists():
        base_cmd = ["npm", "test"]
        if scope is not None:
            base_cmd.append(scope)
        if _docker_enabled():
            return _run_in_docker(base_cmd)
        return _run(base_cmd)
    if Path("pyproject.toml").exists() or Path("pytest.ini").exists():
        base_cmd = ["pytest", "-q"]
        if scope is not None:
            base_cmd.append(scope)
        return _run(base_cmd)
    return {"ok": True, "stdout": "No tests detected; skipping.", "stderr": "", "code": 0}


def lint_code(scope: str | None = None) -> dict[str, object]:
    if Path("pyproject.toml").exists() or Path("ruff.toml").exists():
        base_cmd = ["ruff", "check", "--fix", "."]
        if _docker_enabled():
            return _run_in_docker(base_cmd)
        return _run(base_cmd)
    if Path("package.json").exists():
        base_cmd = ["npm", "run", "lint"]
        if scope is not None:
            base_cmd.extend(["--", scope])
        if _docker_enabled():
            return _run_in_docker(base_cmd)
        return _run(base_cmd)
    return {"ok": True, "stdout": "No linter detected; skipping.", "stderr": "", "code": 0}


def static_analysis(mode: str = "fast") -> dict[str, object]:
    return {
        "ok": True,
        "stdout": f"Static analysis ({mode}) skipped in MVP.",
        "stderr": "",
        "code": 0,
    }
