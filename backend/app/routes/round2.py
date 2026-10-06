"""
Project Chronos — Round 2 API Routes
FastAPI endpoints for Round 2: CHRONOS Terminal Investigation.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from ..services.round2_service import Round2Service

router = APIRouter(prefix="/api/round2", tags=["Round 2: CHRONOS Terminal"])


class Round2ChatRequest(BaseModel):
    team_id: int
    user_prompt: str = Field(..., description="Participant investigation query")


@router.get("/files")
def get_files(team_id: Optional[int] = Query(None, description="Optional team ID for team-specific unlocks")):
    return Round2Service.get_files(team_id=team_id)


@router.get("/files/{file_id}")
def get_file(file_id: str, team_id: Optional[int] = Query(None)):
    file_item = Round2Service.get_file_by_id(file_id=file_id, team_id=team_id)
    if file_item is None:
        raise HTTPException(
            status_code=404,
            detail="File not found or access denied"
        )
    return file_item


@router.post("/chat")
def ask_ai(payload: Round2ChatRequest):
    result = Round2Service.ask_ai(team_id=payload.team_id, user_prompt=payload.user_prompt)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result
