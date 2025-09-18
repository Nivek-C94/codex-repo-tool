# Codex Repo Tool — Tutorial

This short guide mirrors the current CLI/API behaviour. Use it as a walkthrough when experimenting with `codex-repo-tool`.

## 1. Setup

1. Install the package (already done in this environment):
   ```bash
   pip install codex-repo-tool
   ```
2. Run commands from inside a Git repository (the sandbox relies on `git worktree`).

## 2. One-Line Task Execution

Run the end-to-end pipeline with the positional goal argument:

```bash
codexrt run "Add tests for src/add.py"
```

* `--auto-pr` is optional. It calls `github_api.open_pull_request(title=goal)`, so you typically patch that helper when testing.
* `--model` overrides the default model name passed to `model_adapter.get_diff`.
* The command stops after lint/tests; it does **not** commit or push.

## 3. Full Control via Bundles

When you want to assemble patches manually and still rely on the sandbox:

```bash
codexrt bundle '[{"file": "README.md", "diff": "--- a/README.md\n+++ b/README.md\n"}]'
# -> prints the bundle path (e.g., .codexrt/bundle.json)

codexrt apply-bundle-commit .codexrt/bundle.json
# -> applies inside a detached worktree, runs lint/tests, and reports JSON
```

* `codexrt apply <patch_id>` is available for single-file diffs created with `codexrt propose`.
* To discard a proposed patch, run `codexrt discard <patch_id>`.

## 4. Repository Utilities

* `codexrt ls --path src/` – list files (recursive).
* `codexrt cat README.md --start 1 --end 20` – print a slice of a file.
* `codexrt search "def run_task"` – naïve substring scan over `.py`, `.txt`, `.md`, `.rst` files (no ripgrep dependency yet).
* `codexrt lint` / `codexrt test` – run `ruff` or `pytest` / `npm` based on detected project type.
* `codexrt index` – build a lightweight symbol/import index; combine with `codexrt symbol` or `codexrt deps`.
* `codexrt summarize` – write `.codexrt/map.json` from the latest index.

## 5. Python API

```python
from codex_repo_tool import run_task

result = run_task(
    goal="Update README quickstart",
    auto_pr=False,
)
print(result["stage"])  # "done" on success
```

* The helper is an alias of `codex_repo_tool.task.run`.
* The returned dict includes QA results and failure diagnostics (`stage`, `lint`, `tests`).

## 6. Validation Policy

`policy.load_policy()` reads `policy.yaml` or `.codexrt/policy.yaml`. Defaults:

- Lint and tests are required (`require_checks: {lint: true, tests: true}`).
- Only `.git/hooks/` paths are protected. Other paths rely on sandbox validation rather than policy enforcement.

## 7. Next Steps

- Inspect `README.md` for a high-level project overview.
- Browse `tests/` to understand expected JSON payloads.
- Run `python -m codex_repo_tool.cli --help` to see every subcommand.

This file documents behaviour only; it does not impose extra rules on docs.
