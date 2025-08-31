from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CmdResult:
    ok: bool
    stdout: str
    stderr: str


def _run(cmd: list[str], cwd: str | None = None) -> CmdResult:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return CmdResult(p.returncode == 0, p.stdout, p.stderr)


def with_worktree(branch: str, apply_callable):
    git_root = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
    )
    if git_root.returncode != 0:
        return False, {"error": "Not a git repository"}
    root = Path(git_root.stdout.strip())

    tmpdir = Path(tempfile.mkdtemp(prefix="codexrt-wt-"))
    worktree_path = tmpdir / "wt"
    try:
        add = _run(["git", "worktree", "add", "--detach", str(worktree_path), branch], cwd=str(root))
        if not add.ok:
            return False, {"stage": "worktree-add", "stdout": add.stdout, "stderr": add.stderr}
        ok, res = True, apply_callable(str(worktree_path))
        return ok, res
    finally:
        try:
            _run(["git", "worktree", "remove", "--force", str(worktree_path)], cwd=str(root))
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
