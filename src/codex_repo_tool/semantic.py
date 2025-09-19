from __future__ import annotations

import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List

PY_IMPORT_RE = re.compile(r"^\s*(?:from\s+([\w\.]+)\s+import\s+[\w\*]+|import\s+([\w\.]+))")


@dataclass
class Symbol:
    name: str
    kind: str
    line: int


@dataclass
class FileIndex:
    symbols: List[Symbol]
    imports: List[str]


def _parse_python(path: Path) -> FileIndex:
    symbols: List[Symbol] = []
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
    symbols: List[Symbol] = []
    imports: set[str] = set()
    src = path.read_text(encoding="utf-8", errors="ignore")
    for i, line in enumerate(src.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("function "):
            fn = stripped.split()[1].split("(")[0]
            symbols.append(Symbol(fn, "function", i))
        if stripped.startswith("class "):
            cls = stripped.split()[1].split("{")[0]
            symbols.append(Symbol(cls, "class", i))
        m = re.match(PY_IMPORT_RE, line)
        if m:
            pkg = m.group(1) or m.group(2)
            if pkg:
                imports.add(pkg)
    return FileIndex(symbols=symbols, imports=list(imports))


def _should_index(p: Path) -> bool:
    return p.suffix in {".py", ".js", ".jsx", ".ts", ".tsx"}


def build_index(root: str = ".") -> dict[str, Dict[str, Dict[str, List[str]]]]:
    root_path = Path(root)
    per_file: Dict[str, FileIndex] = {}
    for p in root_path.rglob("*"):
        if _should_index(p):
            fi = _parse_python(p) if p.suffix == ".py" else _parse_js_like(p)
            per_file[str(p)] = fi
    deps: Dict[str, List[str]] = {f: fi.imports for f, fi in per_file.items()}
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
            if s.get("name") == name:
                out.append({"file": f, **s})
    return out


def dependency_graph(root_or_index: str | Path | dict = ".") -> dict[str, list[str]]:
    if isinstance(root_or_index, dict):
        return root_or_index.get("deps", {})
    idx = build_index(str(root_or_index))
    return idx.get("deps", {})


def save_repo_map(index: dict, root: str = ".") -> str:
    path = Path(root) / ".codexrt" / "map.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index), encoding="utf-8")
    return str(path)
