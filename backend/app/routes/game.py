"""
Project Chronos — General Game State & Telemetry Routes
"""

from fastapi import APIRouter, HTTPException, Query
from ..services.game_service import GameService

router = APIRouter(prefix="/api/game", tags=["Game State"])

@router.get("/state", summary="Get Current Team Game State")
def get_state(team_id: int = Query(..., description="Team ID")):
    try:
        return GameService.get_team_state(team_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))
