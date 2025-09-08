from __future__ import annotations

import json
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from .config import SETTINGS
from .policy import load_policy
from .qa import lint_code, run_tests
from .sandbox import with_worktree


@dataclass
class Patch:
    file: str
    diff: str
    description: str = ""


def _tmpdir() -> Path:
    p = Path(SETTINGS.tmp_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def propose_patch(file: str, diff: str, description: str = "") -> str:
    """
    Create a uniquely-named patch JSON under tmp_dir and return its ID (string)
    like 'patch_<id>'. Tests expect the returned value to start with 'patch_'.
    """
    tmp = _tmpdir()
    patch_id = f"patch_{uuid.uuid4().hex[:8]}"
    path = tmp / f"{patch_id}.json"
    data = {"file": file, "diff": diff, "description": description}
    path.write_text(json.dumps(data), encoding="utf-8")
    return patch_id


def apply_patch(patch_id: str, branch: str = "HEAD") -> dict:
    """
    Read the patch JSON by ID and attempt to apply it (dry-run validate).
    """
    tmp = _tmpdir()
    path = tmp / f"{patch_id}.json"
    info = json.loads(path.read_text(encoding="utf-8"))

    diff_path = tmp / "apply.patch"
    diff_path.write_text(info["diff"], encoding="utf-8")

    # Dry-run apply to validate
    dry = subprocess.run(
        ["git", "apply", "--check", str(diff_path)],
        capture_output=True,
        text=True,
    )
    if dry.returncode != 0:
        return {
            "applied": False,
            "stage": "dry-run",
            "stdout": dry.stdout,
            "stderr": dry.stderr,
        }
    return {"applied": True, "stage": "done"}


def discard_patch(patch_id: str) -> bool:
    """
    Remove the patch file created by `propose_patch`.
    Tests expect True on success.
    """
    path = _tmpdir() / f"{patch_id}.json"
    if path.exists():
        try:
            path.unlink()
            return True
        except Exception:
            return False
    return False


def propose_bundle(items: list[dict]) -> str:
    """
    Store a bundle file under tmp_dir and return its full path (str).
    """
    tmp = _tmpdir()
    bid = tmp / "bundle.json"
    bid.parent.mkdir(parents=True, exist_ok=True)
    bid.write_text(json.dumps({"items": items}), encoding="utf-8")
    return str(bid)


def apply_bundle(bundle_id: str, branch: str = "HEAD") -> dict:
    bundle = json.loads(Path(bundle_id).read_text(encoding="utf-8"))
    policy = load_policy()

    def _apply_in_wt(wt: str) -> dict:
        from pathlib import Path

        wt_path = Path(wt)
        for i, item in enumerate(bundle.get("items", []), start=1):
            diff_file = wt_path / f"diff_{i}.patch"
            diff_file.parent.mkdir(parents=True, exist_ok=True)
            diff_file.write_text(item["diff"], encoding="utf-8")
            dry = subprocess.run(
                ["git", "apply", "--check", str(diff_file)],
                cwd=wt,
                capture_output=True,
                text=True,
            )
            if dry.returncode != 0:
                return {
                    "applied": False,
                    "stage": "dry-run",
                    "stdout": dry.stdout,
                    "stderr": dry.stderr,
                }
            apply = subprocess.run(
                ["git", "apply", str(diff_file)],
                cwd=wt,
                capture_output=True,
                text=True,
            )
            if apply.returncode != 0:
                return {
                    "applied": False,
                    "stage": "apply",
                    "stdout": apply.stdout,
                    "stderr": apply.stderr,
                }

        lint_ok = True
        tests_ok = True
        if policy.require_checks.get("lint", True):
            lint = lint_code()
            lint_ok = lint.get("ok", False)
        if policy.require_checks.get("tests", True):
            tests = run_tests()
            tests_ok = tests.get("ok", False)

        if (policy.require_checks.get("lint", True) and not lint_ok) or (
            policy.require_checks.get("tests", True) and not tests_ok
        ):
            return {
                "applied": False,
                "stage": "qa",
                "lint_ok": lint_ok,
                "tests_ok": tests_ok,
            }

        return {
            "applied": True,
            "stage": "done",
            "lint_ok": lint_ok,
            "tests_ok": tests_ok,
        }

    ok, res = with_worktree(branch, _apply_in_wt)
    if not ok:
        return {"applied": False, **res}
    return res
