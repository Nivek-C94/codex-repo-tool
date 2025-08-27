from codex_repo_tool.policy import load_policy, Policy
from pathlib import Path

def test_policy_defaults(tmp_path: Path):
    p = load_policy(str(tmp_path))
    assert isinstance(p, Policy)
    assert p.require_checks["lint"] is True
    assert p.is_path_protected(".git/hooks/pre-commit") is True
