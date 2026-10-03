"""
Project Chronos — Round 1 API Routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..services.round1_service import Round1Service

router = APIRouter(prefix="/api/round1", tags=["Round 1: Timeline Fragmentation"])

class Round1SubmitRequest(BaseModel):
    team_id: int
    item_id: int
    selected_era: str = Field(..., description="PAST, PRESENT, or FUTURE")

@router.get("/items")
def get_items():
    return {"items": Round1Service.get_items()}

@router.post("/submit")
def submit_classification(payload: Round1SubmitRequest):
    result = Round1Service.submit_classification(
        team_id=payload.team_id,
        item_id=payload.item_id,
        selected_era=payload.selected_era
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result
