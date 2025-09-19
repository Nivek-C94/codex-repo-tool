from __future__ import annotations

import os
from typing import Any

from .http_client import client as http_client


def _openai_payload(goal: str, context: dict[str, str], model: str) -> dict[str, Any]:
    prompt = (
        "You are a code patch generator.\n"
        "Given a goal and a small context mapping {filename: content}, "
        "produce ONLY a unified diff. No explanations."
    )
    user = f"Goal:\n{goal}\n\nContext files:\n" + "\n".join(
        f"- {k} ({len(v)} bytes)" for k, v in context.items()
    )
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
    }


def _post_json(url: str, payload: Any, headers: dict[str, str] | None = None, timeout: int = 30) -> Any:
    response = http_client.post(url, json=payload, headers=headers or {}, timeout=timeout)
    if hasattr(response, "raise_for_status"):
        response.raise_for_status()
    if hasattr(response, "json"):
        try:
            return response.json()
        except ValueError:
            return {}
    return {}


def get_diff(goal: str, context: dict[str, str], model: str | None = None) -> str:
    provider = (os.environ.get("MODEL_PROVIDER") or "openai").lower()

    if provider == "http":
        endpoint = (
            os.environ.get("MODEL_ENDPOINT")
            or os.environ.get("MODEL_URL")
            or os.environ.get("DIFF_ENDPOINT")
        )
        if not endpoint:
            return ""
        data = _post_json(endpoint, {"goal": goal, "context": context}, timeout=30)
        if isinstance(data, dict):
            diff = data.get("diff", "")
            return diff or ""
        return ""

    endpoint = os.environ.get("OPENAI_ENDPOINT", "https://api.openai.com/v1/chat/completions")
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    headers: dict[str, str] = {}
    if os.environ.get("OPENAI_API_KEY"):
        headers["Authorization"] = f"Bearer {os.environ['OPENAI_API_KEY']}"
    payload = _openai_payload(goal, context, model)

    data = _post_json(endpoint, payload, headers=headers, timeout=60)
    if isinstance(data, dict) and "diff" in data:
        return data.get("diff") or ""

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return ""
