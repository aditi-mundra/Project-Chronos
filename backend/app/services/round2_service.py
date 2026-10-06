"""
Project Chronos — Round 2 Service
Manages digital investigation files (Alpha, Beta, Gamma), restricted AI chat, and culprit submissions.
"""

from typing import Dict, Any, List, Optional
from ..database.connection import get_connection
from .gemini_service import GeminiService


class Round2Service:
    @staticmethod
    def get_files(team_id: Optional[int] = None) -> List[Dict[str, Any]]:
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT file_id, project_name, timeline_tag, filename, content_text, is_locked 
                FROM round2_files 
                WHERE is_locked = 0
                ORDER BY file_id
            """)
            rows = cursor.fetchall()
            if not rows:
                return [
                    {
                        "file_id": "alpha",
                        "project_name": "Project Alpha",
                        "timeline_tag": "future",
                        "filename": "future_audit.log",
                        "content_text": "21:11:04 UTC — Future timeline configuration modified. Parameter rewrite executed on Terminal Node Gamma-7.",
                        "is_locked": 0
                    },
                    {
                        "file_id": "beta",
                        "project_name": "Project Beta",
                        "timeline_tag": "present",
                        "filename": "incident_report.txt",
                        "content_text": "21:11:18 UTC — Temporal anomaly detected. Chronon frequency spike observed immediately post-override.",
                        "is_locked": 0
                    },
                    {
                        "file_id": "gamma",
                        "project_name": "Project Gamma",
                        "timeline_tag": "past",
                        "filename": "access_history.log",
                        "content_text": "21:10:58 UTC — Biometric key SIGMA-99-0x7F1A authenticated from Sub-Level 4 vault.",
                        "is_locked": 0
                    }
                ]
            return [dict(r) for r in rows]
        finally:
            connection.close()

    @staticmethod
    def get_file_by_id(file_id: str, team_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT file_id, project_name, timeline_tag, filename, content_text, is_locked
                FROM round2_files
                WHERE (file_id = ? OR file_id LIKE ?)
                  AND is_locked = 0
            """, (file_id, f"%{file_id}%"))
            row = cursor.fetchone()
            if row is None:
                return None
            return dict(row)
        finally:
            connection.close()

    @staticmethod
    def ask_ai(team_id: int, user_prompt: str) -> Dict[str, Any]:
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM round2_chat_messages WHERE team_id = ?", (team_id,))
            row = cursor.fetchone()
            count = row["count"] if row else 0
            if count >= 3:
                return {"status": "error", "message": "Maximum 3 AI questions reached."}
            
            deductions = [5.0, 5.0, 10.0]
            pts_deducted = deductions[count] if count < len(deductions) else 10.0

            files = Round2Service.get_files()
            ai_reply = GeminiService.generate_investigation_response(user_prompt, files)

            cursor.execute("""
                INSERT INTO round2_chat_messages (team_id, question_number, user_prompt, ai_response, points_deducted)
                VALUES (?, ?, ?, ?, ?)
            """, (team_id, count + 1, user_prompt, ai_reply, pts_deducted))
            connection.commit()

            return {
                "status": "success",
                "question_number": count + 1,
                "ai_response": ai_reply,
                "points_deducted": pts_deducted,
                "remaining_questions": 3 - (count + 1)
            }
        finally:
            connection.close()


def get_round2_files() -> List[Dict[str, Any]]:
    return Round2Service.get_files()


def get_files_for_team(team_id: Optional[int] = None) -> List[Dict[str, Any]]:
    return Round2Service.get_files(team_id=team_id)


def get_file_by_id(file_id: str, team_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    return Round2Service.get_file_by_id(file_id=file_id, team_id=team_id)

