from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ..services.auth_service import login_team, get_team_session

router = APIRouter()


class LoginRequest(BaseModel):
    team_name: Optional[str] = ""
    member_1_name: Optional[str] = None
    member_2_name: Optional[str] = None
    member_1_prn: Optional[str] = None
    member_2_prn: Optional[str] = None
    member1_name: Optional[str] = None
    member2_name: Optional[str] = None
    member1_prn: Optional[str] = None
    member2_prn: Optional[str] = None


@router.post("/login")
def login(request: LoginRequest):
    """
    Team login.

    New team name: the team is registered and logged in.
    Existing team name: logged in only when both PRNs match the registered PRNs
    (verified, never modified); otherwise 409.
    """
    m1_name = request.member_1_name or request.member1_name or ""
    m2_name = request.member_2_name or request.member2_name or ""
    m1_prn = request.member_1_prn or request.member1_prn or ""
    m2_prn = request.member_2_prn or request.member2_prn or ""

    return login_team(
        request.team_name or "",
        m1_name,
        m2_name,
        m1_prn,
        m2_prn,
    )


@router.get("/session")
def session(team_id: int):
    """
    Confirm a stored browser session still maps to an existing team (404 if not).
    """
    return get_team_session(team_id)
