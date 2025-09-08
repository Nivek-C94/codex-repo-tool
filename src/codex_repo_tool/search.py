from __future__ import annotations

from pathlib import Path
from typing import Iterable, List


def _iter_text_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in {".py", ".txt", ".md", ".rst"}:
            yield p


def search_code(query: str, root: str | Path = ".") -> List[str]:
    """
    Naive text search for `query` under `root`. Returns a list of file paths
    (as strings) that contain the query at least once.
    """
    base = Path(root)
    hits: list[str] = []
    for file in _iter_text_files(base):
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if query in text:
            hits.append(str(file))
    return hits
