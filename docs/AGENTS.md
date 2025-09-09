# Codex Repo Tool — Tutorial

This guide walks agents and developers through the common workflows supported by **codex-repo-tool**. Use it as a step-by-step tutorial when exploring or automating repository maintenance.

## 1. Setup

1. Install the package (already done in this environment):
   ```bash
   pip install codex-repo-tool
   ```
2. Navigate to a Git repository that you want to operate on.

## 2. One-Line Task Execution

For quick tasks that should handle diff planning, validation, commit and PR automatically:

```bash
codexrt run --goal "Add tests for src/add.py" --auto-pr
```

* `--goal` describes the change in natural language.
* `--auto-pr` (default) opens a pull request when checks pass.
* The command will refuse to commit if lint or tests fail.

## 3. Full Task Control

When you need more flags or want to run in `dry_run` mode, use the `task` subcommand:

```bash
codexrt task \
  --goal "Refactor helpers into utils/" \
  --hints "src/helpers" "tests" \
  --dry-run
```

* `--hints` restricts file discovery.
* `--dry-run` validates in a temporary worktree without committing.
* Omit `--dry-run` and add `--branch` to create and push changes.

## 4. Searching the Repository

```bash
codexrt search "def run_task"
```

This prints each match with the file path and line number, scanning only source-like files.

## 5. Crafting Patches Manually

1. Propose a patch:
   ```bash
   codexrt patch propose <<'DIFF'
   --- a/README.md
   +++ b/README.md
   @@ -1,3 +1,4 @@
    # Codex Repo Tool
    Unified repository operations for AI agents.
   +Added quickstart example.
   DIFF
   ```
2. If the patch applies cleanly you will see a success message.
3. Apply the stored patch into the working tree:
   ```bash
   codexrt patch apply
   ```
4. Run validation checks (lint and tests):
   ```bash
   codexrt qa
   ```

## 6. Python API

The same capabilities are available programmatically:

```python
from codex_repo_tool import run_task, search_code

hits = search_code('def run_task')
print(hits[0])  # {'path': 'src/codex_repo_tool/task.py', 'line_no': 10, 'line': 'def run_task(...'}

run_task(goal="Update README quickstart", dry_run=True)
```

`run_task` mirrors the `codexrt run` command, returning a dictionary describing the result.

## 7. Validation Policy

The tool enforces checks defined in `.codexrt/policy.yml`. By default:

- Lint and tests must pass (`require_checks`).
- Writes to sensitive paths like `.git/` are blocked (`protected_paths`).

Adjust the policy file if your workflow requires different rules.

## 8. Next Steps

- Explore `examples/sample.diff` for a minimal unified diff.
- Review `README.md` for project overview.
- Run `codexrt --help` to see all available commands.

This AGENTS file only documents usage; it does not enforce additional rules on files under `docs/`.
