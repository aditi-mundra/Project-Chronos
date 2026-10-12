"""
Project Chronos — Master Admin & Leaderboard Routes
Provides host leaderboard, admin authentication, system logs, and CSV export.
"""

import io
import csv
import os
import secrets
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field

from ..database.connection import get_connection

router = APIRouter(prefix="/api/admin", tags=["Admin & Host Leaderboard"])

DEFAULT_ADMIN_PASSWORDS = {"Chronos@123", "chronos@123"}
ADMIN_PASSWORD = os.getenv("CHRONOS_ADMIN_PASSWORD", "").strip()
ADMIN_SECRET_TOKEN = os.getenv("CHRONOS_ADMIN_TOKEN") or secrets.token_urlsafe(32)
VALID_ADMIN_PASSWORDS = {ADMIN_PASSWORD.lower(), *{p.lower() for p in DEFAULT_ADMIN_PASSWORDS}} if ADMIN_PASSWORD else {p.lower() for p in DEFAULT_ADMIN_PASSWORDS}


def is_valid_admin_password(pw: Optional[str]) -> bool:
    if not pw:
        return False
    cleaned = pw.strip().strip('"').strip("'")
    return cleaned == "Chronos@123" or cleaned.lower() in VALID_ADMIN_PASSWORDS


def is_localhost(request: Request) -> bool:
    """
    Checks if the incoming request originated from localhost / loopback.
    Returns False for any network / LAN client.
    """
    if not request.client:
        return True
    host = request.client.host
    return host in ("127.0.0.1", "::1", "localhost", "testclient") or host.startswith("127.")


def require_localhost(request: Request) -> None:
    if not is_localhost(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Master Leaderboard is strictly restricted to localhost and cannot be accessed over the network.",
        )


def require_admin(request: Request) -> None:
    require_localhost(request)
    token = ""
    authorization = request.headers.get("authorization", "")
    scheme, _, auth_token = authorization.partition(" ")
    if scheme.lower() == "bearer" and auth_token:
        token = auth_token
    elif request.query_params.get("token"):
        token = request.query_params.get("token")

    if not token or not secrets.compare_digest(token, ADMIN_SECRET_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Host authorization required.",
        )


class AdminLoginRequest(BaseModel):
    password: str = Field(..., description="Master host supervisor password")


class AdminLoginResponse(BaseModel):
    success: bool
    token: str
    message: str


def format_seconds(seconds: Optional[float]) -> str:
    if seconds is None:
        return "--:--"
    sec_int = int(seconds)
    mins = sec_int // 60
    secs = sec_int % 60
    return f"{mins:02d}:{secs:02d}"


def calculate_r1_time_diff(started_at: Optional[str], completed_at: Optional[str]) -> Optional[float]:
    if not started_at or not completed_at:
        return None
    try:
        start_dt = datetime.fromisoformat(started_at)
        comp_dt = datetime.fromisoformat(completed_at)
        return max(0.0, (comp_dt - start_dt).total_seconds())
    except Exception:
        return None


