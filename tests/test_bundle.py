import subprocess
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
        {
            "applied": True,
            "stage": "done",
            "lint": {"ok": True},
            "tests": {"ok": True},
        },
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


def test_bundle_qa_failure_returns_details(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    (repo / "a.txt").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)
    monkeypatch.chdir(repo)
    diff = "--- a/a.txt\n+++ b/a.txt\n@@ -1 +1 @@\n-hello\n+hi\n"
    bid = propose_bundle([{"file": "a.txt", "diff": diff, "description": ""}])
    monkeypatch.setattr(
        "codex_repo_tool.patch.lint_code",
        lambda: {"ok": False, "stdout": "", "stderr": "lint fail", "code": 1},
    )
    monkeypatch.setattr(
        "codex_repo_tool.patch.run_tests",
        lambda: {"ok": False, "stdout": "", "stderr": "test fail", "code": 1},
    )
    res = apply_bundle(bid, branch="HEAD")
    assert res["applied"] is False
    assert res["stage"] == "qa"
    assert res["lint"]["stderr"] == "lint fail"
    assert res["tests"]["stderr"] == "test fail"
