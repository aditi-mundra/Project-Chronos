"""
Round 3 API. Mounted in main.py behind require_team, so every call must carry the
calling team's session token for the team_id it acts on.

  GET  /api/round3/availability   may this team start Round 3 yet? (no side effects)
  POST /api/round3/start          the Lobby's START ROUND 3 button (idempotent)
  GET  /api/round3/scenario       the team's case once started (read-only)
  POST /api/round3/submit         the final accusation (one per team)
  GET  /api/round3/verdict        debrief, only after the team's own submission

There is no endpoint that lists cases or reveals an answer key.
"""

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..services import round3_service as svc

router = APIRouter(prefix="/api/round3", tags=["Round 3"])


class StartBody(BaseModel):
    team_id: int


class SubmitBody(BaseModel):
    team_id: int
    selected_candidate_id: str = Field(..., min_length=1, max_length=32)
    selected_evidence_ids: Optional[List[str]] = Field(default=None, max_length=20)


@router.get("/availability")
def availability(team_id: int):
    return svc.get_availability(team_id)


@router.post("/start")
def start(body: StartBody):
    return svc.start_round3(body.team_id)


@router.get("/scenario")
def scenario(team_id: int):
    return svc.get_scenario(team_id)


@router.post("/submit")
def submit(body: SubmitBody):
    return svc.submit_decision(
        body.team_id, body.selected_candidate_id, body.selected_evidence_ids or []
    )


@router.get("/verdict")
def verdict(team_id: int):
    return svc.get_verdict(team_id)
