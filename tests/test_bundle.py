from unittest import mock

from codex_repo_tool.patch import apply_bundle, propose_bundle


@mock.patch("codex_repo_tool.patch.with_worktree")
def test_bundle_apply_happy(mock_wt, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bid = propose_bundle(
        [{"file": "a.txt", "diff": "--- a/a.txt\n+++ b/a.txt\n", "description": "d"}]
    )
    mock_wt.return_value = (
        True,
        {"applied": True, "stage": "done", "lint_ok": True, "tests_ok": True},
    )
    res = apply_bundle(bid, branch="HEAD")
    assert res["applied"] is True


@mock.patch("codex_repo_tool.patch.with_worktree")
def test_bundle_policy_block(mock_wt, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mock_wt.return_value = (
        True,
        {"applied": False, "stage": "policy", "error": "Protected path: a.txt"},
    )
    bid = propose_bundle(
        [{"file": "a.txt", "diff": "--- a/a.txt\n+++ b/a.txt\n", "description": "d"}]
    )
    res = apply_bundle(bid, branch="HEAD")
    assert res["applied"] is False
    assert res["stage"] == "policy"
