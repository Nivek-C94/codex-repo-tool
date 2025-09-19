from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    yaml = None


@dataclass
class Policy:
    require_checks: dict[str, bool] = field(
        default_factory=lambda: {"lint": True, "tests": True}
    )

    def is_path_protected(self, path: str | Path) -> bool:
        s = str(path).replace("\\", "/")
        if ".git/hooks/" in s or s.endswith(".git/hooks/pre-commit"):
            return True
        return False


def load_policy(path: str | Path | None = None) -> Policy:
    candidates: list[Path] = []
    if path is not None:
        p = Path(path)
        if p.is_dir():
            candidates = [p / "policy.yaml", p / ".codexrt" / "policy.yaml"]
        else:
            candidates = [p]
    else:
        cwd = Path(".")
        candidates = [cwd / "policy.yaml", cwd / ".codexrt" / "policy.yaml"]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            if yaml is None:
                data = {}
            else:
                data = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
            req = data.get("require_checks", {}) if isinstance(data, dict) else {}
            lint = bool(req.get("lint", True))
            tests = bool(req.get("tests", True))
            return Policy(require_checks={"lint": lint, "tests": tests})
    return Policy()
