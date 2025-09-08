from __future__ import annotations

import os
from typing import Any, Dict

import requests


def _openai_payload(goal: str, context: Dict[str, str], model: str) -> Dict[str, Any]:
    # Minimal, provider-agnostic "diff-only" instruction
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


def get_diff(goal: str, context: Dict[str, str], model: str | None = None) -> str:
    """
    Providers:
      - MODEL_PROVIDER=http:
          POST JSON {'goal','context'} to endpoint env:
            MODEL_ENDPOINT | MODEL_URL | DIFF_ENDPOINT
          expect {'diff': '...'} and return it.
      - MODEL_PROVIDER=openai (default):
          POST OpenAI-style payload to OPENAI_ENDPOINT (or default).
          Accept either {'diff': '...'} or OpenAI-style choices[].
    """
    provider = (os.environ.get("MODEL_PROVIDER") or "openai").lower()

    if provider == "http":
        endpoint = (
            os.environ.get("MODEL_ENDPOINT")
            or os.environ.get("MODEL_URL")
            or os.environ.get("DIFF_ENDPOINT")
        )
        if not endpoint:
            return ""
        resp = requests.post(endpoint, json={"goal": goal, "context": context}, timeout=30)
        # In tests, raise_for_status is mocked to no-op
        if hasattr(resp, "raise_for_status"):
            resp.raise_for_status()
        data = (resp.json() or {}) if hasattr(resp, "json") else {}
        diff = data.get("diff", "")
        return diff or ""

    # default: openai-style
    endpoint = os.environ.get("OPENAI_ENDPOINT", "https://api.openai.com/v1/chat/completions")
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    headers: Dict[str, str] = {}
    if os.environ.get("OPENAI_API_KEY"):
        headers["Authorization"] = f"Bearer {os.environ['OPENAI_API_KEY']}"
    payload = _openai_payload(goal, context, model)

    resp = requests.post(endpoint, json=payload, headers=headers, timeout=60)
    if hasattr(resp, "raise_for_status"):
        resp.raise_for_status()
    data = (resp.json() or {}) if hasattr(resp, "json") else {}

    # Allow tests to just return {"diff": "..."} even on "openai" path
    if "diff" in data:
        return data.get("diff") or ""

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return ""
