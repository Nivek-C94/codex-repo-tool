from __future__ import annotations

from typing import Iterable, Sequence


PLAYBOOK_KEYWORDS: Sequence[tuple[str, Sequence[str]]] = (
    (
        "security",
        (
            "security",
            "vulnerab",
            "cve",
            "xss",
            "csrf",
            "injection",
            "leak",
        ),
    ),
    (
        "bugfix",
        ("fix", "bug", "exception", "error", "failing test", "flake"),
    ),
    (
        "add-tests",
        ("test", "coverage", "unit test", "pytest", "jest"),
    ),
    (
        "refactor",
        ("refactor", "cleanup", "rename", "restructure"),
    ),
    (
        "upgrade-dep",
        ("upgrade", "bump", "migrate"),
    ),
    (
        "docs",
        (
            "docs",
            "documentation",
            "readme",
            "guide",
            "tutorial",
            "changelog",
        ),
    ),
    (
        "performance",
        (
            "performance",
            "optimiz",
            "speed",
            "slow",
            "latency",
            "throughput",
            "efficien",
            "scalab",
        ),
    ),
)


def _matches(goal: str, keywords: Iterable[str]) -> bool:
    return any(keyword in goal for keyword in keywords)


def select_playbook(goal: str) -> str:
    g = goal.lower()
    for playbook, keywords in PLAYBOOK_KEYWORDS:
        if _matches(g, keywords):
            return playbook
    return "general"
