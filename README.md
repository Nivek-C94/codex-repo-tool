# Codex Repo Tool

Codex Repo Tool is a guardrailed automation harness for AI agents. It wraps the common
"discover → plan → diff → sandbox apply → lint/tests" loop in a lightweight Python package
and CLI so that models can update repositories with confidence. Humans are welcome to peek
under the hood, but every feature is designed first for automated operators.

## Why it matters

* **Agent-friendly defaults** – sensible environment detection, optional dependencies, and
  JSON-friendly outputs make the tool trivial to orchestrate from an LLM workflow.
* **Sandboxed safety** – patches are validated in temporary worktrees before touching the
  main checkout, with lint/tests enforced by a pluggable policy.
* **Single-call ergonomics** – run `codexrt task --goal "…"` and the tool will obtain a
  diff (via your model adapter), apply it in isolation, run QA, and optionally file a PR.
* **Repository intelligence** – semantic indexing, dependency graphs, and status helpers
  keep the agent aware of the codebase without bespoke scripting.

## Quickstart

```bash
# run an end-to-end task (diff + sandbox + QA)
codexrt run "Refactor helpers into utils and add tests"

# add --auto-pr once you have a branch pushed and GitHub credentials configured
codexrt run "Refactor helpers into utils and add tests" --auto-pr
```

Python helper:

```python
from codex_repo_tool import run_task

result = run_task("Add feature flag to payment flow")
print(result["stage"], result["ok"])
```

## Capabilities

| Area | Highlights |
| --- | --- |
| **Patching** | `propose`, `apply`, and `bundle` helpers store diffs under `.codexrt/` and validate them in detached worktrees. |
| **Task runner** | `codexrt run` and `codexrt task` orchestrate model diff generation, sandbox apply, QA, and optional PR creation. |
| **Policy & QA** | YAML-driven policy toggles lint/test requirements; QA runners automatically select `pytest`, `ruff`, or `npm`. |
| **Repo insight** | `codexrt index`, `symbol`, `deps`, and `summarize` expose per-file symbols/imports and dependency adjacency graphs. |
| **Search & FS utilities** | Naive search across text files, pattern-aware file listings, and sliced file reads for quick context gathering. |

## Configuration cheat-sheet

Environment variables drive integrations so agents do not need to edit source code:

| Variable | Purpose |
| --- | --- |
| `MODEL_PROVIDER` (`openai`/`http`) | Selects the diff generator backend. |
| `MODEL_ENDPOINT` / `MODEL_URL` / `DIFF_ENDPOINT` | Custom HTTP endpoint for `MODEL_PROVIDER=http`. |
| `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_ENDPOINT` | Credentials for the OpenAI-compatible path. |
| `GITHUB_TOKEN`, `GITHUB_REPO`, `DEFAULT_BRANCH` | GitHub integration for PR/comment helpers. |
| `CODEX_TMP` | Override the working directory used for patches/bundles. |

The HTTP client automatically prefers `requests` when available, but gracefully falls back
to the Python standard library so agent environments stay lean.

## CLI overview

```
codexrt ls --path src/ --pattern "*.py"     # enumerate files
codexrt cat README.md --start 1 --end 20     # slice a file
codexrt search "def run" --path src/        # simple text search
codexrt propose README.md "<diff>"          # store a patch under .codexrt/
codexrt apply-bundle-commit bundle.json     # sandbox validation (lint/tests enforced)
codexrt task --goal "Fix flaky tests"       # full pipeline with hint support
```

All commands print JSON or plain text results that are easy for agents to parse.

## Development notes

* The package uses [PEP 561](https://peps.python.org/pep-0561/) friendly type hints to keep
  interfaces obvious when consumed programmatically.
* Tests exercise the CLI surface, model adapter, GitHub client, sandbox, and semantic index
  so agents get deterministic behaviour out of the box.
* Optional extras such as Docker-based QA or HTTP fallbacks are implemented in thin, easily
  mockable layers to keep the core loop fast.

## Status

The project is a living reference implementation for AI-first repository operations. Expect
APIs to evolve as the automation story grows richer, but the guiding principle remains:
keep agents productive without compromising safety.
