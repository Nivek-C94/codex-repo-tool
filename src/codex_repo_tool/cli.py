from __future__ import annotations
import argparse
import json
from .fs_utils import list_files, read_file
from .search import search_code
from .patch import propose_patch, apply_patch, discard_patch, propose_bundle, apply_bundle
from .qa import run_tests, lint_code, static_analysis
from .github_api import open_pull_request
from .task import run as run_task
from .semantic import build_index, find_symbol, dependency_graph, save_repo_map
from .patch import apply_bundle

def main() -> None:
    parser = argparse.ArgumentParser("codexrt", description="Codex Repo Tool CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ls = sub.add_parser("ls", help="List files")
    p_ls.add_argument("--path", default=".", help="Root path")
    p_ls.add_argument("--pattern", default=None)

    p_cat = sub.add_parser("cat", help="Read file")
    p_cat.add_argument("path")
    p_cat.add_argument("--start", type=int)
    p_cat.add_argument("--end", type=int)

    p_search = sub.add_parser("search", help="Search code")
    p_search.add_argument("query")
    p_search.add_argument("--scope", default=None)
    p_search.add_argument("--root", default=".")

    p_prop = sub.add_parser("propose", help="Propose a patch")
    p_prop.add_argument("file")
    p_prop.add_argument("diff")
    p_prop.add_argument("--desc", default="")

    p_apply = sub.add_parser("apply", help="Apply a patch")
    p_apply.add_argument("patch_id")
    p_apply.add_argument("--no-lint", action="store_true")
    p_apply.add_argument("--no-test", action="store_true")

    p_bundle = sub.add_parser("bundle", help="Propose a patch bundle")
p_bundle.add_argument("bundle_json", help="Path to a JSON file: [{file,diff,description}]")
p_bundle.add_argument("--desc", default="")

p_applyb = sub.add_parser("apply-bundle", help="Apply a patch bundle in sandbox worktree")
p_applyb.add_argument("bundle_id")
p_applyb.add_argument("--branch", default=None)

p_discard = sub.add_parser("discard", help="Discard a patch")
    p_discard.add_argument("patch_id")

    p_test = sub.add_parser("test", help="Run tests")
    p_test.add_argument("--scope", default=None)

    p_lint = sub.add_parser("lint", help="Run lint")

    
    p_index = sub.add_parser("index", help="Build semantic index")
    p_index.add_argument("--root", default=".")

    p_symbol = sub.add_parser("symbol", help="Find symbol in index")
    p_symbol.add_argument("name")
    p_symbol.add_argument("--root", default=".")

    p_deps = sub.add_parser("deps", help="Show dependency graph")
    p_deps.add_argument("--root", default=".")

    p_sum = sub.add_parser("summarize", help="Build and save repo map")
    p_sum.add_argument("--root", default=".")

    p_applybc = sub.add_parser("apply-bundle-commit", help="Apply bundle in sandbox, commit on a branch")
    p_applybc.add_argument("bundle_id")
    p_applybc.add_argument("--branch", required=True)
    p_applybc.add_argument("--message", required=True)

    p_task = sub.add_parser("task", help="Run a one-call task pipeline")
p_task.add_argument("--goal", required=True)
p_task.add_argument("--hints", nargs="*", default=[])
p_task.add_argument("--dry-run", action="store_true")
p_task.add_argument("--auto-pr", action="store_true")
p_task.add_argument("--branch", default=None)
p_task.add_argument("--pr-title", default="")
p_task.add_argument("--pr-body", default="")
p_task.add_argument("--max-files", type=int, default=50)
p_task.add_argument("--time-budget-sec", type=int, default=600)
p_task.add_argument("--strict-checks", action="store_true")

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
        print(json.dumps(search_code(args.query, args.scope, args.root), indent=2))
    elif args.cmd == "propose":
        pid = propose_patch(args.file, args.diff, args.desc)
        print(pid)
    elif args.cmd == "apply":
        res = apply_patch(args.patch_id, run_lint=not args.no_lint, run_test=not args.no_test)
        print(json.dumps(res, indent=2))
    elif args.cmd == "bundle":
    import json, pathlib
    items = json.loads(pathlib.Path(args.bundle_json).read_text(encoding='utf-8'))
    bid = propose_bundle(items, args.desc)
    print(bid)
elif args.cmd == "apply-bundle":
    print(json.dumps(apply_bundle(args.bundle_id, args.branch), indent=2))
elif args.cmd == "discard":
        print(discard_patch(args.patch_id))
    elif args.cmd == "test":
        print(json.dumps(run_tests(args.scope), indent=2))
    elif args.cmd == "lint":
        print(json.dumps(lint_code(), indent=2))

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
    elif args.cmd == "apply-bundle-commit":
        # Run sandbox validations then create branch and commit inside the worktree clone
        res = apply_bundle(args.bundle_id, args.branch)
        print(json.dumps(res, indent=2))
        if not res.get("applied"):
            return
        # If sandbox OK, create commit on current repo (not sandbox) is up to user; we only validated in sandbox.
        # For safety we stop here to avoid writing to the main working tree.
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
