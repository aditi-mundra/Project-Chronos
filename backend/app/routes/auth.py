"""
Project Chronos — Authentication & Team Registration Routes
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from ..database.connection import get_connection
from ..utils.timers import get_utc_now_iso

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    team_name: str = Field(..., description="Unique Team Name")
    member_1_name: str = Field(..., description="Name of Team Member 1")
    member_2_name: str = Field(..., description="Name of Team Member 2")
    member_1_prn: Optional[str] = Field("", description="PRN of Member 1")
    member_2_prn: Optional[str] = Field("", description="PRN of Member 2")

@router.post("/login", summary="Register or Login Team")
def login(payload: LoginRequest):
    """
    Creates a new team or logs in an existing team by team_name.
    Returns team credentials, team_id, and current_state.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM teams WHERE team_name = ?", (payload.team_name.strip(),))
        existing_team = cursor.fetchone()
        
        now_iso = get_utc_now_iso()
        
        if existing_team:
            return {
                "status": "success",
                "team_id": existing_team["id"],
                "team_name": existing_team["team_name"],
                "member_1_name": existing_team["member_1_name"],
                "member_2_name": existing_team["member_2_name"],
                "member_1_prn": existing_team["member_1_prn"],
                "member_2_prn": existing_team["member_2_prn"],
                "current_state": existing_team["current_state"] or "READY",
                "total_score": existing_team["total_score"],
                "round1_score": existing_team["round1_score"],
                "round2_score": existing_team["round2_score"],
                "round3_score": existing_team["round3_score"]
            }
        
        # Insert new team
        cursor.execute("""
            INSERT INTO teams (
                team_name,
                member_1_name,
                member_2_name,
                member_1_prn,
                member_2_prn,
                current_state,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, 'READY', 'ACTIVE', ?, ?)
        """, (
            payload.team_name.strip(),
            payload.member_1_name.strip(),
            payload.member_2_name.strip(),
            payload.member_1_prn.strip() if payload.member_1_prn else "",
            payload.member_2_prn.strip() if payload.member_2_prn else "",
            now_iso,
            now_iso
        ))
        
        team_id = cursor.lastrowid
        
        # Log login event
        cursor.execute("""
            INSERT INTO game_logs (team_id, event_type, event_data, created_at)
            VALUES (?, 'LOGIN', ?, ?)
        """, (team_id, '{"action": "TEAM_REGISTERED"}', now_iso))
        
        connection.commit()
        
        return {
            "status": "success",
            "team_id": team_id,
            "team_name": payload.team_name.strip(),
            "member_1_name": payload.member_1_name.strip(),
            "member_2_name": payload.member_2_name.strip(),
            "member_1_prn": payload.member_1_prn.strip() if payload.member_1_prn else "",
            "member_2_prn": payload.member_2_prn.strip() if payload.member_2_prn else "",
            "current_state": "READY",
            "total_score": 0,
            "round1_score": 0,
            "round2_score": 0,
            "round3_score": 0
        }
    finally:
        connection.close()
