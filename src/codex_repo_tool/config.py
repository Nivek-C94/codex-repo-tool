from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    tmp_dir: os.PathLike[str] = os.fspath(os.environ.get("CODEX_TMP", ".codexrt"))
    github_token_env: str = "GITHUB_TOKEN"


SETTINGS = Settings()
