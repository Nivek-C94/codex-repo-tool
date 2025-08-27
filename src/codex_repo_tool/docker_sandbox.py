
from __future__ import annotations
import subprocess

def docker_available() -> bool:
    try:
        p = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        return p.returncode == 0
    except Exception:
        return False
