from __future__ import annotations

import os
import requests


def _openai_payload(goal: str, context: dict[str, str], model: str):
    # Minimal, provider-agnostic "diff-only" instruction
    prompt = (
        """Return a unified diff (git apply format) for the requested changes.
If changes are not needed, return an empty string.

GOAL:
"""
        + goal
        + """

CONTEXT (snippets, may be partial):
"""
        + "\n".join(f"== {k} ==\n{v}" for k, v in context.items())
    )
    return {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }


def get_diff(goal: str, context: dict[str, str]) -> str:
    """Built-in adapter to request a unified diff from an LLM endpoint."""
    model = os.getenv("MODEL_NAME", "gpt-4o-mini")
    api_key = os.getenv("API_KEY", "")
    url = os.getenv("API_URL", "https://api.openai.com/v1/chat/completions")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = _openai_payload(goal, context, model)
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    # Very thin extraction; robust parsing belongs to provider-specific adapters.
    return data.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
