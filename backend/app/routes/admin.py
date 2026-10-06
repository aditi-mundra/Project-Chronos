"""
Project Chronos — Master Admin & Leaderboard Routes
Provides host leaderboard, admin authentication, system logs, and CSV export.
"""

import io
import csv
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field

from ..database.connection import get_connection

router = APIRouter(prefix="/api/admin", tags=["Admin & Host Leaderboard"])

ADMIN_PASSWORD = os.getenv("CHRONOS_ADMIN_PASSWORD", "chronos2140")
ADMIN_SECRET_TOKEN = "CHRONOS_SUPERVISOR_SESSION_SECURE_2140"
VALID_ADMIN_PASSWORDS = {
    "admin",
    "chronos2140",
    ADMIN_PASSWORD.strip().lower(),
}


def is_valid_admin_password(pw: Optional[str]) -> bool:
    if not pw:
        return False
    cleaned = pw.strip().strip('"').strip("'").lower()
    return cleaned in VALID_ADMIN_PASSWORDS


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
                round1_auth_code,
                round2_score,
                round3_score,
                total_score,
                round1_started_at,
                round1_completed_at,
                round2_started_at,
                round2_completed_at,
                round3_started_at,
                round3_completed_at,
                created_at,
                updated_at
            FROM teams
            ORDER BY total_score DESC, (round1_score + round2_score + round3_score) DESC, id ASC
        """)
        rows = cursor.fetchall()

        entries = []
        for idx, r in enumerate(rows):
            r1_diff = calculate_r1_time_diff(r["round1_started_at"], r["round1_completed_at"])
            r1_score_val = float(r["round1_score"] or 0.0)
            r2_score_val = float(r["round2_score"] or 0.0)
            r3_score_val = float(r["round3_score"] or 0.0)
            calc_total = float(r["total_score"] or (r1_score_val + r2_score_val + r3_score_val))

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
                "r2_score": r2_score_val,
                "round2_score": r2_score_val,
                "r3_score": r3_score_val,
                "round3_score": r3_score_val,
                "total_score": calc_total,
                "current_state": r["current_state"] or "READY",
                "status": status_val,
            })
        return entries
    finally:
        conn.close()


@router.post("/login", response_model=AdminLoginResponse)
def admin_login(payload: AdminLoginRequest):
    if is_valid_admin_password(payload.password):
        return AdminLoginResponse(success=True, token=ADMIN_SECRET_TOKEN, message="ACCESS_GRANTED")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid host passkey.")


@router.get("/leaderboard")
def get_admin_leaderboard():
    """
    Returns ranked leaderboard of all registered teams with real-time score calculation.
    """
    return fetch_leaderboard_data()


@router.get("/export-csv")
def export_leaderboard_csv():
    """
    Generates and downloads a complete master CSV export of the leaderboard.
    """
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
        "Round 1 Score",
        "Round 1 Time (s)",
        "Round 1 Time Formatted",
        "Round 1 Auth Code",
        "Round 2 Score",
        "Round 3 Score",
        "Total Score"
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
            t["round2_score"],
            t["round3_score"],
            t["total_score"]
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
def download_table_csv(table_name: str = "teams"):
    """Download live table data as a downloadable CSV file."""
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
def get_admin_logs(limit: int = Query(100, ge=1, le=1000)):
    """
    Returns recent chronological audit trail events.
    """
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
    Clears all competition database records with password 'admin' authorization.
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

