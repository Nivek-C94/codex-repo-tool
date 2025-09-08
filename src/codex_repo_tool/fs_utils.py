from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Tuple, Optional


def list_files(root: str | Path) -> List[Dict[str, str]]:
    """
    Return a list of {'path': <path>} for files under root.
    """
    base = Path(root)
    out: List[Dict[str, str]] = []
    for p in base.rglob("*"):
        if p.is_file():
            out.append({"path": str(p)})
    return out


def read_file(path: str | Path, line_range: Optional[Tuple[int, int]] = None) -> str:
    """
    Read full file text. If line_range=(start,end) is provided (1-based, inclusive),
    return only those lines joined by '\n' with no trailing newline.
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="ignore")
    if not line_range:
        return text
    start, end = line_range
    lines = text.splitlines()
    # Clamp and slice inclusively
    start = max(1, start)
    end = max(start, end)
    sel = lines[start - 1 : end]
    return "\n".join(sel)
