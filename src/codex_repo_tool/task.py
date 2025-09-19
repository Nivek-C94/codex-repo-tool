from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .github_api import open_pull_request
from .model_adapter import get_diff
from .patch import apply_bundle, propose_bundle
from .playbooks import select_playbook


@dataclass
class TaskContext:
    files: dict[str, str]


_DIFF_NEW_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")
_MAX_HINT_BYTES = 16_000


def _targets_from_diff(diff: str) -> list[str]:
    targets: list[str] = []
    for line in diff.splitlines():
        m = _DIFF_NEW_FILE_RE.match(line.strip())
        if m:
            targets.append(m.group(1))
    return targets or ["README.md"]


def _gather_context(hints: list[str]) -> TaskContext:
    context: dict[str, str] = {}
    for hint in hints:
        path = Path(hint)
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        context[str(path)] = text[:_MAX_HINT_BYTES]
    return TaskContext(files=context)


def run(
    goal: str,
    auto_pr: bool = False,
    ask_model_for_diff: Callable[[str, dict[str, str]], str] | None = None,
    model: str | None = None,
    *,
    hints: list[str] | None = None,
    dry_run: bool = False,
    branch: str | None = None,
    pr_title: str | None = None,
    pr_body: str | None = None,
    max_files: int = 50,
    time_budget_sec: int = 600,  # noqa: ARG001 - reserved for future scheduling
    strict_checks: bool = False,  # noqa: ARG001 - retained for compatibility
) -> dict[str, Any]:
    playbook = select_playbook(goal)

    branch = branch or "HEAD"
    hints = hints or []

    ctx = _gather_context(hints)
    context_payload = ctx.files

    diff = (
        ask_model_for_diff(goal, context_payload) if ask_model_for_diff else get_diff(goal, context_payload, model)
    )
    if not isinstance(diff, str) or not diff.strip():
        return {"ok": False, "stage": "plan", "branch": branch, "reason": "no-diff", "playbook": playbook}

    targets = _targets_from_diff(diff)
    if len(targets) > max_files:
        return {
            "ok": False,
            "stage": "plan",
            "branch": branch,
            "reason": "too-many-files",
            "targets": targets,
            "playbook": playbook,
        }

    if dry_run:
        return {
            "ok": True,
            "stage": "dry-run",
            "branch": branch,
            "diff": diff,
            "targets": targets,
            "context_files": list(context_payload.keys()),
            "playbook": playbook,
        }

    items = [{"file": t, "diff": diff, "description": goal} for t in targets]

    bid = propose_bundle(items)
    res = apply_bundle(bid, branch=branch)

    ok = bool(res.get("applied"))
    out: dict[str, Any] = {"ok": ok, "branch": branch, "playbook": playbook, **res}
    out["targets"] = targets
    out["context_files"] = list(context_payload.keys())

    if ok and auto_pr:
        title = pr_title or goal
        body = pr_body or goal
        pr = open_pull_request(branch, title, body)
        out["pr"] = pr

    return out
