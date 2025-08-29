from __future__ import annotations
import json, re, subprocess, time, tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .semantic import build_index, save_repo_map
from .patch import propose_bundle, apply_bundle
from .model_adapter import get_diff
from .playbooks import select_playbook
from .github_api import open_pull_request

@dataclass
class TaskParams:
    goal: str
    hints: List[str]
    dry_run: bool
    auto_pr: bool
    branch: str
    pr_title: str
    pr_body: str
    max_files: int
    time_budget_sec: int
    strict_checks: bool

def _slug(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip()).strip("-").lower()
    return s[:50] if len(s) > 50 else s

def _discover(hints: List[str], max_files: int) -> List[str]:
    touched: List[str] = []
    for h in hints:
        p = Path(h)
        if p.is_file():
            touched.append(str(p))
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    touched.append(str(f))
        if len(touched) >= max_files:
            return touched[:max_files]
    return touched[:max_files]

def _collect_context(files: List[str], lines_each: int = 120) -> Dict[str, str]:
    ctx: Dict[str, str] = {}
    for f in files:
        try:
            data = Path(f).read_text(encoding="utf-8", errors="ignore")
            ctx[f] = "\n".join(data.splitlines()[:lines_each])
        except Exception:
            continue
    return ctx

def default_model_prompt(goal: str, context: Dict[str, str]) -> str:
    return ""

def run(
    goal: str,
    hints: Optional[List[str]] = None,
    dry_run: bool = False,
    auto_pr: bool = True,
    branch: Optional[str] = None,
    pr_title: str = "",
    pr_body: str = "",
    max_files: int = 50,
    time_budget_sec: int = 600,
    strict_checks: bool = True,
    ask_model_for_diff: Optional[Callable[[str, Dict[str, str]], str]] = None,
) -> Dict[str, Any]:
    start = time.time()
    params = TaskParams(
        goal=goal,
        hints=hints or [],
        dry_run=dry_run,
        auto_pr=auto_pr,
        branch=branch or f"codexrt/auto/{_slug(goal) or 'task'}",
        pr_title=pr_title,
        pr_body=pr_body,
        max_files=max_files,
        time_budget_sec=time_budget_sec,
        strict_checks=strict_checks,
    )

    idx = build_index(".")
    save_repo_map(idx, ".")

    files = _discover(params.hints, params.max_files)
    context = _collect_context(files)

    playbook = select_playbook(params.goal)
    asker = ask_model_for_diff or (lambda g,c: get_diff(f"[{playbook}] "+g, c))
    diff = asker(params.goal, context)
    if not isinstance(diff, str) or not diff.strip():
        return {"ok": False, "stage": "plan", "error": "No diff generated for goal."}

    items: List[Dict[str, str]] = []
    current: List[str] = []
    current_file = None

    def flush_current():
        nonlocal current, current_file, items
        if current and current_file:
            items.append({"file": current_file, "diff": "".join(current), "description": params.goal})
        current = []
        current_file = None

    for line in diff.splitlines(keepends=True):
        if line.startswith("--- ") and "a/" in line:
            if current:
                flush_current()
            current = [line]
            current_file = None
        elif line.startswith("+++ ") and "b/" in line:
            current.append(line)
            try:
                path = line.split("b/", 1)[1].strip()
                current_file = path
            except Exception:
                pass
        else:
            current.append(line)
    flush_current()

    if not items:
        items = [{"file": "UNKNOWN", "diff": diff, "description": params.goal}]

    bid = propose_bundle(items, description=params.goal)
    res = apply_bundle(bid, branch="HEAD")
    if not res.get("applied"):
        res.update({"ok": False})
        return res

    if params.dry_run:
        return {"ok": True, "branch": params.branch, "dry_run": True, "summary": "Validated in sandbox", **res}

    # Create branch
    sub = subprocess.run(["git", "checkout", "-b", params.branch], capture_output=True, text=True)
    if sub.returncode != 0:
        return {"ok": False, "stage": "branch", "stderr": sub.stderr, "stdout": sub.stdout}

    combined = "\n".join(it["diff"] for it in items)
    tmp = Path(tempfile.gettempdir()) / f"codexrt_apply_{int(time.time())}.diff"
    tmp.write_text(combined, encoding="utf-8")
    apply2 = subprocess.run(["git", "apply", str(tmp)], capture_output=True, text=True)
    if apply2.returncode != 0:
        return {"ok": False, "stage": "apply-working", "stderr": apply2.stderr, "stdout": apply2.stdout}

    commit_msg = params.pr_title or f"chore: {params.goal}"
    add = subprocess.run(["git", "add", "-A"], capture_output=True, text=True)
    if add.returncode != 0:
        return {"ok": False, "stage": "stage", "stderr": add.stderr, "stdout": add.stdout}
    commit = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
    if commit.returncode != 0:
        return {"ok": False, "stage": "commit", "stderr": commit.stderr, "stdout": commit.stdout}

    push = subprocess.run(["git", "push", "-u", "origin", params.branch], capture_output=True, text=True)
    if push.returncode != 0:
        return {"ok": False, "stage": "push", "stderr": push.stderr, "stdout": push.stdout}

    pr_info = None
    if params.auto_pr:
        title = params.pr_title or commit_msg
        body = params.pr_body or f"Automated by CodexRepoTool task.run\n\nGoal: {params.goal}"
        pr_info = open_pull_request(params.branch, title, body)

    elapsed = time.time() - start
    return {"ok": True, "branch": params.branch, "pr": pr_info, "elapsed_sec": round(elapsed, 2), "diff_items": len(items)}
