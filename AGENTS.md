# Codex Repo Tool — AI Integration Guide (v0.5.x)

## 0) Purpose

* Do a whole repo task in **one call**: *discover → plan → edit (LLM diff) → validate → commit/push → PR*.
* Keeps changes safe (policy, sandbox apply, required checks).

---

## 1) Entry Points

### A) Tool function (preferred by agents)

**Name:** `task.run`
**Behavior:** Orchestrates end-to-end pipeline.
**Args:**

* `goal` *(string, required)* — Natural language task objective.
* `hints` *(string\[])* — Paths/globs to scope discovery (files/dirs).
* `dry_run` *(bool, default false)* — Validate in sandbox only; no branch/push/PR.
* `auto_pr` *(bool, default true)* — Open PR on success.
* `branch` *(string)* — Branch name; default `codexrt/auto/<slug(goal)>`.
* `pr_title` *(string)* — Defaults to `chore: <goal>`.
* `pr_body` *(string)* — Defaults to a standard body with the goal.
* `max_files` *(int, default 50)* — Discovery limit.
* `time_budget_sec` *(int, default 600)* — Soft guard.
* `strict_checks` *(bool, default true)* — Fail if lint/tests fail.

**Return (JSON):**

* On success: `{ ok: true, branch, pr?: {…}, elapsed_sec, diff_items }`
* On failure: `{ ok: false, stage: "plan|apply|branch|apply-working|stage|commit|push", error? , stdout?, stderr? }`

**Example call (tool JSON):**

```json
{
  "tool": "task.run",
  "arguments": {
    "goal": "Add unit tests for src/parser.py and fix null handling bug",
    "hints": ["src/parser.py", "tests/"],
    "auto_pr": true,
    "branch": "codexrt/auto/parser-tests"
  }
}
```

### B) CLI (useful for operators & debugging)

```bash
codexrt task \
  --goal "Refactor helpers into utils/ and add tests" \
  --auto-pr \
  --branch codexrt/auto/refactor-utils
```

---

## 2) What the Tool Expects From the AI

### Unified diff output (from the model)

* **Only** output a **multi-file unified diff** (no prose).
* Use standard headers:

  ```
  --- a/relative/path.ext
  +++ b/relative/path.ext
  @@ -old,+new @@ optional hunk header
  -old line
  +new line
  ```
* Multiple files = multiple `---/+++` blocks concatenated.
* Paths **must be relative** to repo root.
* Create new files with a normal diff; tool will add them.
* Do not edit `.git`, `.github`, or files disallowed by policy.

**Minimal diff example:**

```
--- a/README.md
+++ b/README.md
@@ -1,3 +1,4 @@
 # CodexRepoTool

 Unified, safe, high-level repo operations for AI agents (e.g., Codex).
+Added quickstart usage.
```

### Context provided to the model

* Tool builds a lightweight repo context (selected file heads/snippets) and **auto-prefixes** your goal with a playbook tag:

  * `[bugfix]`, `[add-tests]`, `[refactor]`, `[upgrade-dep]`, or `[general]`.

---

## 3) How the Pipeline Works (stages)

1. **Discover**: resolve `hints` into candidate files (cap at `max_files`).
2. **Index/Map**: `.codexrt/map.json` used to assist selection (maintenance refreshes it).
3. **Playbook**: goal classified to guide the model.
4. **LLM Diff**: built-in adapter calls your model to get a unified diff.
5. **Sandbox Apply**: apply diff safely; reject if malformed or touches protected paths.
6. **Validate**:

   * `lint` + `tests` (inside Docker if `Dockerfile` or `.codexrt/docker.yml` and Docker is present).
7. **Commit/Push/PR** *(skipped in `dry_run`)*:

   * Create branch → apply diff → commit → push → open PR (if `auto_pr`).

**Failure surfaces (`stage` values):**

* `plan` (no/empty diff), `apply` (bundle apply), `branch`, `apply-working`, `stage` (git add), `commit`, `push`.

---

## 4) Environment & Config

### Required/Recommended env

```bash
# Model for diff generation
MODEL_PROVIDER=openai|azure_openai|http
MODEL_NAME=gpt-4o-mini             # example; choose supported model
API_KEY=...                        # provider key
MODEL_ENDPOINT=https://...         # required for http/azure custom endpoints

# GitHub for PRs
GITHUB_TOKEN=ghp_xxx
GITHUB_REPO=owner/name             # auto-inferred when origin=GitHub
DEFAULT_BRANCH=main                # auto-inferred; falls back to current
```

### Optional behavior flags (speed/infra)

