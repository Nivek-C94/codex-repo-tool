from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Dict


def _iter_text_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in {".py", ".txt", ".md", ".rst"}:
            yield p


def search_code(query: str, root: str | Path = ".") -> List[Dict[str, object]]:
    """
    Naive text search for `query` under `root`.
    Returns a list of hits: {'path': <file>, 'line': <1-based>, 'text': <line>}.
    """
    base = Path(root)
    hits: List[Dict[str, object]] = []
    for file in _iter_text_files(base):
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if query in line:
                hits.append({"path": str(file), "line": i, "text": line})
    return hits
