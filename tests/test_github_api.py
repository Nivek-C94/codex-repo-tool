from unittest import mock

from codex_repo_tool.github_api import open_pull_request


@mock.patch("codex_repo_tool.github_api.requests.post")
def test_open_pr(mock_post, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPO", "owner/name")
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"number": 1}
    mock_post.return_value.raise_for_status.return_value = None
    out = open_pull_request("feature/x", "t", "b")
    assert out["number"] == 1
