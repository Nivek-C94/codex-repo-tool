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
