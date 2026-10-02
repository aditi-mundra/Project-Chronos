"""
Project Chronos — Admin Routes
Provides endpoints for Administrator Leaderboard, Telemetry Logs, and Team Inspection.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ..database.connection import get_connection

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])

@router.get("/leaderboard", summary="Get Live Admin Leaderboard")
def get_leaderboard():
    """
    Returns sorted teams by total_score DESC, then round3_completed_at ASC for tie-breaking.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
                id as team_id,
                team_name,
                member_1_name,
                member_2_name,
                member_1_prn,
                member_2_prn,
                round1_score,
                round2_score,
                round3_score,
                total_score,
                round3_completed_at,
                current_state,
                status
            FROM teams
            ORDER BY total_score DESC, 
                     CASE WHEN round3_completed_at IS NULL THEN 1 ELSE 0 END, 
                     round3_completed_at ASC,
                     id ASC
        """)
        rows = cursor.fetchall()
        
        leaderboard = []
        for idx, row in enumerate(rows):
            leaderboard.append({
                "rank": idx + 1,
                "team_id": row["team_id"],
                "team_name": row["team_name"],
                "member_1_name": row["member_1_name"],
                "member_2_name": row["member_2_name"],
                "member_1_prn": row["member_1_prn"],
                "member_2_prn": row["member_2_prn"],
                "round1_score": row["round1_score"] or 0,
                "round2_score": row["round2_score"] or 0,
                "round3_score": row["round3_score"] or 0,
                "total_score": row["total_score"] or 0,
                "round3_completed_at": row["round3_completed_at"],
                "current_state": row["current_state"],
                "status": row["status"]
            })
        return {"count": len(leaderboard), "leaderboard": leaderboard}
    finally:
        connection.close()

@router.get("/logs", summary="Get Game Telemetry Logs")
def get_logs(limit: int = 100):
    """Returns recent audit logs."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT g.id, g.team_id, t.team_name, g.event_type, g.event_data, g.created_at
            FROM game_logs g
            LEFT JOIN teams t ON g.team_id = t.id
            ORDER BY g.id DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        logs = [dict(r) for r in rows]
        return {"logs": logs}
    finally:
        connection.close()
