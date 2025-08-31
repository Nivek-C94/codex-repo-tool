from __future__ import annotations

    from pathlib import Path


    def list_files(path: str = ".", pattern: str | None = None) -> list[dict]:
        root = Path(path)
        files = []
        for p in root.rglob(pattern or "*"):
            if p.is_file():
                files.append({"path": str(p), "size": p.stat().st_size})
        return files


    def read_file(path: str, lines: tuple[int, int] | None = None) -> str:
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
        if lines:
            start, end = lines
            return "
".join(text.splitlines()[start:end])
        return text
