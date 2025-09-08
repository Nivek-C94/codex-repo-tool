from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    # Use a real Path so callers can do: SETTINGS.tmp_dir / "something"
    tmp_dir: Path = Path(os.environ.get("CODEX_TMP", ".codexrt"))
    github_token_env: str = "GITHUB_TOKEN"


SETTINGS = Settings()
