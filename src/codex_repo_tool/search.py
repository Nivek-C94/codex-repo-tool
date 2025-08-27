from __future__ import annotations
import re
import subprocess
from pathlib import Path

def _rg_available() -> bool:
    try:
        p = subprocess.run(["rg", "--version"], capture_output=True, text=True)
        return p.returncode == 0
    except Exception:
        return False

def _search_with_rg(query: str, root: str, scope: str | None):
    args = ["rg", "-n", "-H", query, root]
    if scope:
        args = ["rg", "-n", "-H", "--glob", scope, query, root]
    p = subprocess.run(args, capture_output=True, text=True)
    results = []
    if p.returncode not in (0, 1):
        return results
    for line in p.stdout.splitlines():
        try:
            path, lineno, match = line.split(":", 2)
            results.append({"path": path, "line": int(lineno), "match": match})
        except ValueError:
            continue
    return results

def _search_python(query: str, root: str, scope: str | None):
    results = []
    root_path = Path(root)
    pattern = re.compile(query, re.IGNORECASE)
    for p in root_path.rglob("*"):
        if not p.is_file():
            continue
        if scope and not p.match(scope):
            continue
        try:
            with p.open("r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, start=1):
                    if pattern.search(line):
                        results.append({"path": str(p), "line": i, "match": line.rstrip()})
        except Exception:
            continue
    return results

def search_code(query: str, scope: str | None = None, root: str = "."):
    if _rg_available():
        return _search_with_rg(query, root, scope)
    return _search_python(query, root, scope)
