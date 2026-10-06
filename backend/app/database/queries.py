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
    """
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE teams
        SET total_score = ROUND(
                COALESCE(r1_score, round1_score, 0.0) +
                COALESCE(r2_score, round2_score, 0.0) +
                COALESCE(r3_score, round3_score, 0.0),
                2
            ),
            r1_score = COALESCE(r1_score, round1_score, 0.0),
            round1_score = COALESCE(round1_score, r1_score, 0.0),
            r2_score = COALESCE(r2_score, round2_score, 0.0),
            round2_score = COALESCE(round2_score, r2_score, 0.0),
            r3_score = COALESCE(r3_score, round3_score, 0.0),
            round3_score = COALESCE(round3_score, r3_score, 0.0),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (team_id,))
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
            total_score = ROUND(
                ? + COALESCE(r2_score, round2_score, 0.0) + COALESCE(r3_score, round3_score, 0.0),
                2
            ),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        start_iso, start_iso,
        end_iso, end_iso,
        round(time_diff, 2),
        r1_score, r1_score,
        r1_score,
        team_id
    ))
    connection.commit()
