from __future__ import annotations

import os
from typing import Any

import requests

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


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "codex-repo-tool/0.2.0",
    }


def open_pull_request(branch: str, title: str, body: str) -> dict[str, Any]:
    token, repo, default_branch = _get_env()
    url = f"{API}/repos/{repo}/pulls"
    payload = {"title": title, "head": branch, "base": default_branch, "body": body}
    r = requests.post(url, headers=_headers(token), json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def comment_pr(pr_id: int, body: str) -> dict[str, Any]:
    token, repo, _ = _get_env()
    url = f"{API}/repos/{repo}/issues/{pr_id}/comments"
    r = requests.post(url, headers=_headers(token), json={"body": body}, timeout=30)
    r.raise_for_status()
    return r.json()


def list_issues(labels: list[str] | None = None, state: str = "open") -> list[dict[str, Any]]:
    token, repo, _ = _get_env()
    url = f"{API}/repos/{repo}/issues"
    params = {"state": state}
    if labels:
        params["labels"] = ",".join(labels)
    r = requests.get(url, headers=_headers(token), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def link_to_issue(issue_id: int, pr_id: int) -> dict[str, Any]:
    return comment_pr(pr_id, f"Linking to issue #{issue_id}.")
