"""
Project Chronos — Physical Transition Round API.
Mounted in main.py behind require_team, so every call must carry the calling team's session
token for the team_id it acts on.

  GET  /api/transition/state    clue id, attempts left and status (allocates the clue on first call)
  POST /api/transition/start    the team started the stopwatch (idempotent, logging only)
  POST /api/transition/verify   submit the password found at the physical destination
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.transition_service import TransitionService, TransitionError

router = APIRouter(prefix="/api/transition", tags=["Transition Round"])


class TransitionTeamBody(BaseModel):
    team_id: int


class TransitionVerifyBody(BaseModel):
    team_id: int
    password: str = Field(..., max_length=64)


def _run(fn, *args):
    try:
        return fn(*args)
    except TransitionError as err:
        raise HTTPException(status_code=err.status_code, detail=err.message)


@router.get("/state")
def get_state(team_id: int):
    return _run(TransitionService.get_state, team_id)


@router.get("/progress")
def get_progress(team_id: int):
    """Read-only position in the round (no clue is allocated); used to resume after a reload."""
    return _run(TransitionService.progress, team_id)


@router.post("/start")
def start(body: TransitionTeamBody):
    return _run(TransitionService.start, body.team_id)


@router.post("/stop")
def stop(body: TransitionTeamBody):
    """END STOPWATCH: freeze the duration server-side (idempotent)."""
    return _run(TransitionService.stop, body.team_id)


@router.post("/verify")
def verify(body: TransitionVerifyBody):
    return _run(TransitionService.verify, body.team_id, body.password)