```bash
CODEXRT_SKIP_UPDATE=1              # skip pip update of tool during maintenance
CODEX_FAST=1                       # maintenance: lint+test only (skip extras)
CODEX_SUMMARIZE_MAX_AGE_MIN=30     # refresh map.json only if older than this
CODEX_SKIP_HUSKY=1                 # don’t (re)install Husky during maintenance
CODEX_INSTALL_CLI=0                # skip brew/apt/etc optional CLI installs
CODEX_WRITE_BASHRC=0               # don’t edit ~/.bashrc to add venv PATH
```

### Docker validations (optional)

* If Docker is available and there’s a `Dockerfile` or `.codexrt/docker.yml`, lint/tests run inside a container.
* `.codexrt/docker.yml` example:

  ```yaml
  image: node:20
  lint: ["npm","run","lint"]
  test: ["npm","run","test"]
  ```

### Policy

* `.codexrt/policy.yml` defaults:

  * `protected_paths`: blocks `.git/**`, `.github/**`, `secrets/**`
  * `require_checks`: `lint: true`, `tests: true`

---

## 5) Start & Maintenance Scripts (what they do for the AI)

* **`scripts/codex_setup_once.sh` (run once per instance)**

  * pyenv-aware Python detection → create `.codexrt/.venv`
  * Install `codex-repo-tool` from GitHub
  * Seed `.codexrt/policy.yml`, `.codexrt/docker.yml`
  * Build initial `.codexrt/map.json`
  * Install Node dev tooling + repo helper scripts; set npm scripts; init Husky

* **`scripts/codex_maintenance_before_task.sh` (run every task)**

  * Optionally stash → `git fetch/rebase` (ff-only)
  * Install JS deps (lockfile-aware)
  * Ensure eslint/prettier/test scripts exist
  * Update `codex-repo-tool` (unless `CODEXRT_SKIP_UPDATE=1`)
  * Refresh `.codexrt/map.json` (time-gated if `CODEX_SUMMARIZE_MAX_AGE_MIN` is set)
  * Infer `GITHUB_REPO`/`DEFAULT_BRANCH` safely (no empty exports)

*You don’t need to call these manually if your environment is wired to run them automatically before work.*

---

## 6) Agent Prompting Patterns (produce diffs reliably)

* **Bugfix task:**

  > *Goal*: Fix crash in `src/parser.py` when config is `null`. Add a unit test reproducing the issue.
  > *Output*: Only a multi-file unified diff that (1) updates `src/parser.py` with explicit null checks and (2) adds a test file under `tests/test_parser.py` covering null config. Do not include commentary.

* **Refactor + tests:**

  > *Goal*: Move helpers from `src/helpers/*.js` into `src/utils/` and update imports. Add basic unit tests for the moved functions.
  > *Output*: Only a unified diff updating all imports and creating tests. Preserve behavior; avoid changing public APIs.

* **Dependency bump (non-breaking):**

  > *Goal*: Bump `lodash` to `^4.17.21`, update lockfile, and fix any lint issues.
  > *Output*: Only unified diff for `package.json` and any necessary code changes (no prose). Do not bump unrelated deps.

**Key rules to include in your model system prompt:**

* “Return **only** a multi-file unified diff; no explanations.”
* “Paths must be relative to repo root.”
* “Don’t modify protected paths.”
* “Prefer small, testable changes with passing lint/tests.”

---

## 7) Good Practices for the AI

* **Scope with `hints`** (paths/globs) to keep diffs focused.
* **Add tests** for behavior changes; place under existing test framework (jest/vitest/pytest).
* **Honor project style** (ESM/CJS, tsconfig, lint rules).
* **Keep atomic**: one task’s changes in one diff (don’t mix refactors and feature work).
* **Avoid large lockfile churn** unless the goal is dependency work.

---

## 8) Troubleshooting (AI can self-diagnose via `stage`)

* `stage: "plan"` → Your diff was empty/malformed. Re-emit a proper unified diff.
* `stage: "apply"` or `"apply-working"` → Patch didn’t apply; likely paths or hunks don’t match. Re-base your diff against HEAD or adjust context lines.
* `stage: "commit" / "push"` → Branch/remote issues; ensure `GITHUB_REPO` and permissions or set `dry_run`.
* Lint/test failures → Update the diff to fix code style or broken tests; include necessary changes to tests.

---

## 9) Minimal End-to-End Example

**Call:**

```json
{
  "tool": "task.run",
  "arguments": {
    "goal": "Add vitest for src/add.ts and fix add() to handle negatives",
    "hints": ["src/add.ts", "tests/"],
    "auto_pr": true
  }
}
```

**Model should return a diff that:**

* Edits `src/add.ts` to correctly sum negatives.
* Adds/updates `tests/add.test.ts` to cover negative inputs.
* Nothing else.

---

## 10) Safety & Limits

* Protected paths are blocked; diffs touching them will fail.
* By default, **lint + tests must pass** (`strict_checks: true`).
* Dockerized checks run only if Docker is available and config is present.
* Large diffs or unrelated file churn may be rejected by sandbox apply.

---
