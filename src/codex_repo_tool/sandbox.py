from __future__ import annotations
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

@dataclass
class SandboxResult:
    ok: bool
    stdout: str
    stderr: str
    code: int

def _run(cmd: list[str], cwd: str | None = None) -> SandboxResult:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return SandboxResult(ok=p.returncode == 0, stdout=p.stdout, stderr=p.stderr, code=p.returncode)

def with_worktree(branch: str, apply_callable):
    git_root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if git_root.returncode != 0:
        return False, {"error": "Not a git repository"}
    root = Path(git_root.stdout.strip())
    tmpdir = Path(tempfile.mkdtemp(prefix="codexrt-"))
    worktree_path = tmpdir / "wt"
    try:
        add = _run(["git", "worktree", "add", "--detach", str(worktree_path), branch], cwd=str(root))
        if not add.ok:
            return False, {"stage": "worktree-add", "stdout": add.stdout, "stderr": add.stderr}
        data = apply_callable(str(worktree_path))
        return True, data
    finally:
        _run(["git", "worktree", "remove", "--force", str(worktree_path)], cwd=str(root))
        shutil.rmtree(tmpdir, ignore_errors=True)
