from __future__ import annotations


def select_playbook(goal: str) -> str:
    g = goal.lower()
    if any(k in g for k in ["fix", "bug", "exception", "error", "failing test", "flake"]):
        return "bugfix"
    if any(k in g for k in ["test", "coverage", "unit test", "pytest", "jest"]):
        return "add-tests"
    if any(k in g for k in ["refactor", "cleanup", "rename", "restructure"]):
        return "refactor"
    if any(k in g for k in ["upgrade", "bump", "migrate"]):
        return "upgrade-dep"
    # default
    return "general"
