"""
Round 3: final decision (wisdom round).

The backend owns everything that matters:

  * entry gate     Round 3 starts only after the team's Round 2 has ended (completed,
                   timed out or out of time). Nothing about Round 2 scoring is needed.
  * the case       one of three canonical cases, chosen from the team id and stored
                   per team the first time Round 3 starts.
  * the answer     the culprit and the valid evidence stay in the database. No player
                   endpoint returns them; the debrief shows the narrative only after
                   the team's own decision is locked in.
  * the decision   one accusation per team, at least two known evidence items, and a
                   candidate that belongs to the team's case. A second attempt never
                   changes the first result.

Tables are created on first use (see ensure_tables), so the shared schema file does
not change. Scoring is kept in _record_result() so it can be revised later without
touching gameplay.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from fastapi import HTTPException

from ..data.round3_cases import (
    ROUND_3_CANONICAL_CASES,
    get_case_for_team,
    get_sanitized_case_for_client,
)
from ..database.connection import get_connection
from . import round2_service

ACTIVE_STATE = "ROUND_3_ACTIVE"
FINAL_STATE = "COMPLETED"

CORRECT_POINTS = 10       # event scoring: correct lock-in +10, wrong 0; nothing else changes it
MIN_EVIDENCE = 2
MAX_EVIDENCE = 12

_SUBMITTED_STATES = {"DECISIONSUBMITTED", "FINALREVEAL", "COMPLETED"}


def _norm(state) -> str:
    return (state or "").replace("_", "").upper()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail=message, headers={"X-Error-Code": code})


# --- tables ------------------------------------------------------------------

def ensure_tables(connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS round3_team_cases (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id               INTEGER NOT NULL UNIQUE,
            case_id               TEXT NOT NULL,
            case_data             TEXT NOT NULL DEFAULT '{}',
            culprit_candidate_id  TEXT NOT NULL DEFAULT '',
            valid_evidence_ids    TEXT NOT NULL DEFAULT '[]',
            status                TEXT DEFAULT 'PENDING',
            assigned_at           TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS round3_submissions (
            id                     INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id                INTEGER NOT NULL UNIQUE,
            selected_candidate_id  TEXT NOT NULL,
            selected_evidence_ids  TEXT NOT NULL,
            is_correct             INTEGER NOT NULL,
            points_awarded         REAL NOT NULL,
            submitted_at           TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
        );
        """
    )
    _migrate_legacy_tables(connection)
    connection.commit()


def _migrate_legacy_tables(connection) -> None:
    """Idempotent upgrade of Round 3 tables created by earlier builds of the Round 3
    source (it created round3_team_cases without case_data / culprit_candidate_id,
    and without a unique team_id)."""
    columns = {r["name"] for r in connection.execute("PRAGMA table_info(round3_team_cases)")}
    wanted = {
        "case_data": "TEXT NOT NULL DEFAULT '{}'",
        "culprit_candidate_id": "TEXT NOT NULL DEFAULT ''",
        "valid_evidence_ids": "TEXT NOT NULL DEFAULT '[]'",
    }
    for column, ddl in wanted.items():
        if column not in columns:
            connection.execute(f"ALTER TABLE round3_team_cases ADD COLUMN {column} {ddl}")

    # Older tables had no uniqueness on team_id. Add it only when it is safe to.
    for table in ("round3_team_cases", "round3_submissions"):
        try:
            connection.execute(
                f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{table}_team ON {table}(team_id)"
            )
        except sqlite3.IntegrityError:
            pass  # legacy duplicates: the service still reads the newest row only


_ready = set()


def _prepare(connection) -> None:
    key = str(connection.execute("PRAGMA database_list").fetchone()[2])
    if key not in _ready:
        ensure_tables(connection)
        _ready.add(key)


def init_round3() -> None:
    connection = get_connection()
    try:
        _prepare(connection)
    finally:
        connection.close()


