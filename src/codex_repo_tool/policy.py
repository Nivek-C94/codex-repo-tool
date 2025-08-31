from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_POLICY = {
    "protected_paths": ["package-lock.json", "pnpm-lock.yaml", "yarn.lock"],
    "require_checks": {"lint": True, "tests": True},
}


@dataclass
class Policy:
    protected_paths: list[str] = field(
        default_factory=lambda: DEFAULT_POLICY["protected_paths"].copy()
    )
    require_checks: dict[str, bool] = field(
        default_factory=lambda: DEFAULT_POLICY["require_checks"].copy()
    )

    def is_path_protected(self, path: str) -> bool:
        p = Path(path).name
        return p in self.protected_paths


def load_policy(path: str | None = None) -> Policy:
    if path and Path(path).exists():
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return Policy(
            protected_paths=data.get("protected_paths", DEFAULT_POLICY["protected_paths"]),
            require_checks=data.get("require_checks", DEFAULT_POLICY["require_checks"]),
        )
    return Policy()
