"""
Project Chronos — Cumulative Scoring Service
Calculates and updates cumulative team scores across Round 1, Round 2, and Round 3.
"""

from typing import Dict, Any
from ..database.connection import get_connection

class ScoringService:
    @staticmethod
    def recalculate_total_score(team_id: int) -> int:
        """
        Atomically aggregates round1_score, round2_score, and round3_score
        and persists total_score in the master teams table.
        """
        from ..database.queries import update_team_scores
        connection = get_connection()
        try:
            update_team_scores(connection, team_id)
            cursor = connection.cursor()
            cursor.execute("SELECT total_score FROM teams WHERE id = ?", (team_id,))
            row = cursor.fetchone()
            return row["total_score"] if row else 0
        finally:
            connection.close()
