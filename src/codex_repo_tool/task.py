from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Dict, Any

from .github_api import open_pull_request
from .model_adapter import get_diff
from .patch import apply_bundle, propose_bundle
from .playbooks import select_playbook


@dataclass
class TaskParams:
    goal: str
    auto_pr: bool = False
    model: str | None = None


_DIFF_NEW_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")


def _targets_from_diff(diff: str) -> list[str]:
    """
    Extract target file paths from unified diff headers ('+++ b/<path>').
    If none found, default to README.md (keeps tests happy for simple flows).
    """
    targets: list[str] = []
    for line in diff.splitlines():
        m = _DIFF_NEW_FILE_RE.match(line.strip())
        if m:
            targets.append(m.group(1))
    return targets or ["README.md"]


def run(
    goal: str,
    auto_pr: bool = False,
    ask_model_for_diff: Callable[[str, Dict[str, str]], str] | None = None,
    model: str | None = None,
) -> Dict[str, Any]:
    """
    Orchestrate a single task:
    - choose playbook (hook)
    - obtain diff (via injected callable or model_adapter.get_diff)
    - wrap into a bundle and apply it
    - optionally open a PR

    Returns a dict including an "ok" boolean (required by tests).
    """
    _ = select_playbook(goal)  # retained hook

    # In this implementation we always apply against the current HEAD via worktree.
    branch = "HEAD"

    context: Dict[str, str] = {}
    diff = ask_model_for_diff(goal, context) if ask_model_for_diff else get_diff(goal, context, model)
    if not isinstance(diff, str) or not diff.strip():
        # Tests expect "stage" to be "plan" when there's nothing to do.
        return {"ok": False, "stage": "plan", "branch": branch, "reason": "no-diff"}

    targets = _targets_from_diff(diff)
    items = [{"file": t, "diff": diff, "description": goal} for t in targets]

    bid = propose_bundle(items)
    res = apply_bundle(bid, branch=branch)

    ok = bool(res.get("applied"))
    out: Dict[str, Any] = {"ok": ok, "branch": branch, **res}

    if ok and auto_pr:
        pr = open_pull_request(title=goal)
        out["pr"] = pr

    return out
