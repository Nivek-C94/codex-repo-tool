from __future__ import annotations

import json
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
    tmp = _tmpdir()
    patch_id = f"patch_{uuid.uuid4().hex[:8]}"
    path = tmp / f"{patch_id}.json"
    data = {"file": file, "diff": diff, "description": description}
    path.write_text(json.dumps(data), encoding="utf-8")
    return patch_id


def apply_patch(patch_id: str, branch: str = "HEAD") -> dict[str, Any]:
    tmp = _tmpdir()
    path = tmp / f"{patch_id}.json"
    info = json.loads(path.read_text(encoding="utf-8"))

    diff_path = tmp / "apply.patch"
    diff_path.write_text(info["diff"], encoding="utf-8")

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
    path = _tmpdir() / f"{patch_id}.json"
    if path.exists():
        try:
            path.unlink()
            return True
        except Exception:
            return False
    return False


def propose_bundle(items: list[dict[str, Any]]) -> str:
    tmp = _tmpdir()
    bid = tmp / "bundle.json"
    bid.parent.mkdir(parents=True, exist_ok=True)
    bid.write_text(json.dumps({"items": items}), encoding="utf-8")
    return str(bid)


def apply_bundle(bundle_id: str, branch: str = "HEAD") -> dict[str, Any]:
    bundle = json.loads(Path(bundle_id).read_text(encoding="utf-8"))
    policy = load_policy()

    for item in bundle.get("items", []):
        if policy.is_path_protected(item.get("file", "")):
            return {
                "applied": False,
                "stage": "policy",
                "error": f"Protected path: {item.get('file', '')}",
            }

    def _apply_in_wt(wt: str) -> dict[str, Any]:
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

        lint_required = policy.require_checks.get("lint", True)
        tests_required = policy.require_checks.get("tests", True)

        lint: dict[str, Any] = {"ok": True}
        tests: dict[str, Any] = {"ok": True}
        if lint_required:
            lint = lint_code()
        if tests_required:
            tests = run_tests()

        lint_ok = lint.get("ok", False) if lint_required else True
        tests_ok = tests.get("ok", False) if tests_required else True

        if (lint_required and not lint_ok) or (tests_required and not tests_ok):
            return {
                "applied": False,
                "stage": "qa",
                "lint": lint,
                "tests": tests,
            }

        return {
            "applied": True,
            "stage": "done",
            "lint": lint,
            "tests": tests,
        }

    ok, res = with_worktree(branch, _apply_in_wt)
    if not ok:
        return {"applied": False, **res}
    return res
