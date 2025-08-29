# CodexRepoTool

Unified, safe, high-level repo operations for AI agents (e.g., Codex).

## Goals
- High-level, atomic operations (search, patch, test, PR)
- Guardrails before applying changes (lint, tests)
- Minimal deps; standard CLI; CI-ready

## Status
MVP scaffolding with working CLI and mocked tests.


## New in 0.2.0
- ripgrep-accelerated search
- Policy engine (.codexrt/policy.yml)
- Patch bundles & sandboxed apply


## New in 0.3.0
- Semantic index & lightweight dependency graph for Python + JS/TS (`codexrt index`, `symbol`, `deps`, `summarize`)
- Repo map cache at `.codexrt/map.json`
- `apply-bundle-commit` (validate in sandbox; intentionally read-only to main tree for safety)
- Docker sandbox detection stub (future: containerized validations)


## New in 0.4.0 — One-call task runner
Run an entire pipeline with a single command:

```bash
codexrt task --goal "Refactor helpers into utils/ and add tests" --auto-pr --branch codexrt/auto/refactor-utils
```


## New in 0.5.0 — Built-in model adapter & Docker checks
- **Model adapter**: set `MODEL_PROVIDER`, `MODEL_NAME`, `API_KEY`, `MODEL_ENDPOINT` and the tool will call your LLM to obtain a unified diff automatically (no injection needed).
- **Auto playbook selection**: goals are prefixed with a lightweight playbook tag to guide the model (e.g., `[bugfix]`).
- **Containerized validations**: if Docker is available and a `Dockerfile` or `.codexrt/docker.yml` exists, lint/tests run **inside Docker**.