def fetch_leaderboard_data() -> List[Dict[str, Any]]:
    from ..database.queries import update_team_scores
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Synchronize and recompute total_score for all teams to ensure DB consistency
        cursor.execute("SELECT id FROM teams")
        for row in cursor.fetchall():
            update_team_scores(conn, row["id"])

        cursor.execute("""
            SELECT 
                id as team_id,
                team_name,
                member_1_name,
                member_2_name,
                member_1_prn,
                member_2_prn,
                current_state,
                round1_score,
                r1_score,
                round1_auth_code,
                transition_score,
                round2_score,
                r2_score,
                round3_score,
                r3_score,
                total_score,
                round1_started_at,
                round1_completed_at,
                round2_started_at,
                round2_completed_at,
                round3_started_at,
                round3_completed_at,
                ai_model_used,
                ai_api_live,
                created_at,
                updated_at
            FROM teams
            ORDER BY total_score DESC, (round1_score + COALESCE(transition_score, 0) + round2_score + round3_score) DESC, id ASC
        """)
        rows = cursor.fetchall()

        entries = []
        for idx, r in enumerate(rows):
            r1_diff = calculate_r1_time_diff(r["round1_started_at"], r["round1_completed_at"])
            
            # Preserve negative Round 1 scores and enforce authoritative grading bounds:
            # Round 1: 50.0 maximum, -25.0 minimum
            # Lobby / Transition: 20.0 maximum, 0.0 minimum
            # Round 2: 20.0 maximum, 0.0 minimum
            # Round 3: 10.0 maximum, 0.0 minimum
            r1_val = r["round1_score"] if r["round1_score"] is not None else r["r1_score"]
            r1_score_val = max(-25.0, min(50.0, float(r1_val))) if r1_val is not None else 0.0

            trans_val = r["transition_score"]
            trans_score_val = max(0.0, min(20.0, float(trans_val))) if trans_val is not None else 0.0

            r2_val = r["round2_score"] if r["round2_score"] is not None else r["r2_score"]
            r2_score_val = max(0.0, min(20.0, float(r2_val))) if r2_val is not None else 0.0

            r3_val = r["round3_score"] if r["round3_score"] is not None else r["r3_score"]
            r3_score_val = max(0.0, min(10.0, float(r3_val))) if r3_val is not None else 0.0

            # Direct mathematical total of Round 1 + Lobby + Round 2 + Round 3 scores
            calc_total = round(r1_score_val + trans_score_val + r2_score_val + r3_score_val, 2)

            status_val = "FINISHED" if r["current_state"] in ("COMPLETED", "DECISION_SUBMITTED", "FINAL_REVEAL") else (r["current_state"] or "ACTIVE")

            entries.append({
                "rank": idx + 1,
                "team_id": r["team_id"],
                "team_name": r["team_name"],
                "member_1_name": r["member_1_name"] or "",
                "member_2_name": r["member_2_name"] or "",
                "member_1_prn": r["member_1_prn"] or "",
                "member_2_prn": r["member_2_prn"] or "",
                "member1_name": r["member_1_name"] or "",
                "member2_name": r["member_2_name"] or "",
                "member1_prn": r["member_1_prn"] or "",
                "member2_prn": r["member_2_prn"] or "",
                "r1_start_time": r["round1_started_at"],
                "r1_end_time": r["round1_completed_at"],
                "r1_time_diff": r1_diff,
                "r1_time_formatted": format_seconds(r1_diff),
                "round1_auth_code": r["round1_auth_code"] or "",
                "r1_score": r1_score_val,
                "r1_scaled": r1_score_val,
                "round1_score": r1_score_val,
                "transition_score": trans_score_val,
                "lobby_score": trans_score_val,
                "r2_score": r2_score_val,
                "round2_score": r2_score_val,
                "r3_score": r3_score_val,
                "round3_score": r3_score_val,
                "total_score": calc_total,
                "r1_max": 50.0,
                "r1_min": -25.0,
                "lobby_max": 20.0,
                "lobby_min": 0.0,
                "transition_max": 20.0,
                "transition_min": 0.0,
                "r2_max": 20.0,
                "r2_min": 0.0,
                "r3_max": 10.0,
                "r3_min": 0.0,
                "total_max": 100.0,
                "total_min": -25.0,
                "current_state": r["current_state"] or "READY",
                "status": status_val,
                "ai_model_used": r["ai_model_used"] or "openai/gpt-oss-120b",
                "ai_api_live": r["ai_api_live"] or "YES",
            })
        return entries
    finally:
        conn.close()


@router.post("/login", response_model=AdminLoginResponse)
def admin_login(request: Request, payload: AdminLoginRequest):
    require_localhost(request)
    if is_valid_admin_password(payload.password):
        return AdminLoginResponse(success=True, token=ADMIN_SECRET_TOKEN, message="ACCESS_GRANTED")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid host passkey.")


