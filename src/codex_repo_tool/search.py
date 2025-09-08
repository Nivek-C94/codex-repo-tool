from __future__ import annotations

import subprocess
from pathlib import Path


def _rg_available() -> bool:
    return subprocess.run(["bash", "-lc", "command -v rg"], capture_output=True).returncode == 0


def search_code(pattern: str, path: str = ".", max_results: int = 200) -> list[dict]:
    root = Path(path)
    results: list[dict] = []
    if _rg_available():
        cmd = [
            "rg",
            "-n",
            "--json",
            "--hidden",
            "--glob",
            "!.git",
            "--max-count",
            str(max_results),
            pattern,
            str(root),
        ]
        p = subprocess.run(cmd, capture_output=True, text=True)
        results.append({"stdout": p.stdout, "stderr": p.stderr, "code": p.returncode})
    else:
        p = subprocess.run(["grep", "-RIn", pattern, str(root)], capture_output=True, text=True)
        results.append({"stdout": p.stdout, "stderr": p.stderr, "code": p.returncode})
    return results
