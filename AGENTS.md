# Codex Repo Tool — AI Integration Guide (v0.5.x)

## 0) Purpose

* Provide a single entry point for "plan → diff → sandbox apply → lint/tests" so agents can update a Git repo safely.
* All Git writes happen inside a temporary worktree; the main checkout is never modified directly.

---

## 1) Entry Points

### A) Python helper (`codex_repo_tool.task.run`)

```python
from codex_repo_tool.task import run
result = run(
    goal="Append a line to README",
    auto_pr=True,               # optional – see note below
    ask_model_for_diff=my_diff_function,  # optional override
    model="gpt-4o-mini",       # optional override for model_adapter
)
```

* **Signature:** `run(goal: str, auto_pr: bool = False, ask_model_for_diff: Callable | None = None, model: str | None = None) -> dict`.
* When `ask_model_for_diff` is `None`, the tool calls `model_adapter.get_diff(goal, context={}, model=model)`.
* The return payload always includes `{"ok": bool, "branch": "HEAD", "stage": <str>, ...}`. A successful run sets `ok=True`, `stage="done"`, and includes lint/test results from the sandbox.
* On failure to generate a diff (empty string), the function returns `{ok: False, stage: "plan", reason: "no-diff"}`.
* `auto_pr=True` calls `github_api.open_pull_request(title=goal)`. The default GitHub helper currently expects positional `branch`/`body`, so in real use you will want to monkeypatch or wrap it before enabling `auto_pr`.

### B) CLI (`codexrt`)

```
codexrt run "Append a line to README" [--auto-pr] [--model MODEL_NAME]
```

* `run` is the happy-path wrapper around `task.run`. Arguments map 1:1 to the Python helper (`goal` positional, optional `--auto-pr`, optional `--model`).
* `task` is wired to the same helper but currently forwards many unsupported options. Stick to `codexrt run` unless you replace `run_task` with a richer implementation.
* Other useful subcommands:
  * `codexrt ls --path src/` – recursively list files.
  * `codexrt cat README.md --start 1 --end 20` – print slices of a file.
  * `codexrt search "def run"` – naïve substring search across `.py/.txt/.md/.rst` files.
  * Patch helpers: `codexrt propose <file> <diff>`, `codexrt apply <patch_id>`, `codexrt discard <patch_id>`.
  * Bundle helpers: `codexrt bundle '[{"file": "README.md", "diff": "..."}]'` plus `codexrt apply-bundle-commit <bundle_path>` to run the sandbox + QA.
  * QA shortcuts: `codexrt lint`, `codexrt test`.
  * Semantic helpers: `codexrt index`, `codexrt symbol <Name>`, `codexrt deps`, `codexrt summarize` (writes `.codexrt/map.json`).
  * PR helper: `codexrt pr --branch feature --title "My PR" --body "..."` (passes straight through to the GitHub API module).

### C) Lower-level APIs

* `propose_patch(file, diff, description="")` → returns an ID like `patch_ab12cd34` stored under `${CODEX_TMP:-.codexrt}/`.
* `apply_patch(patch_id, branch="HEAD")` → validates a single diff with `git apply --check`.
* `propose_bundle(items)` → writes `{"items": [...]}` JSON and returns the file path.
* `apply_bundle(bundle_id, branch="HEAD")` → opens a detached worktree for `branch`, applies every diff, then runs lint/tests per policy. This is what `task.run` uses under the hood.

---

## 2) What the Model Must Output

* Return **only** a unified diff – no explanations, no extra text.
* Use standard headers and hunks:

  ```
  --- a/path.ext
  +++ b/path.ext
  @@ -old,+new @@ optional header
  -old line
  +new line
  ```
* Combine multiple files by concatenating multiple `---/+++` blocks. Paths must be repo-relative.
* New files are created naturally by diff headers (`--- /dev/null`, `+++ b/new/file`).

**Minimal example**:

```
--- a/README.md
+++ b/README.md
@@ -1,3 +1,4 @@
 # CodexRepoTool
 
 Unified, safe, high-level repo operations for AI agents (e.g., Codex).
+Added quickstart usage.
```

`task.run` pulls file targets from the `+++ b/<path>` lines. If none are present, it assumes `README.md` to keep tests stable.

---

## 3) Pipeline Inside `task.run`

1. **Playbook tagging** – `select_playbook(goal)` classifies the goal (`bugfix`, `add-tests`, `refactor`, `upgrade-dep`, `general`). The return value is not yet used for branching logic but provides a hook.
2. **Diff acquisition** – `ask_model_for_diff(goal, context)` if supplied, otherwise `model_adapter.get_diff`. Context is currently an empty dict; you can pre-fill it with `{path: file_snippet}` if you wrap `run`.
3. **Bundle assembly** – `_targets_from_diff` extracts the `+++ b/...` paths, then each target receives the same diff payload in the bundle. The bundle is stored under `${CODEX_TMP:-.codexrt}/bundle.json`.
4. **Sandbox apply** – `apply_bundle` calls `git worktree add --detach <tmp>` for `branch="HEAD"`, copies each diff to the worktree, and runs `git apply --check` followed by `git apply`.
5. **QA phase** – after patching, `lint_code()` and `run_tests()` execute if the policy requires them (defaults: both required). Failures yield `{applied: False, stage: "qa", lint: {...}, tests: {...}}`.
6. **Result assembly** – the dict from `apply_bundle` is returned with an added `ok` flag (`applied` coerced to bool) and the `branch` name. No commits, pushes, or branch creation occur. The main checkout stays untouched.
7. **Optional PR** – if `auto_pr` is true, `open_pull_request(title=goal)` is called. Because no branch is created automatically, this helper is only useful when you pre-create a branch and adjust `open_pull_request` to default to it.

