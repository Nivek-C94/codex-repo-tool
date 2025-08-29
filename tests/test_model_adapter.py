
from unittest import mock
from codex_repo_tool.model_adapter import get_diff

@mock.patch("codex_repo_tool.model_adapter.requests.post")
def test_adapter_openai_path(mock_post, monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "openai")
    monkeypatch.setenv("MODEL_NAME", "gpt-4o-mini")
    monkeypatch.setenv("API_KEY", "x")
    mock_post.return_value.json.return_value = {"choices": [{"message": {"content": "--- a/x\n+++ b/x\n"}}]}
    mock_post.return_value.raise_for_status.return_value = None
    out = get_diff("goal", {"x.py": "code"})
    assert out.startswith("--- a/")

@mock.patch("codex_repo_tool.model_adapter.requests.post")
def test_adapter_http_path(mock_post, monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "http")
    monkeypatch.setenv("MODEL_ENDPOINT", "https://example.com/diff")
    mock_post.return_value.json.return_value = {"diff": "--- a/y\n+++ b/y\n"}
    mock_post.return_value.raise_for_status.return_value = None
    out = get_diff("goal", {"y.py": "code"})
    assert out.startswith("--- a/")
