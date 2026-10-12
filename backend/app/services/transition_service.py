import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from ..database.connection import get_connection
from ..database.queries import update_team_scores
from .google_sheets_service import google_sheets_service

CLUES_FILE = Path(__file__).resolve().parents[3] / "docs" / "clues.md"

DEFAULT_PLACEHOLDER_PASSWORD = "Chronos@123"

# Cached parsed clues
_CACHED_CLUES: Dict[str, List[Dict[str, Any]]] = {}


def _parse_clues_from_file(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    clues_by_zone: Dict[str, List[Dict[str, Any]]] = {
        "PAST": [],
        "PRESENT": [],
        "FUTURE": [],
    }
    if not path.is_file():
        return clues_by_zone

    content = path.read_text(encoding="utf-8")
    current_zone = None
    current_clue = None

    for line in content.splitlines():
        line_s = line.strip()
        if not line_s:
            continue
        if line_s.startswith("---"):
            continue
        lower = line_s.lower()
        if "for past:" in lower:
            current_zone = "PAST"
            continue
        elif "for present:" in lower:
            current_zone = "PRESENT"
            continue
        elif "for future:" in lower:
            current_zone = "FUTURE"
            continue

        m = re.match(r"^clue\s+(\d+)", lower)
        if m and current_zone:
            c_num = int(m.group(1))
            current_clue = {"number": c_num, "lines": [], "destination": ""}
            clues_by_zone[current_zone].append(current_clue)
            continue

        if line_s.lower().startswith("destination:"):
            if current_clue:
                current_clue["destination"] = line_s
            continue

        if current_clue:
            current_clue["lines"].append(line_s)

    return clues_by_zone


def get_all_clues() -> Dict[str, List[Dict[str, Any]]]:
    global _CACHED_CLUES
    if not _CACHED_CLUES or not any(_CACHED_CLUES.values()):
        _CACHED_CLUES = _parse_clues_from_file(CLUES_FILE)
    return _CACHED_CLUES


def _log_event(cursor, team_id: int, event_type: str, data: dict):
    cursor.execute(
        """
        INSERT INTO game_logs (team_id, event_type, event_data, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            team_id,
            event_type,
            json.dumps(data),
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
        ),
    )


def assign_transition_zone_and_clue(conn, team_id: int) -> Dict[str, Any]:
    """
    Assigns a zone (PAST, PRESENT, or FUTURE) and a clue from docs/clues.md to a team.
    
    Compulsory condition:
    In 6-team gameplay, exactly two teams receive each zone:
      - 2 teams get PAST
      - 2 teams get PRESENT
      - 2 teams get FUTURE
    
    Within each zone, teams receive distinct clues from docs/clues.md.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 
            transition_zone,
            transition_clue_number,
            transition_clue_text,
            transition_destination
        FROM teams
        WHERE id = ?
        """,
        (team_id,),
    )
    row = cursor.fetchone()

    if row and row["transition_zone"] and row["transition_clue_text"]:
        return {
            "zone": row["transition_zone"],
            "clue_number": row["transition_clue_number"],
            "clue_text": row["transition_clue_text"],
            "destination": row["transition_destination"],
        }

    clues = get_all_clues()
    zones_order = ["PAST", "PRESENT", "FUTURE"]

    # Count how many teams have already been assigned to each zone
    cursor.execute(
        """
        SELECT transition_zone, COUNT(*) as cnt
        FROM teams
        WHERE transition_zone IN ('PAST', 'PRESENT', 'FUTURE')
        GROUP BY transition_zone
        """
    )
    counts = {z: 0 for z in zones_order}
    for r in cursor.fetchall():
        if r["transition_zone"] in counts:
            counts[r["transition_zone"]] = r["cnt"]

    total_assigned = sum(counts.values())
    # In a 6-team game, capacity per zone is 2.
    # For multiple batches (e.g. 12 teams or testing):
    cap_per_zone = max(2, (total_assigned // 6 + 1) * 2)

    available = [z for z in zones_order if counts[z] < cap_per_zone]
    if not available:
        cap_per_zone += 2
        available = [z for z in zones_order if counts[z] < cap_per_zone]

    # Select the zone with the minimum count, breaking ties deterministically
    selected_zone = min(available, key=lambda z: (counts[z], zones_order.index(z)))

    # Select distinct clue within that zone
    zone_clues = clues.get(selected_zone, [])
    if not zone_clues:
        # Fallback if file was empty
        zone_clues = [{
            "number": 1,
            "lines": [f"Explore the {selected_zone.title()} Zone for temporal artifacts."],
            "destination": f"Destination: {selected_zone.title()} Zone"
        }]

    clue_idx = counts[selected_zone] % len(zone_clues)
    selected_clue = zone_clues[clue_idx]

    clue_number = selected_clue["number"]
    clue_text = "\n".join(selected_clue["lines"])
    destination = selected_clue.get("destination") or f"Destination: {selected_zone.title()} Zone"

    cursor.execute(
        """
        UPDATE teams
        SET transition_zone = ?,
            transition_clue_number = ?,
            transition_clue_text = ?,
            transition_destination = ?
        WHERE id = ?
        """,
        (selected_zone, clue_number, clue_text, destination, team_id),
    )
    conn.commit()

    _log_event(cursor, team_id, "TRANSITION_ZONE_ASSIGNED", {
        "zone": selected_zone,
        "clue_number": clue_number,
        "destination": destination,
    })
    conn.commit()

    return {
        "zone": selected_zone,
        "clue_number": clue_number,
        "clue_text": clue_text,
        "destination": destination,
    }


def get_transition_info(team_id: int) -> Dict[str, Any]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                id,
                team_name,
                member_1_name,
                member_2_name,
                member_1_prn,
                member_2_prn,
                current_state,
                round1_auth_code,
                transition_zone,
                transition_clue_number,
                transition_clue_text,
                transition_destination,
                transition_start_time,
                transition_end_time,
                transition_time_diff,
                transition_status,
                transition_password_used,
                transition_attempts,
                transition_score
            FROM teams
            WHERE id = ?
            """,
            (team_id,),
        )
        team = cursor.fetchone()
        if not team:
            return {"error": "Invalid team_id."}

        # Ensure zone & clue are assigned
        if not team["transition_zone"] or not team["transition_clue_text"]:
            assignment = assign_transition_zone_and_clue(conn, team_id)
            zone = assignment["zone"]
            clue_number = assignment["clue_number"]
            clue_text = assignment["clue_text"]
            destination = assignment["destination"]
        else:
            zone = team["transition_zone"]
            clue_number = team["transition_clue_number"]
            clue_text = team["transition_clue_text"]
            destination = team["transition_destination"]

        status = team["transition_status"] or "NOT_STARTED"
        start_time = team["transition_start_time"]
        end_time = team["transition_end_time"]
        elapsed_seconds = team["transition_time_diff"] or 0.0

        if status == "RUNNING" and start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=timezone.utc)
                now_dt = datetime.now(timezone.utc)
                elapsed_seconds = max(0.0, (now_dt - start_dt).total_seconds())
            except Exception:
                pass

        pw_used = ""
        try:
            pw_used = team["transition_password_used"] or ""
        except Exception:
            pass

        attempts = 0
        score = 0.0
        try:
            attempts = int(team["transition_attempts"] or 0)
        except Exception:
            pass
        try:
            score = float(team["transition_score"] or 0.0)
        except Exception:
            pass

        is_completed = (status == "COMPLETED") or (attempts >= 3)
        auto_advanced = (attempts >= 3 and score == 0.0) or (pw_used == "LOCKOUT_AUTO_ADVANCE")

        return {
            "team_id": team["id"],
            "team_name": team["team_name"],
            "round1_auth_code": team["round1_auth_code"] or "CHRONOS-KEY",
            "zone": zone,
            "clue_number": clue_number,
            "clue_text": clue_text,
            "destination": destination,
            "stopwatch_status": "COMPLETED" if is_completed else status,
            "start_time": start_time,
            "end_time": end_time,
            "elapsed_seconds": round(float(elapsed_seconds), 2),
            "is_completed": is_completed,
            "can_proceed": is_completed,
            "auto_advanced": auto_advanced,
            "password_used": pw_used,
            "transition_attempts": attempts,
            "attempts_remaining": max(0, 3 - attempts),
            "transition_score": score,
        }
    finally:
        conn.close()


