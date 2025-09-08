from __future__ import annotations

import ast
import re
from dataclasses import asdict, dataclass
from pathlib import Path

PY_IMPORT_RE = re.compile(r"^\s*(?:from\s+([\w\.]+)\s+import\s+[\w\*]+|import\s+([\w\.]+))")


@dataclass
class Symbol:
    name: str
    kind: str
    line: int


@dataclass
class FileIndex:
    symbols: list[Symbol]
    imports: list[str]


def _parse_python(path: Path) -> FileIndex:
    symbols: list[Symbol] = []
    imports: set[str] = set()
    src = path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbols.append(Symbol(node.name, "function", node.lineno))
            elif isinstance(node, ast.ClassDef):
                symbols.append(Symbol(node.name, "class", node.lineno))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
    except SyntaxError:
        pass
    return FileIndex(symbols=symbols, imports=list(imports))


def _parse_js_like(path: Path) -> FileIndex:
    symbols: list[Symbol] = []
    imports: set[str] = set()
    src = path.read_text(encoding="utf-8", errors="ignore")
    # naive symbol extraction
    for i, line in enumerate(src.splitlines(), 1):
        if line.strip().startswith("function "):
            fn = line.strip().split()[1].split("(")[0]
            symbols.append(Symbol(fn, "function", i))
        if line.strip().startswith("class "):
            cls = line.strip().split()[1].split("{")[0]
            symbols.append(Symbol(cls, "class", i))
        m = re.match(PY_IMPORT_RE, line)
        if m:
            pkg = m.group(1) or m.group(2)
            imports.add(pkg)
    return FileIndex(symbols=symbols, imports=list(imports))


def _should_index(p: Path) -> bool:
    suf = p.suffix
    return suf in {".py", ".js", ".jsx", ".ts", ".tsx"}


def build_index(root: str = ".") -> dict[str, dict]:
    """Return per-file indices with symbols+imports and a dependency adjacency list."""
    root_path = Path(root)
    per_file: dict[str, FileIndex] = {}
    for p in root_path.rglob("*"):
        if _should_index(p):
            fi = _parse_python(p) if p.suffix == ".py" else _parse_js_like(p)
            per_file[str(p)] = fi
        else:
            continue
    # Build deps map (file->imports) in a normalized way
    deps: dict[str, list[str]] = {f: fi.imports for f, fi in per_file.items()}
    return {
        "files": {
            f: {"symbols": [asdict(s) for s in fi.symbols], "imports": fi.imports}
            for f, fi in per_file.items()
        },
        "deps": deps,
    }


def find_symbol(name: str, index: dict) -> list[dict]:
    out: list[dict] = []
    for f, data in index.get("files", {}).items():
        for s in data.get("symbols", []):
            if s["name"] == name:
                out.append({"file": f, **s})
    return out


def dependency_graph(root: str = ".") -> dict[str, list[str]]:
    """
    Expose the dependency adjacency list from build_index(root).
    Keys are file paths (strings), values are the list of imports found.
    """
    idx = build_index(root)
    return idx.get("deps", {})
