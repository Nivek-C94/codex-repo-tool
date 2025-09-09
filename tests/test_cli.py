import json
import sys
from unittest import mock

from codex_repo_tool import run_task as run_task_alias
from codex_repo_tool.cli import main
from codex_repo_tool.task import run as run_task

SAMPLE_DIFF = """--- a/README.md
+++ b/README.md
@@ -1,3 +1,4 @@
 # CodexRepoTool
 
 Unified, safe, high-level repo operations for AI agents (e.g., Codex).
+Added by task test.
"""


def test_run_task_alias():
    assert run_task_alias is run_task


@mock.patch("codex_repo_tool.task.open_pull_request")
@mock.patch("subprocess.run")
def test_cli_run(mock_run, mock_pr, tmp_path, monkeypatch, capsys):
    class R:
        def __init__(self, code=0):
            self.returncode = code
            self.stdout = ""
            self.stderr = ""

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
    monkeypatch.setattr(
        "codex_repo_tool.task.get_diff",
        lambda goal, ctx, model=None: SAMPLE_DIFF,
    )
    monkeypatch.setattr(sys, "argv", ["codexrt", "run", "Append line", "--auto-pr"])

    main()
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["ok"] is True
    assert "pr" in data
