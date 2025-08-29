from __future__ import annotations
import json
import subprocess
from pathlib import Path
from .docker_sandbox import docker_available
def _run(cmd: list[str]) -> dict:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return {"ok": p.returncode == 0, "stdout": p.stdout, "stderr": p.stderr, "code": p.returncode}

def run_tests(scope: str | None = None) -> dict:
    """
    Detects Python pytest or Node npm test and runs it.
    """
    if Path("pytest.ini").exists() or Path("pyproject.toml").exists() or Path("tests").exists():
        if _docker_enabled():
            return _run_in_docker(["pytest", "-q"] if scope is None else ["pytest", "-q", scope])
        return _run(["pytest", "-q"] if scope is None else ["pytest", "-q", scope])
    if Path("package.json").exists():
        if _docker_enabled():
            if scope:
                return _run_in_docker(["npm", "run", "test", "--", scope])
            return _run_in_docker(["npm", "test"])
        if scope:
            return _run(["npm", "run", "test", "--", scope])
        return _run(["npm", "test"])
    return {"ok": True, "stdout": "No test framework detected; skipping.", "stderr": "", "code": 0}

def lint_code(scope: str | None = None) -> dict:
    """
    Detects Python (ruff+black --check) or Node (eslint) linters.
    """
    if Path("pyproject.toml").exists() or Path("src").exists():
        if _docker_enabled():
            r1 = _run_in_docker(["ruff", "src", "tests"])
        else:
            r1 = _run(["ruff", "src", "tests"])
        if not r1["ok"]:
            return r1
        r2 = _run(["black", "--check", "src", "tests"])
        return r2
    if Path("package.json").exists():
        if _docker_enabled():
            return _run_in_docker(["npm", "run", "lint"] if scope is None else ["npm", "run", "lint", "--", scope])
        return _run(["npm", "run", "lint"] if scope is None else ["npm", "run", "lint", "--", scope])
    return {"ok": True, "stdout": "No linter detected; skipping.", "stderr": "", "code": 0}

def static_analysis(scope: str | None = None, mode: str = "style") -> dict:
    """
    Placeholder for security/style analyzers; returns success by default.
    """
    return {"ok": True, "stdout": f"Static analysis ({mode}) skipped in MVP.", "stderr": "", "code": 0}


def _docker_enabled() -> bool:
    # Enable Docker checks if docker is installed AND repo has Dockerfile or .codexrt/docker.yml
    if not docker_available():
        return False
    if Path("Dockerfile").exists() or (Path(".codexrt") / "docker.yml").exists():
        return True
    return False

def _run_in_docker(cmd: list[str]) -> dict:
    """
    Build ephemeral image and run the command inside it, mounting the repo at /app.
    This is a minimal approach; customize as needed in docker.yml.
    """
    # Build
    import subprocess, uuid, shlex
    tag = f"codexrt:{uuid.uuid4().hex[:8]}"
    build = subprocess.run(["docker", "build", "-t", tag, "."], capture_output=True, text=True)
    if build.returncode != 0:
        return {"ok": False, "stdout": build.stdout, "stderr": build.stderr, "code": build.returncode}
    # Run
    run = subprocess.run(["docker", "run", "--rm", "-v", f"{Path('.').resolve()}:/app", "-w", "/app", tag] + cmd,
                         capture_output=True, text=True)
    return {"ok": run.returncode == 0, "stdout": run.stdout, "stderr": run.stderr, "code": run.returncode}
