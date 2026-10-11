"""
Admin access and the leaderboard data.

Admin access
  * CHRONOS_ADMIN_PASSWORD must be set (environment or .env). With no password the
    admin API is disabled; there is no built-in default.
  * Login returns a signed, expiring bearer token (HMAC-SHA256). Every /api/admin
    route except /login requires it.

Leaderboard data
  * Read-only: it only SELECTs, so opening or polling the leaderboard never changes
    any score or state.
  * It reports only what the database actually recorded. A round with no recorded
    result is None (shown as "-"), never 0. The total adds up the recorded rounds and
    says whether all three are present (total_complete).
  * Round 2 is investigation-only. Its only scoring rule is the AI-question
    deduction (EVENT_SPECIFICATIONS.md: start with 20, questions cost 5, 5, 10). The
    score is read from the recorded deductions (round2_chat_messages.points_deducted)
    for a team that has started Round 2, and stays None for a team that has not. While
    Round 2 is still running the value is flagged round2_provisional. A score recorded
    by an earlier build's culprit submission is used as recorded.
  * Ranking follows EVENT_SPECIFICATIONS.md: total score, then earlier Round 3
    completion, then earlier Round 2 completion, then earlier Round 1 completion.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import io
import json
import sqlite3
import time
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Header, HTTPException, Request

from ..config import setting
from ..database.connection import get_connection
from .round2_service import AI_BUDGET

TOKEN_TTL_SECONDS = 8 * 60 * 60
_FAILURE_WINDOW = 10 * 60
_FAILURE_LIMIT = 8
_failures: dict[str, list[float]] = {}


# --- authentication --------------------------------------------------------------

def _password() -> str:
    return setting("CHRONOS_ADMIN_PASSWORD")


def _signing_key() -> bytes:
    secret = setting("CHRONOS_ADMIN_SECRET")
    if not secret:
        # Derived from the password, so tokens stay valid across restarts and workers
        # without a second secret to manage.
        secret = "chronos-admin-token:" + _password()
    return hashlib.sha256(secret.encode()).digest()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def admin_enabled() -> bool:
    return bool(_password())


def password_matches(candidate: str) -> bool:
    expected = _password()
    if not expected or not isinstance(candidate, str):
        return False
    return hmac.compare_digest(expected.encode(), candidate.encode())


def make_token() -> str:
    payload = _b64(json.dumps({"sub": "admin", "exp": int(time.time()) + TOKEN_TTL_SECONDS}).encode())
    signature = _b64(hmac.new(_signing_key(), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{signature}"


def token_valid(token: str) -> bool:
    if not admin_enabled() or not token or "." not in token:
        return False
    payload, _, signature = token.partition(".")
    expected = _b64(hmac.new(_signing_key(), payload.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(expected, signature):
        return False
    try:
        data = json.loads(_unb64(payload))
        return data.get("sub") == "admin" and int(data.get("exp", 0)) > time.time()
    except Exception:
        return False


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def check_login_allowed(request: Request) -> None:
    now = time.time()
    key = _client_key(request)
    recent = [t for t in _failures.get(key, []) if now - t < _FAILURE_WINDOW]
    _failures[key] = recent
    if len(recent) >= _FAILURE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try again later.")


def record_login_failure(request: Request) -> None:
    _failures.setdefault(_client_key(request), []).append(time.time())


def require_admin(authorization: str = Header(default="")) -> None:
    """FastAPI dependency for every protected /api/admin route."""
    if not admin_enabled():
        raise HTTPException(status_code=503, detail="Admin access is not configured on this server.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token_valid(token.strip()):
        raise HTTPException(status_code=401, detail="Admin authentication required.")


# --- leaderboard -----------------------------------------------------------------

def _parse_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).strip().replace(" ", "T"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _team_ids(connection, sql: str) -> set[int]:
    try:
        return {int(r[0]) for r in connection.execute(sql).fetchall()}
    except (sqlite3.OperationalError, ValueError, TypeError):
        return set()  # table not created yet


def _fmt_seconds(seconds: Optional[float]) -> str:
    if seconds is None:
        return "--:--"
    s = int(seconds)
    return f"{s // 60:02d}:{s % 60:02d}"


_AFTER_ROUND2 = {
    "ROUND2COMPLETED", "TIMEOUT", "ROUND3ACTIVE", "DECISIONSUBMITTED", "FINALREVEAL", "COMPLETED",
}


def _state_label(state: str) -> str:
    key = (state or "").replace("_", "").upper()
    if key in {"COMPLETED", "DECISIONSUBMITTED", "FINALREVEAL"}:
        return "FINISHED"
    return state or "READY"


def leaderboard() -> list[dict[str, Any]]:
    connection = get_connection()
    try:
        teams = connection.execute("SELECT * FROM teams ORDER BY id").fetchall()
        r1_recorded_ids = _team_ids(connection, "SELECT DISTINCT team_id FROM round1_submissions")
        r2_recorded_ids = _team_ids(connection, "SELECT DISTINCT team_id FROM round2_submissions")
        r3_recorded_ids = _team_ids(connection, "SELECT DISTINCT team_id FROM round3_submissions")
        ledger: dict[int, tuple[int, float]] = {}
        try:
            for row in connection.execute(
                "SELECT team_id, COUNT(*) AS n, COALESCE(SUM(points_deducted), 0) AS lost "
                "FROM round2_chat_messages GROUP BY team_id"
            ).fetchall():
                ledger[int(row["team_id"])] = (int(row["n"]), float(row["lost"]))
        except (sqlite3.OperationalError, ValueError, TypeError):
            pass  # Round 2 tables not created yet
    finally:
        connection.close()

    entries: list[dict[str, Any]] = []
    for t in teams:
        tid = t["id"]
        r1_done = _parse_ts(t["round1_completed_at"])
        r1_start = _parse_ts(t["round1_started_at"])
        r2_done = _parse_ts(t["round2_completed_at"])
        r3_done = _parse_ts(t["round3_completed_at"])

        r1 = float(t["round1_score"] or 0) if (tid in r1_recorded_ids or r1_done) else None

        questions, lost = ledger.get(tid, (0, 0.0))
        state_key = (t["current_state"] or "").replace("_", "").upper()
        r2_over = bool(r2_done) or state_key in _AFTER_ROUND2
        r2_source = None
        if tid in r2_recorded_ids:                      # legacy culprit-submission score, as recorded
            r2, r2_source = float(t["round2_score"] or 0), "legacy_submission"
        elif t["round2_started_at"]:                    # investigation-only: 20 minus recorded deductions
            r2, r2_source = float(AI_BUDGET) - lost, "ai_deductions"
        else:
            r2 = None
        r3 = float(t["round3_score"] or 0) if tid in r3_recorded_ids else None
        recorded = [v for v in (r1, r2, r3) if v is not None]
        r1_seconds = (r1_done - r1_start).total_seconds() if (r1_done and r1_start) else None

        entries.append({
            "team_id": tid,
            "team_name": t["team_name"],
            "member_1_name": t["member_1_name"] or "",
            "member_2_name": t["member_2_name"] or "",
            "member_1_prn": t["member_1_prn"] or "",
            "member_2_prn": t["member_2_prn"] or "",
            "round1_auth_code": t["round1_auth_code"] or "",
            "current_state": t["current_state"] or "READY",
            "status": _state_label(t["current_state"]),
            "round1_score": r1,
            "round2_score": r2,
            "round3_score": r3,
            "round2_source": r2_source,
            "round2_provisional": r2 is not None and r2_source == "ai_deductions" and not r2_over,
            "round2_questions_used": questions if r2_source else None,
            "round2_points_deducted": lost if r2_source else None,
            "total_score": sum(recorded) if recorded else None,
            "total_complete": len(recorded) == 3,
            "recorded_rounds": [n for n, v in ((1, r1), (2, r2), (3, r3)) if v is not None],
            "r1_started_at": t["round1_started_at"],
            "r1_completed_at": t["round1_completed_at"],
            "r2_completed_at": t["round2_completed_at"],
            "r3_completed_at": t["round3_completed_at"],
            "r1_time_diff": r1_seconds,
            "r1_time_formatted": _fmt_seconds(r1_seconds),
            "_k": (r3_done, r2_done, r1_done),
        })

    far = datetime.max.replace(tzinfo=timezone.utc)

    def sort_key(e):
        total = e["total_score"] if e["total_score"] is not None else float("-inf")
        r3d, r2d, r1d = e["_k"]
        return (-total, r3d or far, r2d or far, r1d or far, e["team_id"])

    entries.sort(key=sort_key)

    previous = None
    for index, entry in enumerate(entries):
        tie_key = sort_key(entry)[:-1]
        entry["rank"] = entries[index - 1]["rank"] if (previous == tie_key and index) else index + 1
        previous = tie_key
        del entry["_k"]
    return entries


def _csv_cell(value: Any) -> Any:
    """Neutralise spreadsheet formulas in user-supplied text."""
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def leaderboard_csv() -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Rank", "Team Name", "Member 1", "Member 1 PRN", "Member 2", "Member 2 PRN",
        "State", "Round 1 Score", "Round 1 Time", "Round 2 Score", "Round 3 Score",
        "Round 2 AI Questions Used", "Round 2 Provisional",
        "Total (recorded rounds)", "All rounds recorded", "Round 3 Completed At",
    ])
    for t in leaderboard():
        writer.writerow([_csv_cell(v) for v in (
            t["rank"], t["team_name"], t["member_1_name"], t["member_1_prn"],
            t["member_2_name"], t["member_2_prn"], t["status"],
            "" if t["round1_score"] is None else t["round1_score"], t["r1_time_formatted"],
            "" if t["round2_score"] is None else t["round2_score"],
            "" if t["round3_score"] is None else t["round3_score"],
            "" if t["round2_questions_used"] is None else t["round2_questions_used"],
            "yes" if t["round2_provisional"] else "no",
            "" if t["total_score"] is None else t["total_score"],
            "yes" if t["total_complete"] else "no", t["r3_completed_at"] or "",
        )])
    return output.getvalue()


def recent_logs(limit: int) -> list[dict[str, Any]]:
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT l.id, l.team_id, t.team_name, l.event_type, l.event_data, l.created_at "
            "FROM game_logs l LEFT JOIN teams t ON l.team_id = t.id "
            "ORDER BY l.id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        connection.close()
