from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    github_token: str | None = os.getenv("GITHUB_TOKEN")
    github_repo: str | None = os.getenv("GITHUB_REPO")
    default_branch: str = os.getenv("DEFAULT_BRANCH", "main")
    patches_dir: str = os.getenv("CODEXRT_PATCHES_DIR", ".codexrt/patches")
    workdir: str = os.getenv("CODEXRT_WORKDIR", ".")
    timeout_sec: int = int(os.getenv("CODEXRT_TIMEOUT_SEC", "600"))

SETTINGS = Settings()
