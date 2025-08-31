from __future__ import annotations

import re
import subprocess
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .github_api import open_pull_request
from .model_adapter import get_diff
from .patch import apply_bundle, propose_bundle
from .playbooks import select_playbook
from .semantic import build_index, save_repo_map


@dataclass
class TaskParams:
    goal: str
    hints: list[str]
    dry_run: bool
    auto_pr: bool
    branch: str
    pr_title: str
    pr_body: str
    max_files: int
    time_budget_sec: int
    strict_checks: bool
    ask_model_for_diff: Callable[[str, dict[str, str]], str] | None


def _slug(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.strip().lower())
    return s[:50] if len(s) > 50 else s


def _discover(hints: list[str], max_files: int) -> list[str]:
    touched: list[str] = []
    for h in hints:
        p = Path(h)
        if p.is_file():
            touched.append(str(p))
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    touched.append(str(f))
    return touched[:max_files]


def _collect_context(files: list[str], lines_each: int = 120) -> dict[str, str]:
    ctx: dict[str, str] = {}
    for f in files:
        try:
            text = Path(f).read_text(encoding="utf-8", errors="ignore")
            head = "\n".join(text.splitlines()[:lines_each])
            ctx[f] = head
        except Exception:
            continue
    return ctx


def default_model_prompt(goal: str, context: dict[str, str]) -> str:
    return ""


def run(
    goal: str,
    hints: list[str] | None = None,
    dry_run: bool = False,
    auto_pr: bool = True,
    branch: str | None = None,
    pr_title: str = "",
    pr_body: str = "",
    max_files: int = 50,
    time_budget_sec: int = 600,
    strict_checks: bool = True,
    ask_model_for_diff: Callable[[str, dict[str, str]], str] | None = None,
) -> dict[str, Any]:
    start = time.time()
    params = TaskParams(
        goal=goal,
        hints=hints or [],
        dry_run=dry_run,
        auto_pr=auto_pr,
        branch=branch or f"codexrt/auto/{_slug(goal)}",
        pr_title=pr_title or f"chore: {goal}",
        pr_body=pr_body,
        max_files=max_files,
        time_budget_sec=time_budget_sec,
        strict_checks=strict_checks,
        ask_model_for_diff=ask_model_for_diff,
    )

    files = _discover(params.hints, params.max_files)
    context = _collect_context(files)
    playbook = select_playbook(params.goal)
    prompt = f"[{playbook}] {params.goal}"
    diff = (
        params.ask_model_for_diff(prompt, context)
        if params.ask_model_for_diff
        else get_diff(prompt, context)
    )
    if not diff.strip():
        return {"ok": False, "stage": "plan", "error": "No diff generated for goal."}

    items: list[dict[str, str]] = []
    current: list[str] = []
    current_file = None

    def flush_current():
        nonlocal current, current_file, items
        if current and current_file:
            items.append(
                {
                    "file": current_file,
                    "diff": "".join(current),
                    "description": params.goal,
                }
            )
            current = []
            current_file = None

    for line in diff.splitlines(keepends=True):
        if line.startswith("--- "):
            flush_current()
            current_file = line.split()[1][2:]  # strip 'a/'
            current = [line]
        else:
            current.append(line)
    flush_current()

    if not items:
        return {"ok": False, "stage": "plan", "error": "Parsed diff had no items."}

    # Propose and apply
    bid = propose_bundle(items)
    ok, res = apply_bundle(bid, branch=params.branch)
    if not ok:
        return res

    if params.dry_run:
        return {
            "ok": True,
            "branch": params.branch,
            "dry_run": True,
            "summary": "Validated in sandbox",
            **res,
        }

    # Create branch
    subprocess.run(["git", "checkout", "-b", params.branch], check=False)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".patch") as tmp:
        tmp.write(diff.encode())
        tmp.flush()
        apply2 = subprocess.run(
            ["git", "apply", str(tmp)], capture_output=True, text=True
        )
        if apply2.returncode != 0:
            return {
                "ok": False,
                "stage": "apply-working",
                "stderr": apply2.stderr,
                "stdout": apply2.stdout,
            }

    commit_msg = params.pr_title or f"chore: {params.goal}"
    commit = subprocess.run(
        ["git", "commit", "-am", commit_msg], capture_output=True, text=True
    )
    if commit.returncode != 0:
        return {
            "ok": False,
            "stage": "commit",
            "stderr": commit.stderr,
            "stdout": commit.stdout,
        }

    push = subprocess.run(
        ["git", "push", "-u", "origin", params.branch],
        capture_output=True,
        text=True,
    )
    if push.returncode != 0:
        return {
            "ok": False,
            "stage": "push",
            "stderr": push.stderr,
            "stdout": push.stdout,
        }

    pr_info = None
    if params.auto_pr:
        pr_info = open_pull_request(
            params.branch, params.pr_title, params.pr_body or params.goal
        )

    elapsed = time.time() - start
    return {
        "ok": True,
        "branch": params.branch,
        "pr": pr_info,
        "elapsed_sec": round(elapsed, 2),
        "diff_items": len(items),
    }
