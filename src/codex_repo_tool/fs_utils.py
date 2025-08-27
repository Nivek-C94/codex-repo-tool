from __future__ import annotations
import os
from pathlib import Path
from typing import Iterable

def list_files(path: str = ".", pattern: str | None = None) -> list[dict]:
    base = Path(path)
    items: list[dict] = []
    if pattern is None:
        for p in base.rglob("*"):
            if p.is_file():
                items.append({"path": str(p), "size": p.stat().st_size, "suffix": p.suffix})
    else:
        import fnmatch
        for p in base.rglob("*"):
            if p.is_file() and fnmatch.fnmatch(p.name, pattern):
                items.append({"path": str(p), "size": p.stat().st_size, "suffix": p.suffix})
    return items

def read_file(path: str, lines: tuple[int, int] | None = None) -> str:
    p = Path(path)
    data = p.read_text(encoding="utf-8", errors="replace")
    if lines:
        start, end = lines
        return "\n".join(data.splitlines()[start-1:end])
    return data
