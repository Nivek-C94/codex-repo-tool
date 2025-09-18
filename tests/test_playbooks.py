from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_playbooks_module():
    module_path = Path(__file__).resolve().parent.parent / "src" / "codex_repo_tool" / "playbooks.py"
    spec = importlib.util.spec_from_file_location("codex_repo_tool.playbooks", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load playbooks module for testing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


select_playbook = _load_playbooks_module().select_playbook


@pytest.mark.parametrize(
    ("goal", "expected"),
    [
        ("Fix security vulnerability in auth flow", "security"),
        ("Update documentation for the API", "docs"),
        ("Optimize query performance for large datasets", "performance"),
        ("Refactor helper module names", "refactor"),
        ("Add missing pytest cases", "add-tests"),
        ("Upgrade dependency versions", "upgrade-dep"),
        ("Explore new idea", "general"),
    ],
)
def test_select_playbook(goal: str, expected: str) -> None:
    assert select_playbook(goal) == expected


def test_security_has_priority_over_bugfix() -> None:
    assert (
        select_playbook("Fix security vulnerability in login handler")
        == "security"
    )
