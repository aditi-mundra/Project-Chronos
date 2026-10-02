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
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT round1_score, round2_score, round3_score FROM teams WHERE id = ?", (team_id,))
            row = cursor.fetchone()
            if not row:
                return 0
            
            r1 = row["round1_score"] or 0
            r2 = row["round2_score"] or 0
            r3 = row["round3_score"] or 0
            total = r1 + r2 + r3

            cursor.execute("""
                UPDATE teams
                SET total_score = ?,
                    updated_at = (datetime('now'))
                WHERE id = ?
            """, (total, team_id))
            connection.commit()
            return total
        finally:
            connection.close()