class _Db:
    def __enter__(self):
        self.connection = get_connection()
        try:
            _prepare(self.connection)
        except Exception:
            self.connection.close()
            raise
        return self.connection

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.connection.close()


# --- helpers -------------------------------------------------------------------

def _log(connection, team_id, event_type, data) -> None:
    connection.execute(
        "INSERT INTO game_logs (team_id, event_type, event_data, created_at) VALUES (?, ?, ?, ?)",
        (team_id, event_type, json.dumps(data), _now_iso()),
    )


def _team(connection, team_id):
    row = connection.execute("SELECT * FROM teams WHERE id = ?", (int(team_id),)).fetchone()
    if row is None:
        raise _error(404, "TEAM_NOT_FOUND", "Team not found.")
    return row


def _submission(connection, team_id):
    return connection.execute(
        "SELECT * FROM round3_submissions WHERE team_id = ? ORDER BY id DESC LIMIT 1", (team_id,)
    ).fetchone()


def _assigned_case(connection, team_id):
    return connection.execute(
        "SELECT * FROM round3_team_cases WHERE team_id = ? ORDER BY id DESC LIMIT 1", (team_id,)
    ).fetchone()


def _assign_case(connection, team_id):
    """The team's stored case; created from the canonical catalog on first use."""
    row = _assigned_case(connection, team_id)
    if row is not None and row["culprit_candidate_id"]:
        return row

    # The Round 3 case is the one that matches the team's own Round 2 case.
    try:
        r2 = connection.execute(
            "SELECT case_id FROM round2_team_cases WHERE team_id = ?", (team_id,)
        ).fetchone()
    except sqlite3.OperationalError:
        r2 = None  # Round 2 tables not created yet
    full = get_case_for_team(team_id, r2["case_id"] if r2 else None)
    sanitized = get_sanitized_case_for_client(full)
    connection.execute(
        "INSERT OR REPLACE INTO round3_team_cases "
        "(id, team_id, case_id, case_data, culprit_candidate_id, valid_evidence_ids, status, assigned_at) "
        "VALUES ((SELECT id FROM round3_team_cases WHERE team_id = ?), ?, ?, ?, ?, ?, 'ASSIGNED', ?)",
        (
            team_id, team_id, full["case_id"], json.dumps(sanitized),
            full["culprit_candidate_id"], json.dumps(full["valid_evidence_ids"]), _now_iso(),
        ),
    )
    return _assigned_case(connection, team_id)


def _client_scenario(row) -> dict:
    """The case as players may see it: no culprit, no valid-evidence list, no narrative."""
    case = json.loads(row["case_data"] or "{}")
    for secret in ("culprit_candidate_id", "valid_evidence_ids", "narrative_summary"):
        case.pop(secret, None)
    # The evidence panel reads `evidence_archive`.
    if "evidence_pool" in case:
        case["evidence_archive"] = case.pop("evidence_pool")
    return case


def _canonical_case(case_id: str):
    return next((c for c in ROUND_3_CANONICAL_CASES if c["case_id"] == case_id), None)


def _state_payload(team, row, submission) -> dict:
    return {
        "status": "success",
        "team_id": team["id"],
        "team_name": team["team_name"],
        "team_state": team["current_state"],
        "round3_started_at": team["round3_started_at"],
        "is_submitted": submission is not None,
        "scenario": _client_scenario(row) if row is not None else None,
    }


def _is_submitted(team, submission) -> bool:
    return submission is not None or _norm(team["current_state"]) in _SUBMITTED_STATES


# --- entry gate ----------------------------------------------------------------

def _eligibility(team, submission) -> tuple[bool, str]:
    state = _norm(team["current_state"])
    if _is_submitted(team, submission):
        return False, "ALREADY_SUBMITTED"
    if state == _norm(ACTIVE_STATE):
        return True, "ACTIVE"
    if round2_service.round2_is_over(team):
        return True, "ROUND_2_FINISHED"
    return False, "ROUND_2_NOT_FINISHED"


