"""
Tester shortcut routes. Every route answers 404 unless the server runs with
CHRONOS_ENABLE_SKIP=1 (see services/dev_skip.py). Mounted behind require_team.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from ..services import dev_skip

router = APIRouter(prefix="/api/dev", tags=["Dev"])


class SkipBody(BaseModel):
    team_id: int


@router.post("/skip-round")
def skip_round(body: SkipBody):
    return dev_skip.skip_round(body.team_id)
