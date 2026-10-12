from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..services import transition_service as svc

router = APIRouter(prefix="/api/transition", tags=["Transition Round"])


class TeamIdPayload(BaseModel):
    team_id: int


class VerifyPasswordPayload(BaseModel):
    team_id: int
    password: str


@router.get("/info")
def get_info(team_id: int):
    """
    Get transition round details for a team:
    - Assigned Zone (Past, Present, or Future, with 6-team 2-per-zone guarantee)
    - Clue from docs/clues.md
    - Destination
    - Round 1 Auth Code
    - Stopwatch status & elapsed seconds
    """
    res = svc.get_transition_info(team_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@router.post("/start")
def start_stopwatch(payload: TeamIdPayload):
    """
    Start the transition physical reconnaissance stopwatch.
    """
    res = svc.start_stopwatch(payload.team_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@router.post("/verify")
def verify_password(payload: VerifyPasswordPayload):
    """
    Verify security override password (placeholder Chronos@123) and stop the stopwatch.
    """
    res = svc.verify_password_and_stop_stopwatch(payload.team_id, payload.password)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Invalid password."))
    return res
