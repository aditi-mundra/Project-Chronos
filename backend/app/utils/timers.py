"""
Project Chronos — Timers and Synchronization Utilities
Server-authoritative timestamp management and ISO-8601 parsing.
"""

from datetime import datetime, timezone
from typing import Optional

def get_utc_now() -> datetime:
    """Returns current UTC datetime."""
    return datetime.now(timezone.utc)

def get_utc_now_iso() -> str:
    """Returns current UTC datetime formatted as ISO-8601 string."""
    return get_utc_now().isoformat()

def calculate_time_diff_seconds(start_iso: Optional[str], end_iso: Optional[str]) -> float:
    """Calculates duration in seconds between two ISO-8601 timestamps."""
    if not start_iso or not end_iso:
        return 0.0
    try:
        start_dt = datetime.fromisoformat(start_iso)
        end_dt = datetime.fromisoformat(end_iso)
        return max(0.0, (end_dt - start_dt).total_seconds())
    except Exception:
        return 0.0