def get_availability(team_id) -> dict:
    with _Db() as connection:
        team = _team(connection, team_id)
        submission = _submission(connection, team["id"])
        eligible, reason = _eligibility(team, submission)
        return {
            "team_id": team["id"],
            "eligible": eligible,
            "reason": reason,
            "state": team["current_state"],
            "started": bool(team["round3_started_at"]),
            "submitted": _is_submitted(team, submission),
        }


# --- start / scenario ----------------------------------------------------------

def start_round3(team_id) -> dict:
    """The Lobby's START ROUND 3 button. Safe to repeat: a second call returns the
    same assignment and never restarts anything."""
    with _Db() as connection:
        team = _team(connection, team_id)
        tid = team["id"]
        submission = _submission(connection, tid)

        if _is_submitted(team, submission):
            return _state_payload(team, _assigned_case(connection, tid), submission)

        eligible, reason = _eligibility(team, submission)
        if not eligible:
            raise _error(
                409, reason,
                "Round 2 must be finished before Round 3 can begin.",
            )

        row = _assign_case(connection, tid)

        if _norm(team["current_state"]) != _norm(ACTIVE_STATE) or not team["round3_started_at"]:
            now = _now_iso()
            connection.execute(
                "UPDATE teams SET current_state = ?, round3_started_at = COALESCE(round3_started_at, ?), "
                "updated_at = ? WHERE id = ?",
                (ACTIVE_STATE, now, now, tid),
            )
            _log(connection, tid, "R3_START", {"round": 3, "case": row["case_id"], "from": reason})
            team = _team(connection, tid)

        return _state_payload(team, row, None)


def get_scenario(team_id) -> dict:
    """Read-only: the team's case after Round 3 has been started with the button.
    It never starts Round 3 itself."""
    with _Db() as connection:
        team = _team(connection, team_id)
        tid = team["id"]
        submission = _submission(connection, tid)
        row = _assigned_case(connection, tid)

        if submission is None and (
            _norm(team["current_state"]) != _norm(ACTIVE_STATE) or row is None
        ):
            raise _error(409, "ROUND_3_NOT_STARTED", "Round 3 has not been started for this team.")

        return _state_payload(team, row, submission)


# --- decision ------------------------------------------------------------------

def _record_result(connection, team_id, points: float, completed_at: str) -> None:
    """Persist the Round 3 result. This is the only place Round 3 touches scores."""
    connection.execute(
        "UPDATE teams SET round3_score = ?, "
        "total_score = COALESCE(round1_score, 0) + COALESCE(round2_score, 0) + ?, "
        "round3_completed_at = ?, current_state = ?, updated_at = ? WHERE id = ?",
        (points, points, completed_at, FINAL_STATE, completed_at, team_id),
    )


def _clean_evidence(evidence_ids) -> list[str]:
    if evidence_ids is None:
        evidence_ids = []
    if not isinstance(evidence_ids, list):
        raise _error(422, "INVALID_EVIDENCE", "Evidence must be a list of evidence IDs.")
    seen: list[str] = []
    for item in evidence_ids:
        if not isinstance(item, str) or not item.strip():
            raise _error(422, "INVALID_EVIDENCE", "Evidence IDs must be non-empty strings.")
        value = item.strip()
        if value not in seen:
            seen.append(value)
    if len(seen) > MAX_EVIDENCE:
        raise _error(422, "INVALID_EVIDENCE", "Too many evidence items were submitted.")
    return seen


