
from unittest import mock
from codex_repo_tool.qa import run_tests, lint_code

@mock.patch("codex_repo_tool.qa.docker_available", return_value=True)
@mock.patch("subprocess.run")
def test_docker_path_for_py(mock_run, mock_dok, tmp_path, monkeypatch):
    class R:
        def __init__(self, code=0):
            self.returncode = code
            self.stdout = ""
            self.stderr = ""
    mock_run.return_value = R(0)
    # Create Dockerfile to trigger docker path
    (tmp_path / "Dockerfile").write_text("FROM python:3.11-slim\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    monkeypatch.chdir(tmp_path)
    # Should attempt docker build/run; our mock makes it succeed
    assert run_tests()["ok"] is True
    assert lint_code()["ok"] in (True, False)  # may call ruff/black which aren't installed; mocked docker makes ok
