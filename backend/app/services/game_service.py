"""
Project Chronos — Master Game State Service
Manages cross-round state transitions, score calculations, and continuity.
"""

from typing import Dict, Any, Optional
from ..database.connection import get_connection
from ..utils.timers import get_utc_now_iso

class GameService:
    @staticmethod
    def get_team_state(team_id: int) -> Dict[str, Any]:
        """Fetches full state snapshot for a team."""
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
            team = cursor.fetchone()
            if not team:
                raise ValueError(f"Team {team_id} not found")
            
            return {
                "team_id": team["id"],
                "team_name": team["team_name"],
                "member_1_name": team["member_1_name"],
                "member_2_name": team["member_2_name"],
                "member_1_prn": team["member_1_prn"],
                "member_2_prn": team["member_2_prn"],
                "current_state": team["current_state"],
                "status": team["status"],
                "round1_score": team["round1_score"] or 0,
                "round2_score": team["round2_score"] or 0,
                "round3_score": team["round3_score"] or 0,
                "total_score": team["total_score"] or 0,
                "round1_started_at": team["round1_started_at"],
                "round1_completed_at": team["round1_completed_at"],
                "round2_started_at": team["round2_started_at"],
                "round2_completed_at": team["round2_completed_at"],
                "round3_started_at": team["round3_started_at"],
                "round3_completed_at": team["round3_completed_at"],
            }
        finally:
            connection.close()

    @staticmethod
    def transition_state(team_id: int, target_state: str) -> Dict[str, Any]:
        """Updates team state."""
        connection = get_connection()
        try:
            cursor = connection.cursor()
            now_iso = get_utc_now_iso()
            cursor.execute("""
                UPDATE teams
                SET current_state = ?,
                    updated_at = ?
                WHERE id = ?
            """, (target_state, now_iso, team_id))
            connection.commit()
            return GameService.get_team_state(team_id)
        finally:
            connection.close()
