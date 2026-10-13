"""
Compatibility shim. The Round 2 analyst now lives in ai_service.py (several Groq keys and
models, then Gemini keys, then the built-in replies). This module only keeps the old
`gemini_service.ask(...)` / `is_configured()` names working for any caller that still uses them.
"""

from __future__ import annotations

from . import ai_service


def is_configured() -> bool:
    return ai_service.is_configured()


def ask(system_prompt: str, history: list[dict], user_message: str) -> str | None:
    return ai_service.ask(system_prompt, history, user_message)
