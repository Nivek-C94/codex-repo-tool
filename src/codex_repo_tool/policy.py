from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

import yaml


@dataclass
class Policy:
    # which checks to require after applying a bundle
    require_checks: Dict[str, bool] = field(default_factory=lambda: {"lint": True, "tests": True})

    def is_path_protected(self, path: str | Path) -> bool:
        """
        Default policy: protect .git hooks (e.g., .git/hooks/pre-commit) by default.
        Keeps other paths unprotected.
        """
        s = str(path).replace("\\", "/")
        # Normalize to avoid false negatives with relative/absolute variants
        if ".git/hooks/" in s or s.endswith(".git/hooks/pre-commit"):
            return True
        return False


def load_policy(path: str | None = None) -> Policy:
    """
    Load policy from a YAML file if present; otherwise return defaults.
    - If `path` is a directory, look for 'policy.yaml' or '.codexrt/policy.yaml' inside it.
    - If `path` is a file, read that file.
    - If nothing found, return default Policy().
    """
    candidates: list[Path] = []
    if path:
        p = Path(path)
        if p.is_dir():
            candidates = [p / "policy.yaml", p / ".codexrt" / "policy.yaml"]
        else:
            candidates = [p]
    else:
        candidates = [Path(".") / "policy.yaml", Path(".") / ".codexrt" / "policy.yaml"]

    for c in candidates:
        if c.exists() and c.is_file():
            data = yaml.safe_load(c.read_text(encoding="utf-8")) or {}
            req = data.get("require_checks", {})
            lint = bool(req.get("lint", True))
            tests = bool(req.get("tests", True))
            return Policy(require_checks={"lint": lint, "tests": tests})
    return Policy()
