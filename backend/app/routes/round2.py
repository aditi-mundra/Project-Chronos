"""
Project Chronos — Round 2 API Routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..services.round2_service import Round2Service

router = APIRouter(prefix="/api/round2", tags=["Round 2: CHRONOS Terminal"])

class Round2ChatRequest(BaseModel):
    team_id: int
    user_prompt: str = Field(..., description="Participant investigation query")

@router.get("/files")
def get_files():
    return {"files": Round2Service.get_files()}

@router.post("/chat")
def ask_ai(payload: Round2ChatRequest):
    result = Round2Service.ask_ai(team_id=payload.team_id, user_prompt=payload.user_prompt)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result