def start_stopwatch(team_id: int) -> Dict[str, Any]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT transition_status, transition_start_time
            FROM teams
            WHERE id = ?
            """,
            (team_id,),
        )
        row = cursor.fetchone()
        if not row:
            return {"error": "Invalid team_id."}

        # If already completed, do not restart
        if row["transition_status"] == "COMPLETED":
            return get_transition_info(team_id)

        now_iso = datetime.now(timezone.utc).isoformat(timespec="milliseconds")

        if not row["transition_start_time"]:
            cursor.execute(
                """
                UPDATE teams
                SET transition_start_time = ?,
                    transition_status = 'RUNNING'
                WHERE id = ?
                """,
                (now_iso, team_id),
            )
            _log_event(cursor, team_id, "TRANSITION_STOPWATCH_STARTED", {"start_time": now_iso})
            conn.commit()

        return get_transition_info(team_id)
    finally:
        conn.close()


def verify_password_and_stop_stopwatch(team_id: int, password: str) -> Dict[str, Any]:
    cleaned = (password or "").strip()
    if not cleaned:
        return {
            "success": False,
            "error": "Password cannot be empty.",
            "is_completed": False
        }

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, team_name, transition_zone, transition_start_time, transition_status, 
                   transition_time_diff, transition_attempts, transition_score
            FROM teams
            WHERE id = ?
            """,
            (team_id,),
        )
        row = cursor.fetchone()
        if not row:
            return {"success": False, "error": "Invalid team_id."}

        # If already completed, return existing state
        if row["transition_status"] == "COMPLETED":
            return {
                "success": True,
                "message": "Security override verified. Sector cleared.",
                "elapsed_seconds": float(row["transition_time_diff"] or 0.0),
                "is_completed": True,
                "points_awarded": float(row["transition_score"] or 0.0),
                "attempts_used": int(row["transition_attempts"] or 0),
            }

        # REQUIREMENT: Until stopwatch is started, do NOT allow password to be entered!
        if row["transition_status"] != "RUNNING" or not row["transition_start_time"]:
            return {
                "success": False,
                "error": "Reconnaissance stopwatch has not been started. You must start the stopwatch before entering the authentication password.",
                "is_completed": False,
                "stopwatch_required": True,
            }

        team_name = row["team_name"]
        team_zone = row["transition_zone"] or ""
        current_attempts = 0
        try:
            current_attempts = int(row["transition_attempts"] or 0)
        except Exception:
            pass

        # HARD LIMIT: Strictly maximum 3 password attempts allowed! Never allow a 4th attempt.
        if current_attempts >= 3 or row["transition_status"] == "COMPLETED":
            if row["transition_status"] != "COMPLETED":
                cursor.execute(
                    """
                    UPDATE teams
                    SET transition_status = 'COMPLETED',
                        transition_score = 0.0,
                        transition_attempts = 3
                    WHERE id = ?
                    """,
                    (team_id,),
                )
                conn.commit()
            return {
                "success": True,
                "is_completed": True,
                "auto_advanced": True if float(row["transition_score"] or 0.0) == 0.0 else False,
                "points_awarded": float(row["transition_score"] or 0.0),
                "attempts_used": 3,
                "attempts_remaining": 0,
                "elapsed_seconds": float(row["transition_time_diff"] or 0.0),
                "message": "Maximum 3 password attempts reached. Authentication locked.",
            }

        attempt_number = current_attempts + 1

        # Validate password against Google Spreadsheet API
        val_result = google_sheets_service.validate_and_use_password(
            password=cleaned,
            team_id=team_id,
            team_name=team_name,
            zone=team_zone
        )

        start_time = row["transition_start_time"]
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat(timespec="milliseconds")
        elapsed_seconds = 0.0

        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=timezone.utc)
                now_dt = datetime.now(timezone.utc)
                elapsed_seconds = max(0.0, (now_dt - start_dt).total_seconds())
            except Exception:
                pass

        if val_result.get("valid"):
            # SUCCESS: Graded authentication
            # 1st attempt: 20 points
            # 2nd attempt: 10 points
            # 3rd attempt: 5 points
            if attempt_number == 1:
                points_awarded = 20.0
            elif attempt_number == 2:
                points_awarded = 10.0
            elif attempt_number == 3:
                points_awarded = 5.0
            else:
                points_awarded = 0.0

            cursor.execute(
                """
                UPDATE teams
                SET transition_end_time = ?,
                    transition_time_diff = ?,
                    transition_status = 'COMPLETED',
                    transition_password_used = ?,
                    transition_attempts = ?,
                    transition_score = ?
                WHERE id = ?
                """,
                (now_iso, elapsed_seconds, cleaned, attempt_number, points_awarded, team_id),
            )

            update_team_scores(conn, team_id)

            _log_event(cursor, team_id, "TRANSITION_PASSWORD_VERIFIED", {
                "password": cleaned,
                "stop_time": now_iso,
                "elapsed_seconds": elapsed_seconds,
                "source": val_result.get("source", "GOOGLE_SPREADSHEET"),
                "zone": val_result.get("zone"),
                "attempt_number": attempt_number,
                "points_awarded": points_awarded,
            })
            conn.commit()

            suffix = "ST" if attempt_number == 1 else ("ND" if attempt_number == 2 else "RD")
            return {
                "success": True,
                "message": f"AUTHENTICATION VERIFIED ({attempt_number}{suffix} ATTEMPT) // +{int(points_awarded)} PTS AWARDED",
                "elapsed_seconds": round(float(elapsed_seconds), 2),
                "is_completed": True,
                "points_awarded": points_awarded,
                "attempts_used": attempt_number,
                "attempts_remaining": max(0, 3 - attempt_number),
                "zone": val_result.get("zone"),
            }

        else:
            # FAILED ATTEMPT:
            new_attempts = attempt_number

            # REQUIREMENT: After 3 inaccurate responses, automatically advance to Round 2 with 0 points
            if new_attempts >= 3:
                cursor.execute(
                    """
                    UPDATE teams
                    SET transition_end_time = ?,
                        transition_time_diff = ?,
                        transition_status = 'COMPLETED',
                        transition_password_used = 'LOCKOUT_AUTO_ADVANCE',
                        transition_attempts = ?,
                        transition_score = 0.0
                    WHERE id = ?
                    """,
                    (now_iso, elapsed_seconds, new_attempts, team_id),
                )
                update_team_scores(conn, team_id)

                _log_event(cursor, team_id, "TRANSITION_AUTO_ADVANCED_3_FAILED_ATTEMPTS", {
                    "last_attempt": cleaned,
                    "stop_time": now_iso,
                    "elapsed_seconds": elapsed_seconds,
                    "attempts": new_attempts,
                    "points_awarded": 0.0,
                })
                conn.commit()

                return {
                    "success": True,
                    "is_completed": True,
                    "auto_advanced": True,
                    "points_awarded": 0.0,
                    "attempts_used": 3,
                    "attempts_remaining": 0,
                    "elapsed_seconds": round(float(elapsed_seconds), 2),
                    "message": "3 INACCURATE RESPONSES (0 PTS) // SECURITY LOCKOUT BYPASS TRIGGERED: ADVANCING TO ROUND 2.",
                }
            else:
                cursor.execute(
                    "UPDATE teams SET transition_attempts = ? WHERE id = ?",
                    (new_attempts, team_id),
                )
                conn.commit()

                attempts_left = 3 - new_attempts
                next_pts = 10 if attempts_left == 2 else 5
                raw_error = val_result.get("error") or "Invalid security password."

                warning_suffix = ""
                if attempts_left == 1:
                    warning_suffix = " ⚠️ WARNING: 3rd and final attempt next — 0 points will be given if failed!"

                return {
                    "success": False,
                    "is_completed": False,
                    "auto_advanced": False,
                    "attempts_used": new_attempts,
                    "attempts_remaining": attempts_left,
                    "next_potential_points": next_pts,
                    "error": f"{raw_error} Attempt {new_attempts} of 3 failed. {attempts_left} attempt{'s' if attempts_left > 1 else ''} remaining ({next_pts} pts next attempt).{warning_suffix}",
                }
    finally:
        conn.close()
