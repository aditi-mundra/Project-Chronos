"""
Tester shortcut: skip the team's current stage with 0 points.

Reachable only while it is switched on: from the admin leaderboard (master password), or by
CHRONOS_ENABLE_SKIP=1 as the default; otherwise the route answers 404 as if it did not exist. It is meant for rehearsal and
testing. LEAVE IT OFF FOR THE REAL EVENT: with it on, any logged-in team could skip rounds.

One call skips ONE stage, in order:

  Round 1 (not started / running)  -> Round 1 finished, 0 points
  Transition round                  -> transition finished, 0 points
  Round 2 (not started / running)   -> Round 2 finished (lobby), 0 points
  Round 2 lobby / Round 3           -> Round 3 filed with no accusation, 0 points, event complete

The skipped stage is recorded exactly like a real result (so the leaderboard shows 0, not
"unknown") and a DEV_SKIP event is written to the game log.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from fastapi import HTTPException

from ..config import setting
from ..database.connection import get_connection
from . import round2_service, round3_service
from .round1_service import generate_auth_code

ROUND1_DONE = "ROUND1_COMPLETED"


_TRUE = {"1", "true", "yes", "on"}


def _table(connection) -> None:
    connection.execute(
        "CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT)"
    )


def _stored() -> str | None:
    connection = get_connection()
    try:
        _table(connection)
        row = connection.execute("SELECT value FROM app_settings WHERE key = 'dev_skip'").fetchone()
        return row["value"] if row else None
    except sqlite3.Error:
        return None
    finally:
        connection.close()


def enabled() -> bool:
    """The admin leaderboard switch (stored in the database) wins; with no switch set, the
    CHRONOS_ENABLE_SKIP environment / .env value is the default (off when unset)."""
    stored = _stored()
    if stored is not None:
        return stored.strip().lower() in _TRUE
    return setting("CHRONOS_ENABLE_SKIP").strip().lower() in _TRUE


def set_enabled(value: bool) -> dict:
    connection = get_connection()
    try:
        _table(connection)
        connection.execute(
            "INSERT INTO app_settings (key, value, updated_at) VALUES ('dev_skip', ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            ("1" if value else "0", _now()),
        )
        connection.execute(
            "INSERT INTO game_logs (team_id, event_type, event_data, created_at) "
            "VALUES (NULL, 'DEV_SKIP_SWITCH', ?, ?)",
            (json.dumps({"enabled": bool(value)}), _now()),
        )
        connection.commit()
    finally:
        connection.close()
    return {"enabled": enabled()}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(state) -> str:
    return (state or "").replace("_", "").upper()


def _retotal(connection, team_id: int) -> None:
    connection.execute(
        "UPDATE teams SET total_score = COALESCE(round1_score, 0) + COALESCE(transition_score, 0) "
        "+ COALESCE(round2_score, 0) + COALESCE(round3_score, 0) WHERE id = ?",
        (team_id,),
    )


def skip_round(team_id: int) -> dict:
    if not enabled():
        raise HTTPException(status_code=404, detail="Not Found")

    with round3_service._Db() as connection:  # also makes sure the Round 2/3 tables exist
        connection.execute("BEGIN IMMEDIATE")
        team = connection.execute("SELECT * FROM teams WHERE id = ?", (team_id,)).fetchone()
        if team is None:
            raise HTTPException(status_code=404, detail="Team not found.")
        tid = team["id"]
        state = _norm(team["current_state"])
        now = _now()
        skipped = None

        if state in {"", "READY", "LOGGEDIN", "REGISTERED", "ROUND1ACTIVE"}:
            skipped = "round1"
            connection.execute(
                "UPDATE teams SET current_state = ?, round1_score = 0, "
                "round1_started_at = COALESCE(round1_started_at, ?), round1_completed_at = ?, "
                "round1_auth_code = COALESCE(NULLIF(round1_auth_code, ''), ?), updated_at = ? WHERE id = ?",
                (ROUND1_DONE, now, now, generate_auth_code(), now, tid),
            )

        elif state == "ROUND1COMPLETED" and not team["transition_completed_at"]:
            skipped = "transition"
            connection.execute(
                "UPDATE teams SET transition_score = 0, transition_completed_at = ?, updated_at = ? WHERE id = ?",
                (now, now, tid),
            )

        elif state in {"ROUND1COMPLETED", "ROUND2ACTIVE"}:
            skipped = "round2"
            # A recorded "SKIPPED" filing makes every reader (leaderboard included) show 0
            # instead of 20 minus the AI deductions.
            connection.execute("DELETE FROM round2_submissions WHERE team_id = ?", (str(tid),))
            connection.execute(
                "INSERT INTO round2_submissions "
                "(team_id, suspect, is_correct, points_awarded, ai_points_remaining, round2_score, submitted_at) "
                "VALUES (?, 'SKIPPED', 0, 0, 0, 0, ?)",
                (str(tid), now),
            )
            connection.execute(
                "UPDATE teams SET current_state = ?, round2_score = 0, "
                "round2_started_at = COALESCE(round2_started_at, ?), "
                "round2_completed_at = COALESCE(round2_completed_at, ?), updated_at = ? WHERE id = ?",
                (round2_service.COMPLETED_STATE, now, now, now, tid),
            )

        elif state in {"ROUND2COMPLETED", "TIMEOUT", "ROUND3ACTIVE"}:
            skipped = "round3"
            round3_service._assign_case(connection, tid)
            connection.execute(
                "UPDATE teams SET round3_started_at = COALESCE(round3_started_at, ?) WHERE id = ?", (now, tid)
            )
            try:
                connection.execute(
                    "INSERT INTO round3_submissions "
                    "(team_id, selected_candidate_id, selected_evidence_ids, is_correct, points_awarded, submitted_at) "
                    "VALUES (?, 'skipped', '[]', 0, 0, ?)",
                    (tid, now),
                )
            except sqlite3.IntegrityError:
                pass  # already filed
            connection.execute(
                "INSERT INTO submissions (team_id, round, reference_id, answer, is_correct, points_awarded, "
                "submitted_at) VALUES (?, 3, 'skipped', ?, 0, 0, ?)",
                (tid, json.dumps({"skipped": True}), now),
            )
            round3_service._record_result(connection, tid, 0.0, now)

        if skipped:
            _retotal(connection, tid)
            connection.execute(
                "INSERT INTO game_logs (team_id, event_type, event_data, created_at) VALUES (?, 'DEV_SKIP', ?, ?)",
                (tid, json.dumps({"skipped": skipped, "from_state": team["current_state"], "points": 0}), now),
            )

        new_state = connection.execute(
            "SELECT current_state FROM teams WHERE id = ?", (tid,)
        ).fetchone()["current_state"]
        return {"skipped": skipped, "points": 0, "current_state": new_state}
