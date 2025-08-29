
from __future__ import annotations
import os
import json
from typing import Dict

import requests

def _openai_payload(goal: str, context: Dict[str, str], model: str):
    # Minimal, provider-agnostic "diff-only" instruction
    prompt = (
        "You are a coding agent. Produce ONLY a multi-file unified diff for the goal below.\n"
        "If changes are not needed, return an empty string.\n\n"
        f"GOAL:\n{goal}\n\n"
        "CONTEXT (snippets, may be partial):\n" + "\n".join(f"== {k} ==\n{v}" for k,v in context.items())
    )
    return {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    }

def get_diff(goal: str, context: Dict[str, str]) -> str:
    """
    Built-in adapter to request a unified diff from an LLM endpoint.
    Supported via environment:
      MODEL_PROVIDER: "openai" | "azure_openai" | "http"
      MODEL_NAME: e.g., "gpt-4o-mini"
      API_KEY: API key for provider
      MODEL_ENDPOINT: for http/azure custom endpoints
    Returns empty string on failure.
    """
    provider = os.getenv("MODEL_PROVIDER", "").lower()
    model = os.getenv("MODEL_NAME", "gpt-4o-mini")
    api_key = os.getenv("API_KEY", "")
    endpoint = os.getenv("MODEL_ENDPOINT", "")

    try:
        if provider in ("openai", "azure_openai"):
            url = endpoint or "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = _openai_payload(goal, context, model)
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()
            # Best-effort extraction
            return data.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
        elif provider == "http":
            # Generic POST that returns {"diff": "..."} or raw text
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            payload = {"goal": goal, "context": context}
            r = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            try:
                data = r.json()
                return data.get("diff", "") or data.get("content", "") or ""
            except Exception:
                return r.text
    except Exception:
        return ""
    return ""
