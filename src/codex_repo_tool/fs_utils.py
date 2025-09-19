from __future__ import annotations

import fnmatch
from pathlib import Path


def list_files(root: str | Path, pattern: str | None = None) -> list[dict[str, str]]:
    base = Path(root)
    out: list[dict[str, str]] = []
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(base)
        if pattern and not fnmatch.fnmatch(str(rel), pattern):
            continue
        out.append({"path": str(p)})
    return out


def read_file(path: str | Path, line_range: tuple[int, int] | None = None) -> str:
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="ignore")
    if not line_range:
        return text
    start, end = line_range
    lines = text.splitlines()
    start = max(1, start)
    end = max(start, end)
    sel = lines[start - 1 : end]
    return "\n".join(sel)