**Failure stages you may see:**
* `plan` – diff was empty.
* `dry-run` – `git apply --check` failed in the sandbox.
* `apply` – `git apply` failed.
* `qa` – lint or tests failed; see the embedded `lint` / `tests` dicts.
* `worktree-add` – `git worktree add` failed (often because you are not in a Git repo).
* `{error: "Not a git repository"}` – the sandbox could not find a Git root.

---

## 4) Environment & Configuration

* **Temp directory:** `config.SETTINGS.tmp_dir` defaults to `.codexrt/`. Override via `CODEX_TMP=/path`.
* **Model adapter:**
  * Set `MODEL_PROVIDER=http` to POST `{goal, context}` to `MODEL_ENDPOINT` (or `MODEL_URL` / `DIFF_ENDPOINT`). Response must be JSON containing `{"diff": "..."}`.
  * Default provider is `openai`. Configure `OPENAI_API_KEY`, optionally `OPENAI_ENDPOINT` (defaults to `https://api.openai.com/v1/chat/completions`) and `OPENAI_MODEL` (defaults to `gpt-4o-mini`). Responses may be OpenAI-style chat completions or a plain `{"diff": "..."}` payload.
* **GitHub API:** `github_api.open_pull_request` requires `GITHUB_TOKEN`, `GITHUB_REPO` (e.g., `owner/name`), and optional `DEFAULT_BRANCH` (`main` if unset). Because `task.run` does not create or push a branch, callers typically disable `auto_pr` or swap in a stub for testing.
* **Docker flag:** `docker_sandbox.docker_available()` just checks `docker version`. `_run_in_docker` currently executes commands directly (no container isolation yet).

---

## 5) Policy & QA Defaults

* `policy.load_policy()` looks for `policy.yaml` or `.codexrt/policy.yaml`; if absent it uses `Policy(require_checks={"lint": True, "tests": True})`.
* The default protection only blocks paths containing `.git/hooks/`. All other paths are allowed.
* `lint_code()` runs:
  * `ruff check --fix .` when Python tooling is detected, OR
  * `npm run lint` (with optional scope) for JS projects.
  * If neither tool is present, linting succeeds immediately.
* `run_tests()` runs:
  * `pytest -q` (optionally with a scope argument) when Python tooling is detected, OR
  * `npm test` for Node projects.
  * If no known test runner exists, the function reports success with a "skipping" message.

---

## 6) Search & Semantic Helpers

* `search_code(query, root=".")` performs a simple substring scan over `.py`, `.txt`, `.md`, `.rst` files. There is no ripgrep dependency yet.
* `semantic.build_index(root)` builds a naive symbol/import map for Python and JS/TS files using `ast` or regex heuristics.
* `semantic.save_repo_map(index, root)` writes the map to `.codexrt/map.json` and returns the file path.

---

## 7) Troubleshooting Cheatsheet

| Stage / Error            | Likely Cause & Fix |
|--------------------------|--------------------|
| `plan`                   | Diff blank or whitespace only. Regenerate with actual edits.
| `dry-run`                | Patch failed `git apply --check`. Update diff context against HEAD.
| `apply`                  | Patch failed to apply even after the dry-run check (usually conflicts). Adjust diff.
| `qa`                     | Lint/tests failed. Inspect `res["lint"]` and `res["tests"]` for stdout/stderr.
| `worktree-add` / `error` | Not in a Git repo or `git worktree` unsupported. Initialise Git or adjust environment.

---

## 8) Minimal JSON Tool Invocation

```json
{
  "tool": "task.run",
  "arguments": {
    "goal": "Append a troubleshooting note to README",
    "auto_pr": false
  }
}
```

Produce a unified diff that updates `README.md`; no additional metadata is needed.

---

## 9) Good Practices for Agents

1. **Search before renaming.** Use `codexrt search` or `semantic.find_symbol` to locate all references.
2. **Respect repo conventions.** Match formatting, module style, and lint expectations (ruff, npm lint, etc.).
3. **Keep diffs focused.** Edit only what the goal requires to keep the sandbox happy.
4. **Mind QA defaults.** If lint/tests are required, update them in the same diff so the bundle passes.
5. **No secrets.** GitHub helpers rely on `GITHUB_TOKEN`; never print or commit sensitive values.
6. **Communicate optional extras.** If you add opportunistic fixes (docs, comments), mark them optional so humans can back them out.

---

## 10) Status Menu Template

When summarising work, include:

* **Repository:** `<repo name>`
* **Main Goal:** `<task objective>`
* **Suggested Next Task:** `<concise follow-up>`

