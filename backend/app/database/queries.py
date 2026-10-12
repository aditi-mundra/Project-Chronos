"""
Project Chronos — Database Query Helpers & Automatic Score Synchronization
Documented in docs/database.md Section 5.
"""

import sqlite3
from datetime import datetime
from typing import Optional


def update_team_scores(connection: sqlite3.Connection, team_id: int):
    """
    Recomputes total_score and synchronizes both legacy and database.md column names
    (r1_score/round1_score, r2_score/round2_score, r3_score/round3_score, total_score).
    Accurately sums Round 1 (including negative values) + Round 2 + Round 3.
    """
    cursor = connection.cursor()
    cursor.execute("""
        SELECT 
            round1_score, r1_score,
            round2_score, r2_score,
            round3_score, r3_score,
            transition_score
        FROM teams
        WHERE id = ?
    """, (team_id,))
    row = cursor.fetchone()
    if not row:
        return

    def resolve_score(primary, alias):
        p = float(primary) if primary is not None else None
        a = float(alias) if alias is not None else None
        if p is not None and p != 0.0:
            return p
        if a is not None and a != 0.0:
            return a
        if p is not None:
            return p
        if a is not None:
            return a
        return 0.0

    s1 = resolve_score(row["round1_score"], row["r1_score"])
    s2 = resolve_score(row["round2_score"], row["r2_score"])
    s3 = resolve_score(row["round3_score"], row["r3_score"])
    s_trans = 0.0
    try:
        s_trans = float(row["transition_score"]) if row["transition_score"] is not None else 0.0
    except Exception:
        pass

    # Enforce authoritative grading system:
    # Round 1: 50 maximum, -25 minimum
    # Lobby / Transition: 20 maximum, 0 minimum
    # Round 2: 20 maximum, 0 minimum
    # Round 3: 10 maximum, 0 minimum
    s1 = max(-25.0, min(50.0, s1))
    s_trans = max(0.0, min(20.0, s_trans))
    s2 = max(0.0, min(20.0, s2))
    s3 = max(0.0, min(10.0, s3))
    total = round(s1 + s_trans + s2 + s3, 2)

    cursor.execute("""
        UPDATE teams
        SET round1_score = ?,
            r1_score = ?,
            r1_scaled = ?,
            transition_score = ?,
            round2_score = ?,
            r2_score = ?,
            round3_score = ?,
            r3_score = ?,
            total_score = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (s1, s1, s1, s_trans, s2, s2, s3, s3, total, team_id))
    connection.commit()


def record_round1_completion(
    connection: sqlite3.Connection,
    team_id: int,
    r1_score: float,
    start_time: datetime,
    end_time: datetime
):
    """
    Computes duration in seconds and updates Round 1 metrics across both schema column sets.
    """
    r1_score = max(-25.0, min(50.0, float(r1_score)))
    time_diff = (end_time - start_time).total_seconds()
    start_iso = start_time.isoformat()
    end_iso = end_time.isoformat()
    
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE teams
        SET r1_start_time = ?,
            round1_started_at = COALESCE(round1_started_at, ?),
            r1_end_time = ?,
            round1_completed_at = ?,
            r1_time_diff = ?,
            r1_score = ?,
            round1_score = ?,
            r1_scaled = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        start_iso, start_iso,
        end_iso, end_iso,
        round(time_diff, 2),
        r1_score, r1_score, r1_score,
        team_id
    ))
    connection.commit()
    update_team_scores(connection, team_id)

