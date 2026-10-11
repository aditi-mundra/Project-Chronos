from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..services.auth_service import login_team, get_team_session
from ..services.team_session import require_team

router = APIRouter()


class LoginRequest(BaseModel):
    team_name: Optional[str] = ""
    member_1_name: Optional[str] = ""
    member_2_name: Optional[str] = ""
    member_1_prn: Optional[str] = ""
    member_2_prn: Optional[str] = ""


@router.post("/login")
def login(request: LoginRequest):
    """
    Team login.

    New team name: the team is registered and logged in.
    Existing team name: logged in only when both PRNs match the registered PRNs
    (verified, never modified); otherwise 409.
    """
    return login_team(
        request.team_name,
        request.member_1_name,
        request.member_2_name,
        request.member_1_prn,
        request.member_2_prn,
    )


@router.get("/session", dependencies=[Depends(require_team)])
def session(team_id: int):
    """
    Confirm a stored browser session is still valid: 404 when the team no longer
    exists, 401 when the session token is missing or wrong (the team logs in again).
    """
    return get_team_session(team_id)
