from __future__ import annotations

import argparse
import json

from .fs_utils import list_files, read_file
from .github_api import open_pull_request
from .patch import (
    apply_bundle,
    apply_patch,
    discard_patch,
    propose_bundle,
    propose_patch,
)
from .qa import lint_code, run_tests
from .search import search_code
from .semantic import (
    build_index,
    dependency_graph,
    find_symbol,
    save_repo_map,
)
from .task import run as run_task


def main() -> None:
    parser = argparse.ArgumentParser("codexrt", description="Codex Repo Tool CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ls
    p_ls = sub.add_parser("ls", help="List files")
    p_ls.add_argument("--path", default=".")
    p_ls.add_argument("--pattern", default=None)

    # cat
    p_cat = sub.add_parser("cat", help="Read a file (slice)")
    p_cat.add_argument("path")
    p_cat.add_argument("--start", type=int)
    p_cat.add_argument("--end", type=int)

    # search
    p_search = sub.add_parser("search", help="Search code via ripgrep/grep")
    p_search.add_argument("pattern")
    p_search.add_argument("--path", default=".")
    p_search.add_argument("--max", type=int, default=200)

    # patch ops
    p_prop = sub.add_parser("propose", help="Propose a single-file patch")
    p_prop.add_argument("file")
    p_prop.add_argument("diff")
    p_prop.add_argument("--description", default="")

    p_apply = sub.add_parser("apply", help="Apply a single-file patch")
    p_apply.add_argument("patch_id")
    p_apply.add_argument("--branch", default="HEAD")

    p_discard = sub.add_parser("discard", help="Discard a proposed patch")
    p_discard.add_argument("patch_id")

    # bundle ops
    p_bundle = sub.add_parser("bundle", help="Propose a bundle (JSON list items)")
    p_bundle.add_argument("items_json", help="JSON: [{file,diff,description}, ...]")

    p_apply_bundle = sub.add_parser("apply-bundle-commit", help="Validate bundle in sandbox")
    p_apply_bundle.add_argument("bundle_id")
    p_apply_bundle.add_argument("--branch", default="HEAD")

    # QA
    p_test = sub.add_parser("test", help="Run tests (best effort)")
    p_test.add_argument("--scope", default=None)

    p_lint = sub.add_parser("lint", help="Run linters (best effort)")
    p_lint.add_argument("--scope", default=None)

    # index/symbol/deps/summarize
    p_index = sub.add_parser("index", help="Build repo index")
    p_index.add_argument("--root", default=".")

    p_symbol = sub.add_parser("symbol", help="Find symbol by name")
    p_symbol.add_argument("name")
    p_symbol.add_argument("--root", default=".")

    p_deps = sub.add_parser("deps", help="Dependency graph (adjacency)")
    p_deps.add_argument("--root", default=".")

    p_sum = sub.add_parser("summarize", help="Write repo summary map to disk")
    p_sum.add_argument("--root", default=".")

    # simplified task runner
    p_run = sub.add_parser("run", help="Run a task with minimal options")
    p_run.add_argument("goal", help="Natural language task objective")
    p_run.add_argument("--auto-pr", action="store_true", default=False)
    p_run.add_argument("--model", default=None)

    # task orchestrator
    p_task = sub.add_parser("task", help="Plan → validate → (optional) PR")
    p_task.add_argument("--goal", required=True)
    p_task.add_argument("--hints", nargs="*", default=[])
    p_task.add_argument("--dry-run", action="store_true")
    p_task.add_argument("--auto-pr", action="store_true", default=False)
    p_task.add_argument("--branch", default=None)
    p_task.add_argument("--pr-title", default="")
    p_task.add_argument("--pr-body", default="")
    p_task.add_argument("--max-files", type=int, default=50)
    p_task.add_argument("--time-budget-sec", type=int, default=600)
    p_task.add_argument("--strict-checks", action="store_true")

    # PR
    p_pr = sub.add_parser("pr", help="Open PR")
    p_pr.add_argument("--branch", required=True)
    p_pr.add_argument("--title", required=True)
    p_pr.add_argument("--body", default="")

    args = parser.parse_args()

    if args.cmd == "ls":
        print(json.dumps(list_files(args.path, args.pattern), indent=2))
    elif args.cmd == "cat":
        lines = (args.start, args.end) if args.start and args.end else None
        print(read_file(args.path, lines))
    elif args.cmd == "search":
        print(json.dumps(search_code(args.pattern, args.path, args.max), indent=2))
    elif args.cmd == "propose":
        print(json.dumps(propose_patch(args.file, args.diff, args.description), indent=2))
    elif args.cmd == "apply":
        print(json.dumps(apply_patch(args.patch_id, args.branch), indent=2))
    elif args.cmd == "discard":
        print(json.dumps(discard_patch(args.patch_id), indent=2))
    elif args.cmd == "bundle":
        items = json.loads(args.items_json)
        print(json.dumps(propose_bundle(items), indent=2))
    elif args.cmd == "apply-bundle-commit":
        # Validate bundle in sandbox
        res = apply_bundle(args.bundle_id, args.branch)
        print(json.dumps(res, indent=2))
        if not res.get("applied"):
            return
    elif args.cmd == "test":
        print(json.dumps(run_tests(args.scope), indent=2))
    elif args.cmd == "lint":
        print(json.dumps(lint_code(args.scope), indent=2))
    elif args.cmd == "index":
        print(json.dumps(build_index(args.root), indent=2))
    elif args.cmd == "symbol":
        idx = build_index(args.root)
        print(json.dumps(find_symbol(args.name, idx), indent=2))
    elif args.cmd == "deps":
        idx = build_index(args.root)
        print(json.dumps(dependency_graph(idx), indent=2))
    elif args.cmd == "summarize":
        idx = build_index(args.root)
        path = save_repo_map(idx, args.root)
        print(path)
    elif args.cmd == "run":
        res = run_task(goal=args.goal, auto_pr=args.auto_pr, model=args.model)
        print(json.dumps(res, indent=2))
    elif args.cmd == "task":
        res = run_task(
            goal=args.goal,
            hints=args.hints,
            dry_run=args.dry_run,
            auto_pr=args.auto_pr,
            branch=args.branch,
            pr_title=args.pr_title,
            pr_body=args.pr_body,
            max_files=args.max_files,
            time_budget_sec=args.time_budget_sec,
            strict_checks=args.strict_checks,
        )
        print(json.dumps(res, indent=2))
    elif args.cmd == "pr":
        print(json.dumps(open_pull_request(args.branch, args.title, args.body), indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
