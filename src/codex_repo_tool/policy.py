from __future__ import annotations
import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict
import yaml

DEFAULT_POLICY = {
    "protected_paths": ["**/.github/**", "**/.git/**"],
    "require_checks": {"lint": True, "tests": True}
}

@dataclass
class Policy:
    protected_paths: List[str] = field(default_factory=lambda: DEFAULT_POLICY["protected_paths"].copy())
    require_checks: Dict[str, bool] = field(default_factory=lambda: DEFAULT_POLICY["require_checks"].copy())

    def is_path_protected(self, path: str) -> bool:
        p = Path(path)
        parts = p.as_posix().split('/')
        if '.git' in parts or '.github' in parts:
            return True
        for pattern in self.protected_paths:
            try:
                if p.match(pattern):
                    return True
            except Exception:
                pass
        return False

def load_policy(root: str = ".") -> Policy:
    cfg = Path(root) / ".codexrt" / "policy.yml"
    if not cfg.exists():
        return Policy()
    try:
        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    except Exception:
        data = {}
    protected = data.get("protected_paths", DEFAULT_POLICY["protected_paths"])
    req = data.get("require_checks", DEFAULT_POLICY["require_checks"])
    return Policy(protected_paths=list(protected), require_checks=dict(req))