def submit_decision(team_id, candidate_id, evidence_ids) -> dict:
    candidate = (candidate_id or "").strip().lower() if isinstance(candidate_id, str) else ""
    if not candidate:
        raise _error(422, "MISSING_CANDIDATE", "A suspect must be selected.")
    evidence = _clean_evidence(evidence_ids)

    with _Db() as connection:
        connection.execute("BEGIN IMMEDIATE")  # one decision per team, even under double clicks
        team = _team(connection, team_id)
        tid = team["id"]

        existing = _submission(connection, tid)
        if existing is not None:
            return _submit_response(already=True)

        if _norm(team["current_state"]) != _norm(ACTIVE_STATE):
            raise _error(409, "ROUND_3_NOT_STARTED", "Round 3 has not been started for this team.")
        row = _assigned_case(connection, tid)
        if row is None or not row["culprit_candidate_id"]:
            raise _error(409, "ROUND_3_NOT_STARTED", "Round 3 has not been started for this team.")

        scenario = _client_scenario(row)
        candidate_ids = {c["id"] for c in scenario.get("candidates", [])}
        known_evidence = {e["id"] for e in scenario.get("evidence_archive", [])}

        if candidate not in candidate_ids:
            raise _error(422, "INVALID_CANDIDATE", "That suspect is not part of this case.")
        if any(e not in known_evidence for e in evidence):
            raise _error(422, "INVALID_EVIDENCE", "One or more evidence items are not part of this case.")
        if len(evidence) < MIN_EVIDENCE:
            raise _error(
                422, "INVALID_EVIDENCE_COUNT",
                f"Select at least {MIN_EVIDENCE} evidence items to support the accusation.",
            )

        correct = candidate == row["culprit_candidate_id"].strip().lower()
        points = float(CORRECT_POINTS if correct else 0)
        now = _now_iso()

        try:
            connection.execute(
                "INSERT INTO round3_submissions "
                "(team_id, selected_candidate_id, selected_evidence_ids, is_correct, points_awarded, submitted_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (tid, candidate, json.dumps(evidence), int(correct), points, now),
            )
        except sqlite3.IntegrityError:
            return _submit_response(already=True)

        connection.execute(
            "INSERT INTO submissions (team_id, round, reference_id, answer, is_correct, points_awarded, submitted_at) "
            "VALUES (?, 3, ?, ?, ?, ?, ?)",
            (tid, candidate, json.dumps({"candidate_id": candidate, "evidence_ids": evidence}),
             int(correct), points, now),
        )
        _record_result(connection, tid, points, now)
        _log(connection, tid, "R3_SUBMIT", {
            "round": 3, "case": row["case_id"], "candidate": candidate,
            "evidence_count": len(evidence), "correct": correct,
        })
        return _submit_response(already=False)


def _submit_response(already: bool) -> dict:
    # Deliberately no correctness or points: players are not told how they did.
    return {
        "status": "success",
        "submitted": True,
        "already_submitted": already,
        "next_state": FINAL_STATE,
    }


# --- debrief -------------------------------------------------------------------

def get_verdict(team_id) -> dict:
    """The completion screen: what the team filed plus the narrative resolution.
    Available only once this team's own decision is locked in; never returns
    correctness, points or scores."""
    with _Db() as connection:
        team = _team(connection, team_id)
        tid = team["id"]
        submission = _submission(connection, tid)
        if submission is None:
            raise _error(409, "NO_DECISION", "No decision has been submitted for Round 3 yet.")

        row = _assigned_case(connection, tid)
        canonical = _canonical_case(row["case_id"]) if row else None
        candidates = (canonical or {}).get("candidates", [])
        picked = next((c for c in candidates if c["id"] == submission["selected_candidate_id"]), None)

        return {
            "status": "success",
            "team_id": tid,
            "team_name": team["team_name"],
            "current_state": team["current_state"],
            "submission": {
                "selected_candidate_id": submission["selected_candidate_id"],
                "selected_candidate_name": picked["name"] if picked else submission["selected_candidate_id"],
                "selected_evidence_ids": json.loads(submission["selected_evidence_ids"] or "[]"),
                "submitted_at": submission["submitted_at"],
            },
            "verdict_details": {
                "narrative_summary": (canonical or {}).get("narrative_summary", ""),
            },
        }
