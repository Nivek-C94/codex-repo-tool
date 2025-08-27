import json
from unittest import mock
from codex_repo_tool.patch import propose_patch, apply_patch, discard_patch

def test_propose_and_discard(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pid = propose_patch("foo.py", "--- a/foo.py\n+++ b/foo.py\n", "desc")
    assert pid.startswith("patch_")
    assert discard_patch(pid) is True

@mock.patch("subprocess.run")
def test_apply_patch_checks(mock_run, tmp_path, monkeypatch):
    # Simulate successful dry-run, apply, lint, tests
    class R: 
        def __init__(self, code=0): 
            self.returncode=code; self.stdout=""; self.stderr=""
    mock_run.side_effect = [R(0), R(0), R(0), R(0)]
    monkeypatch.chdir(tmp_path)
    pid = propose_patch("foo.py", "--- a/foo.py\n+++ b/foo.py\n", "desc")
    res = apply_patch(pid)
    assert res["applied"] is True
