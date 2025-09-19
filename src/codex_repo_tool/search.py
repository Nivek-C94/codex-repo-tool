from __future__ import annotations

from pathlib import Path
from typing import Iterator


def _iter_text_files(root: Path) -> Iterator[Path]:
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in {".py", ".txt", ".md", ".rst"}:
            yield p


def search_code(query: str, root: str | Path = ".", max_results: int | None = None) -> list[dict[str, object]]:
    base = Path(root)
    hits: list[dict[str, object]] = []
    for file in _iter_text_files(base):
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if query in line:
                hits.append({"path": str(file), "line": i, "text": line})
                if max_results is not None and len(hits) >= max_results:
                    return hits
    return hits
