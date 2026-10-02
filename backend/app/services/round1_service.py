"""
Project Chronos — Round 1 Service
Manages puzzle items, era classifications (PAST/PRESENT/FUTURE), and score calculation.
"""

from typing import Dict, Any, List
from ..database.connection import get_connection

class Round1Service:
    @staticmethod
    def get_items() -> List[Dict[str, Any]]:
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT item_id, item_name, image_path, clue_text FROM round1_items WHERE is_active = 1")
            return [dict(r) for r in cursor.fetchall()]
        finally:
            connection.close()

    @staticmethod
    def submit_classification(team_id: int, item_id: int, selected_era: str) -> Dict[str, Any]:
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT correct_era, points_positive, points_negative FROM round1_items WHERE item_id = ?", (item_id,))
            item = cursor.fetchone()
            if not item:
                return {"status": "error", "message": "Item not found"}
            
            is_correct = (item["correct_era"] == selected_era.upper())
            points = item["points_positive"] if is_correct else -item["points_negative"]

            cursor.execute("""
                INSERT INTO round1_submissions (team_id, item_id, selected_era, is_correct, points_awarded)
                VALUES (?, ?, ?, ?, ?)
            """, (team_id, item_id, selected_era.upper(), 1 if is_correct else 0, points))

            # Update team score
            cursor.execute("UPDATE teams SET round1_score = round1_score + ? WHERE id = ?", (points, team_id))
            connection.commit()

            return {
                "status": "success",
                "is_correct": is_correct,
                "points_awarded": points
            }
        finally:
            connection.close()
