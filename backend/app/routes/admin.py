"""
Admin API (host only). Everything except /login needs the bearer token that
/login returns; with CHRONOS_ADMIN_PASSWORD unset the whole API answers 503.
There is no public leaderboard and no unauthenticated export.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field

from ..services import admin_service as svc

router = APIRouter(prefix="/api/admin", tags=["Admin"])


class LoginBody(BaseModel):
    password: str = Field(..., min_length=1, max_length=256)


@router.post("/login")
def login(body: LoginBody, request: Request):
    if not svc.admin_enabled():
        raise HTTPException(status_code=503, detail="Admin access is not configured on this server.")
    svc.check_login_allowed(request)
    if not svc.password_matches(body.password):
        svc.record_login_failure(request)
        raise HTTPException(status_code=401, detail="Invalid admin password.")
    return {"success": True, "token": svc.make_token(), "expires_in": svc.TOKEN_TTL_SECONDS}


@router.get("/session", dependencies=[Depends(svc.require_admin)])
def session():
    return {"valid": True}


@router.get("/leaderboard", dependencies=[Depends(svc.require_admin)])
def get_leaderboard():
    return svc.leaderboard()


@router.get("/export-csv", dependencies=[Depends(svc.require_admin)])
def export_csv():
    filename = f"chronos_leaderboard_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=svc.leaderboard_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/logs", dependencies=[Depends(svc.require_admin)])
def get_logs(limit: int = Query(100, ge=1, le=1000)):
    return svc.recent_logs(limit)