@router.get("/leaderboard")
def get_admin_leaderboard(request: Request):
    """
    Returns ranked leaderboard of all registered teams with real-time score calculation.
    """
    require_admin(request)
    return fetch_leaderboard_data()


@router.get("/export-csv")
def export_leaderboard_csv(request: Request):
    """
    Generates and downloads a complete master CSV export of the leaderboard.
    """
    require_admin(request)
    entries = fetch_leaderboard_data()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Rank",
        "Team Name",
        "Operator 1 Name",
        "Operator 1 PRN",
        "Operator 2 Name",
        "Operator 2 PRN",
        "Status / State",
        "Round 1 Score (Max 50 / Min -25)",
        "Round 1 Time (s)",
        "Round 1 Time Formatted",
        "Round 1 Auth Code",
        "Lobby Score (Max 20)",
        "Round 2 Score (Max 20)",
        "Round 3 Score (Max 10)",
        "Total Score (Max 100)",
        "AI Model Used",
        "AI API Live"
    ])

    for t in entries:
        writer.writerow([
            t["rank"],
            t["team_name"],
            t["member_1_name"],
            t["member_1_prn"],
            t["member_2_name"],
            t["member_2_prn"],
            t["status"],
            t["round1_score"],
            t["r1_time_diff"] if t["r1_time_diff"] is not None else "",
            t["r1_time_formatted"],
            t["round1_auth_code"],
            t.get("transition_score", 0.0),
            t["round2_score"],
            t["round3_score"],
            t["total_score"],
            t.get("ai_model_used", ""),
            t.get("ai_api_live", "")
        ])

    csv_data = output.getvalue()
    filename = f"chronos_leaderboard_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


from ..utils.csv_export import export_table_to_csv

@router.get("/export/csv/{table_name}")
def download_table_csv(request: Request, table_name: str = "teams"):
    """Download live table data as a downloadable CSV file."""
    require_admin(request)
    try:
        csv_data = export_table_to_csv(table_name)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={table_name}_export.csv"}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/logs")
def get_admin_logs(request: Request, limit: int = Query(100, ge=1, le=1000)):
    """
    Returns recent chronological audit trail events.
    """
    require_admin(request)
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.id, l.team_id, t.team_name, l.event_type, l.event_data, l.created_at
            FROM game_logs l
            LEFT JOIN teams t ON l.team_id = t.id
            ORDER BY l.id DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


class ClearDbRequest(BaseModel):
    password: Optional[str] = None


@router.post("/clear-db")
async def clear_database(
    request: Request,
    payload: Optional[ClearDbRequest] = None,
    password: Optional[str] = Query(None)
):
    """
    Clears all competition database records with the configured host passkey.
    Wipes all teams, submissions, round cases, and audit logs.
    Preserves and verifies seed data for subsequent games.
    """
    req_password = password
    if not req_password and payload and payload.password:
        req_password = payload.password
    if not req_password:
        try:
            body = await request.json()
            if isinstance(body, dict):
                req_password = body.get("password")
        except Exception:
            pass

    if not is_valid_admin_password(req_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrator password. Clearance denied."
        )

    from ..database.schema import seed_round1_items_if_empty, seed_round2_files_if_empty

    conn = get_connection()
    try:
        cursor = conn.cursor()
        tables_to_clear = [
            "teams",
            "round1_submissions",
            "round1_team_items",
            "round2_chat_messages",
            "round2_submissions",
            "round3_team_cases",
            "round3_submissions",
            "submissions",
            "team_fragments",
            "hints",
            "investments",
            "game_logs"
        ]
        for tbl in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {tbl}")
            except Exception:
                pass

        try:
            placeholders = ",".join(f"'{tbl}'" for tbl in tables_to_clear)
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name IN ({placeholders})")
        except Exception:
            pass

        conn.commit()
    finally:
        conn.close()

    # Re-verify and ensure baseline seed items exist
    seed_round1_items_if_empty()
    seed_round2_files_if_empty()

    return {
        "success": True,
        "message": "Database successfully cleared. All team records and game telemetry purged."
    }

