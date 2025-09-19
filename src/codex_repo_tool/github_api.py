from __future__ import annotations

import os
from typing import Any, Mapping

from .http_client import client as http_client

API = "https://api.github.com"


def _get_env() -> tuple[str, str, str]:
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    default_branch = os.getenv("DEFAULT_BRANCH", "main")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not set")
    if not repo:
        raise RuntimeError("GITHUB_REPO is not set (e.g., owner/name)")
    return token, repo, default_branch


def _headers(token: str) -> Mapping[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "codex-repo-tool/0.5",
    }


def _request_json(
    method: str,
    url: str,
    *,
    headers: Mapping[str, str],
    json_payload: Any | None = None,
    params: Mapping[str, Any] | None = None,
) -> Any:
    response = http_client.request(
        method,
        url,
        headers=headers,
        json=json_payload,
        params=params,
        timeout=30,
    )
    if hasattr(response, "raise_for_status"):
        response.raise_for_status()
    if hasattr(response, "json"):
        try:
            return response.json()
        except ValueError:
            return {}
    return {}


def open_pull_request(branch: str, title: str, body: str) -> dict[str, Any]:
    token, repo, default_branch = _get_env()
    url = f"{API}/repos/{repo}/pulls"
    payload = {"title": title, "head": branch, "base": default_branch, "body": body}
    data = _request_json("POST", url, headers=_headers(token), json_payload=payload)
    if not isinstance(data, dict):
        raise RuntimeError("Unexpected response when creating pull request")
    return data


def comment_pr(pr_id: int, body: str) -> dict[str, Any]:
    token, repo, _ = _get_env()
    url = f"{API}/repos/{repo}/issues/{pr_id}/comments"
    data = _request_json("POST", url, headers=_headers(token), json_payload={"body": body})
    if not isinstance(data, dict):
        raise RuntimeError("Unexpected response when commenting on pull request")
    return data


def list_issues(labels: list[str] | None = None, state: str = "open") -> list[dict[str, Any]]:
    token, repo, _ = _get_env()
    url = f"{API}/repos/{repo}/issues"
    params: dict[str, Any] = {"state": state}
    if labels:
        params["labels"] = ",".join(labels)
    data = _request_json("GET", url, headers=_headers(token), params=params)
    if isinstance(data, list):
        return data  # type: ignore[return-value]
    return []


def link_to_issue(issue_id: int, pr_id: int) -> dict[str, Any]:
    return comment_pr(pr_id, f"Linking to issue #{issue_id}.")
