"""
Runtime settings.

Values come from the process environment first, then from a `.env` file
(backend/.env or <project>/.env), the same places gemini_service already reads
GEMINI_API_KEY from. Nothing secret is ever hard-coded here.
"""

from __future__ import annotations

import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]  # the folder that contains backend/
_ENV_FILES = (_ROOT / "backend" / ".env", _ROOT / ".env")


def setting(name: str, default: str = "") -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value

    for env_file in _ENV_FILES:
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, raw = line.partition("=")
                if key.strip() == name:
                    value = raw.strip().strip('"').strip("'")
                    if value:
                        return value
        except OSError:
            continue

    return default
