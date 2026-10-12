import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from ..database.connection import get_connection

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
                transition_status
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

        return {
            "team_id": team["id"],
            "team_name": team["team_name"],
            "round1_auth_code": team["round1_auth_code"] or "CHRONOS-KEY",
            "zone": zone,
            "clue_number": clue_number,
            "clue_text": clue_text,
            "destination": destination,
            "stopwatch_status": status,
            "start_time": start_time,
            "end_time": end_time,
            "elapsed_seconds": round(float(elapsed_seconds), 2),
            "is_completed": status == "COMPLETED",
            "can_proceed": status == "COMPLETED",
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

    # Verify against placeholder password Chronos@123
    is_valid = (cleaned == DEFAULT_PLACEHOLDER_PASSWORD or cleaned.lower() == DEFAULT_PLACEHOLDER_PASSWORD.lower())

    if not is_valid:
        return {
            "success": False,
            "error": "Invalid security override password. Stopwatch continues running.",
            "is_completed": False
        }

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT transition_start_time, transition_status, transition_time_diff
            FROM teams
            WHERE id = ?
            """,
            (team_id,),
        )
        row = cursor.fetchone()
        if not row:
            return {"success": False, "error": "Invalid team_id."}

        if row["transition_status"] == "COMPLETED":
            return {
                "success": True,
                "message": "Security override verified. Sector cleared.",
                "elapsed_seconds": float(row["transition_time_diff"] or 0.0),
                "is_completed": True,
            }

        start_time = row["transition_start_time"]
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat(timespec="milliseconds")
        elapsed_seconds = 0.0

        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=timezone.utc)
                elapsed_seconds = max(0.0, (now_dt - start_dt).total_seconds())
            except Exception:
                pass

        cursor.execute(
            """
            UPDATE teams
            SET transition_end_time = ?,
                transition_time_diff = ?,
                transition_status = 'COMPLETED'
            WHERE id = ?
            """,
            (now_iso, elapsed_seconds, team_id),
        )

        _log_event(cursor, team_id, "TRANSITION_STOPWATCH_STOPPED", {
            "stop_time": now_iso,
            "elapsed_seconds": elapsed_seconds,
        })
        conn.commit()

        return {
            "success": True,
            "message": "SECURITY OVERRIDE VERIFIED // ACCESS GRANTED",
            "elapsed_seconds": round(float(elapsed_seconds), 2),
            "is_completed": True,
        }
    finally:
        conn.close()
