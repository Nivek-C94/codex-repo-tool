import subprocess
from unittest import mock

from codex_repo_tool.task import run

SAMPLE_DIFF = """--- a/README.md
+++ b/README.md
@@ -1,3 +1,4 @@
 # CodexRepoTool
 
 Unified, safe, high-level repo operations for AI agents (e.g., Codex).
+Added by task test.
"""


@mock.patch("codex_repo_tool.task.open_pull_request")
@mock.patch("subprocess.run")
def test_task_happy(mock_run, mock_pr, tmp_path, monkeypatch):
    class R:
        def __init__(self, code=0):
            self.returncode = code
            self.stdout = ""
            self.stderr = ""

    # checkout, apply, add, commit, push
    mock_run.return_value = R(0)
    mock_pr.return_value = {"number": 1}

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "README.md").write_text(
        "# CodexRepoTool\n\nUnified, safe, high-level repo operations for AI agents (e.g., Codex).\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(repo)

    def ask(goal, ctx):
        return SAMPLE_DIFF

    res = run(goal="Append line to README", auto_pr=True, ask_model_for_diff=ask)
    assert res["ok"] is True
    assert "branch" in res


@mock.patch("subprocess.run")
def test_task_no_diff(mock_run, tmp_path, monkeypatch):
    class R:
        def __init__(self, code=0):
            self.returncode = code
            self.stdout = ""
            self.stderr = ""

    mock_run.return_value = R(0)
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "README.md").write_text("# x\n", encoding="utf-8")
    monkeypatch.chdir(repo)

    res = run(goal="Nothing", auto_pr=False, ask_model_for_diff=lambda g, c: "")
    assert res["ok"] is False
    assert res["stage"] == "plan"


def test_task_qa_failure_details(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    (repo / "README.md").write_text(
        "# CodexRepoTool\n\nUnified, safe, high-level repo operations for AI agents (e.g., Codex).\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)
    monkeypatch.chdir(repo)
    monkeypatch.setattr(
        "codex_repo_tool.patch.lint_code",
        lambda: {"ok": False, "stdout": "", "stderr": "lint fail", "code": 1},
    )
    monkeypatch.setattr(
        "codex_repo_tool.patch.run_tests",
        lambda: {"ok": False, "stdout": "", "stderr": "test fail", "code": 1},
    )
    res = run(
        goal="Append line to README",
        auto_pr=False,
        ask_model_for_diff=lambda g, c: SAMPLE_DIFF,
    )
    assert res["ok"] is False
    assert res["stage"] == "qa"
    assert res["lint"]["stderr"] == "lint fail"
    assert res["tests"]["stderr"] == "test fail"
