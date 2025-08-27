
from __future__ import annotations
import ast
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

PY_IMPORT_RE = re.compile(r'^\s*(?:from\s+([\w\.]+)\s+import\s+[\w\*]+|import\s+([\w\.]+))')
JS_IMPORT_RE = re.compile(r'^\s*import\s+(?:[^"\']+\s+from\s+)?["\']([^"\']+)["\']')
JS_REQUIRE_RE = re.compile(r'require\(\s*["\']([^"\']+)["\']\s*\)')

@dataclass
class Symbol:
    name: str
    kind: str  # function|class|variable
    file: str
    line: int

@dataclass
class FileIndex:
    symbols: List[Symbol]
    imports: List[str]

def _parse_python(path: Path) -> FileIndex:
    symbols: List[Symbol] = []
    imports: Set[str] = set()
    src = path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(src)
    except Exception:
        return FileIndex(symbols=[], imports=[])

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            symbols.append(Symbol(node.name, "function", str(path), node.lineno))
        elif isinstance(node, ast.AsyncFunctionDef):
            symbols.append(Symbol(node.name, "function", str(path), node.lineno))
        elif isinstance(node, ast.ClassDef):
            symbols.append(Symbol(node.name, "class", str(path), node.lineno))
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    symbols.append(Symbol(t.id, "variable", str(path), getattr(node, "lineno", 1)))
    for line in src.splitlines():
        m = PY_IMPORT_RE.match(line)
        if m:
            pkg = m.group(1) or m.group(2)
            if pkg:
                imports.add(pkg)
    return FileIndex(symbols=symbols, imports=sorted(imports))

def _parse_js_like(path: Path) -> FileIndex:
    symbols: List[Symbol] = []
    imports: Set[str] = set()
    src = path.read_text(encoding="utf-8", errors="ignore")
    # naive symbol extraction
    for i, line in enumerate(src.splitlines(), start=1):
        if re.search(r'^\s*function\s+([A-Za-z0-9_]+)\s*\(', line):
            name = re.findall(r'^\s*function\s+([A-Za-z0-9_]+)\s*\(', line)[0]
            symbols.append(Symbol(name, "function", str(path), i))
        elif re.search(r'^\s*class\s+([A-Za-z0-9_]+)', line):
            name = re.findall(r'^\s*class\s+([A-Za-z0-9_]+)', line)[0]
            symbols.append(Symbol(name, "class", str(path), i))
        elif re.search(r'^\s*(?:const|let|var)\s+([A-Za-z0-9_]+)\s*=', line):
            name = re.findall(r'^\s*(?:const|let|var)\s+([A-Za-z0-9_]+)\s*=', line)[0]
            symbols.append(Symbol(name, "variable", str(path), i))
        m1 = JS_IMPORT_RE.match(line)
        if m1:
            imports.add(m1.group(1))
        for m2 in JS_REQUIRE_RE.finditer(line):
            imports.add(m2.group(1))
    return FileIndex(symbols=symbols, imports=sorted(imports))

def _should_index(path: Path) -> bool:
    if not path.is_file():
        return False
    suf = path.suffix.lower()
    return suf in {".py", ".js", ".jsx", ".ts", ".tsx"}

def build_index(root: str = ".") -> Dict[str, dict]:
    """Return per-file indices with symbols+imports and a dependency adjacency list."""
    root_path = Path(root)
    per_file: Dict[str, FileIndex] = {}
    for p in root_path.rglob("*"):
        if _should_index(p):
            try:
                if p.suffix == ".py":
                    per_file[str(p)] = _parse_python(p)
                else:
                    per_file[str(p)] = _parse_js_like(p)
            except Exception:
                continue
    # Build deps map (file->imports) in a normalized way
    deps: Dict[str, List[str]] = {f: fi.imports for f, fi in per_file.items()}
    return { "files": {f: {"symbols": [asdict(s) for s in fi.symbols], "imports": fi.imports} for f, fi in per_file.items()},
             "deps": deps }

def find_symbol(name: str, index: dict) -> List[dict]:
    out: List[dict] = []
    for f, data in index.get("files", {}).items():
        for s in data.get("symbols", []):
            if s["name"] == name:
                out.append(s | {"file": f})
    return out

def dependency_graph(index: dict) -> dict:
    return index.get("deps", {})

def save_repo_map(index: dict, root: str = ".") -> str:
    p = Path(root) / ".codexrt"
    p.mkdir(parents=True, exist_ok=True)
    out = p / "map.json"
    out.write_text(__import__("json").dumps(index, indent=2), encoding="utf-8")
    return str(out)
