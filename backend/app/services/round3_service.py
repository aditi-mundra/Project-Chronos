"""Round 3 business logic built directly from each team's Round 2 case."""

from __future__ import annotations

import json
import random
import re
from typing import Any, Dict, List, Optional

from ..database.connection import get_connection
from ..utils.timers import get_utc_now_iso
from . import round2_service


CANDIDATE_IDS = ("alpha", "beta", "gamma")
R3_ACTIVE = "ROUND_3_ACTIVE"
R3_COMPLETE_STATES = {"DECISION_SUBMITTED", "FINAL_REVEAL", "COMPLETED"}


def _norm(state: str | None) -> str:
    return (state or "").replace("_", "").upper()


def _json_list(value: str | None) -> List[str]:
    try:
        data = json.loads(value or "[]")
        return data if isinstance(data, list) else []
    except (TypeError, json.JSONDecodeError):
        return []


def _round2_data(cursor, team_id: int, *, include_solution: bool = False) -> Dict[str, Any]:
    """Return the exact Round 2 material assigned to this team."""
    team_case = cursor.execute(
        "SELECT case_id FROM round2_team_cases WHERE team_id = ?", (team_id,)
    ).fetchone()
    if not team_case:
        raise ValueError("This team has no Round 2 case to carry into Round 3.")

    case_id = team_case["case_id"]
    case_row = cursor.execute(
        "SELECT case_id, case_code, archetype, incident, culprit "
        "FROM round2_cases WHERE case_id = ?",
        (case_id,),
    ).fetchone()
    if not case_row:
        raise ValueError(f"Round 2 case {case_id} is missing.")

    files = [
        dict(row)
        for row in cursor.execute(
            "SELECT file_id, timeline_tag, filename, content_text "
            "FROM round2_case_files WHERE case_id = ? AND is_locked = 0 ORDER BY id",
            (case_id,),
        ).fetchall()
    ]
    suspects = [
        dict(row)
        for row in cursor.execute(
            "SELECT suspect_name, user_id, role "
            "FROM round2_case_suspects WHERE case_id = ? ORDER BY id",
            (case_id,),
        ).fetchall()
    ]
    if len(suspects) != 3:
        raise ValueError(
            f"Round 2 case {case_id} must contain exactly three suspects for Round 3."
        )

    chat_messages = [
        dict(row)
        for row in cursor.execute(
            "SELECT question_number, user_prompt, ai_response, points_deducted, created_at "
            "FROM round2_chat_messages WHERE team_id = ? ORDER BY question_number",
            (str(team_id),),
        ).fetchall()
    ]
    points_lost = sum(int(row["points_deducted"]) for row in chat_messages)
    case_info = {
        "case_id": case_row["case_id"],
        "case_code": case_row["case_code"],
        "archetype": case_row["archetype"],
        "incident": case_row["incident"],
    }
    if include_solution:
        case_info["culprit"] = case_row["culprit"]

    return {
        "case_info": case_info,
        "files": files,
        "suspects": suspects,
        "chat_messages": chat_messages,
        "questions_used": len(chat_messages),
        "points_deducted_total": points_lost,
        "ai_points_remaining": max(0, 20 - points_lost),
    }


def _build_case(round2_data: Dict[str, Any]) -> Dict[str, Any]:
    """Map Round 2 identities to anonymous Alpha/Beta/Gamma project aliases."""
    case_info = round2_data["case_info"]
    culprit_name = case_info.get("culprit", "").strip().lower()
    candidates = []
    culprit_candidate_id = ""
    identity_aliases = {}

    for candidate_id, suspect in zip(CANDIDATE_IDS, round2_data["suspects"]):
        project_name = f"Project {candidate_id.title()}"
        identity_aliases[suspect["suspect_name"]] = project_name
        identity_aliases[suspect["user_id"]] = f"PROJECT-{candidate_id.upper()}"
        if suspect["suspect_name"].strip().lower() == culprit_name:
            culprit_candidate_id = candidate_id
        candidates.append(
            {
                "id": candidate_id,
                "label": project_name,
                "name": project_name,
                "designation": project_name,
            }
        )

    if not culprit_candidate_id:
        raise ValueError("The Round 2 culprit does not match one of the assigned suspects.")

    # Candidate order is presentation-only and changes whenever Round 3 loads.
    random.SystemRandom().shuffle(candidates)

    def anonymize(value: str) -> str:
        result = value or ""
        for identity, alias in sorted(identity_aliases.items(), key=lambda item: len(item[0]), reverse=True):
            result = re.sub(re.escape(identity), alias, result, flags=re.IGNORECASE)
        return result

    evidence = []
    for item in round2_data["files"]:
        evidence_id = f"r2_{item['file_id'].lower()}"
        content = anonymize(item["content_text"].strip())
        evidence.append(
            {
                "id": evidence_id,
                "file_id": item["file_id"],
                "category": f"Timeline {item['timeline_tag'].title()}",
                "category_code": f"TIMELINE_{item['timeline_tag'].upper()}",
                "source_file": item["filename"],
                "label": f"Project {item['file_id'].title()} ({item['timeline_tag'].title()})",
                "title": item["filename"],
                "excerpt": content[:240] + ("..." if len(content) > 240 else ""),
                "full_text": content,
                "source_tag": f"ROUND 2 // {item['timeline_tag'].upper()}",
            }
        )

    return {
        "case_id": case_info["case_id"],
        "title": f"Final Review: {case_info['case_code']}",
        "description": case_info["incident"],
        "mission_brief": (
            "Re-evaluate the investigation you completed in Round 2. Review the carried "
            "case files, then lock in Project Alpha, Project Beta, or Project Gamma."
        ),
        "incident_brief": case_info["incident"],
        "candidates": candidates,
        "evidence_pool": evidence,
        "evidence_archive": evidence,
        "culprit_candidate_id": culprit_candidate_id,
        "valid_evidence_ids": [item["id"] for item in evidence],
        "_identity_aliases": identity_aliases,
        "narrative_summary": (
            f"The Round 2 evidence identifies Project {culprit_candidate_id.title()} as responsible."
        ),
    }


def _client_case(full_case: Dict[str, Any], round2_data: Dict[str, Any]) -> Dict[str, Any]:
    safe = {
        key: value
        for key, value in full_case.items()
        if key not in {"culprit_candidate_id", "valid_evidence_ids", "narrative_summary", "_identity_aliases"}
    }
    public_case_info = {
        key: value
        for key, value in round2_data["case_info"].items()
        if key != "culprit"
    }
    safe["round2_investigation"] = {
        **{
            key: value
            for key, value in round2_data.items()
            if key not in {
                "files",
                "case_info",
                "chat_messages",
                "suspects",
                "points_deducted_total",
                "ai_points_remaining",
            }
        },
        "case_info": public_case_info,
        "chat_messages": [
            {
                key: (
                    _anonymize_round3_text(value, full_case["_identity_aliases"])
                    if key in {"user_prompt", "ai_response"} and isinstance(value, str)
                    else value
                )
                for key, value in message.items()
                if key != "points_deducted"
            }
            for message in round2_data["chat_messages"]
        ],
    }
    return safe


def _anonymize_round3_text(value: str, aliases: Dict[str, str]) -> str:
    result = value or ""
    for identity, alias in sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True):
        result = re.sub(re.escape(identity), alias, result, flags=re.IGNORECASE)
    return result


def _existing_response(team, submission) -> Dict[str, Any]:
    return {
        "status": "success",
        "message": "Decision already locked for this team.",
        "verdict_recorded": True,
        "is_already_locked": True,
        "completed_at": team["round3_completed_at"],
        "round3_completed_at": team["round3_completed_at"],
        "next_state": team["current_state"],
        "current_state": team["current_state"],
    }


class Round3Service:
    @staticmethod
    def start_round3_for_team(team_id: int) -> Dict[str, Any]:
        connection = get_connection()
        try:
            round2_service.ensure_tables(connection)
            cursor = connection.cursor()
            team = cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,)).fetchone()
            if not team:
                raise ValueError(f"Team ID {team_id} not found in database.")

            team = round2_service.expire_if_needed(connection, team)

            state = team["current_state"] or ""
            completed = state in R3_COMPLETE_STATES
            resuming = _norm(state) == _norm(R3_ACTIVE) or bool(team["round3_started_at"])
            round2_timed_out = _norm(state) == "TIMEOUT" and bool(team["round2_started_at"])
            round2_complete = _norm(state) == "ROUND2COMPLETED"
            if not completed and not resuming and not (round2_complete or round2_timed_out):
                raise PermissionError(
                    f"Round 3 cannot start until Round 2 is complete (current state: {state or 'UNKNOWN'})."
                )

            round2_data = _round2_data(cursor, team_id, include_solution=True)
            full_case = _build_case(round2_data)
            now = get_utc_now_iso()
            started_at = team["round3_started_at"] or now

            if not completed and _norm(state) != _norm(R3_ACTIVE):
                cursor.execute(
                    "UPDATE teams SET round3_started_at = ?, current_state = ?, updated_at = ? WHERE id = ?",
                    (started_at, R3_ACTIVE, now, team_id),
                )
                cursor.execute(
                    "INSERT INTO game_logs (team_id, event_type, event_data, created_at) "
                    "VALUES (?, 'R3_START', ?, ?)",
                    (team_id, json.dumps({"round2_case_id": full_case["case_id"]}), now),
                )

            scenario = _client_case(full_case, round2_data)
            cursor.execute(
                """
                INSERT INTO round3_team_cases
                    (team_id, case_id, status, case_data, culprit_candidate_id,
                     valid_evidence_ids, assigned_at)
                VALUES (?, ?, 'ACTIVE', ?, ?, ?, ?)
                ON CONFLICT(team_id) DO UPDATE SET
                    case_id = excluded.case_id,
                    case_data = excluded.case_data,
                    culprit_candidate_id = excluded.culprit_candidate_id,
                    valid_evidence_ids = excluded.valid_evidence_ids
                """,
                (
                    team_id,
                    full_case["case_id"],
                    json.dumps(scenario),
                    full_case["culprit_candidate_id"],
                    json.dumps(full_case["valid_evidence_ids"]),
                    now,
                ),
            )

            submission = cursor.execute(
                "SELECT * FROM round3_submissions WHERE team_id = ?", (team_id,)
            ).fetchone()
            connection.commit()

            return {
                "status": "success",
                "team_id": team_id,
                "team_name": team["team_name"],
                "team_state": team["current_state"] if completed else R3_ACTIVE,
                "round3_started_at": started_at,
                "is_submitted": submission is not None,
                "submission": None if not submission else {
                    "selected_candidate_id": submission["selected_candidate_id"],
                    "selected_evidence_ids": _json_list(submission["selected_evidence_ids"]),
                    "submitted_at": submission["submitted_at"],
                },
                "case": scenario,
                "scenario": scenario,
                "round2_investigation": scenario["round2_investigation"],
            }
        finally:
            connection.close()

    @staticmethod
    def get_team_scenario(team_id: int) -> Dict[str, Any]:
        return Round3Service.start_round3_for_team(team_id)

    @staticmethod
    def submit_round3_decision(
        team_id: int,
        selected_candidate_id: str,
        selected_evidence_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        candidate_id = (selected_candidate_id or "").strip().lower()
        # Evidence is carried over for review only; the final action is one candidate.
        evidence_ids = []
        if not candidate_id:
            return {"status": "error", "error_code": "MISSING_CANDIDATE", "message": "Choose Alpha, Beta, or Gamma."}

        connection = get_connection()
        try:
            round2_service.ensure_tables(connection)
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.cursor()
            team = cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,)).fetchone()
            if not team:
                return {"status": "error", "error_code": "TEAM_NOT_FOUND", "message": f"Team ID {team_id} does not exist."}

            existing = cursor.execute(
                "SELECT * FROM round3_submissions WHERE team_id = ?", (team_id,)
            ).fetchone()
            if existing:
                return _existing_response(team, existing)

            if _norm(team["current_state"]) != _norm(R3_ACTIVE):
                return {
                    "status": "error",
                    "error_code": "INVALID_STATE",
                    "message": "Start Round 3 after completing Round 2 before submitting a decision.",
                }

            case_row = cursor.execute(
                "SELECT * FROM round3_team_cases WHERE team_id = ?", (team_id,)
            ).fetchone()
            if not case_row:
                return {"status": "error", "error_code": "CASE_NOT_STARTED", "message": "Round 3 has not been initialized."}

            try:
                case_data = json.loads(case_row["case_data"])
            except json.JSONDecodeError:
                return {"status": "error", "error_code": "CASE_DATA_INVALID", "message": "Stored Round 3 case data is invalid."}

            valid_candidates = {item["id"] for item in case_data.get("candidates", [])}
            if candidate_id not in valid_candidates:
                return {"status": "error", "error_code": "INVALID_CANDIDATE", "message": "Choose Alpha, Beta, or Gamma."}

            is_correct = candidate_id == case_row["culprit_candidate_id"].strip().lower()
            points_awarded = 30 if is_correct else 0
            now = get_utc_now_iso()
            cursor.execute(
                "INSERT INTO round3_submissions "
                "(team_id, selected_candidate_id, selected_evidence_ids, is_correct, points_awarded, submitted_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (team_id, candidate_id, json.dumps(evidence_ids), int(is_correct), points_awarded, now),
            )
            cursor.execute(
                "INSERT INTO submissions "
                "(team_id, round, reference_id, answer, is_correct, points_awarded, submitted_at) "
                "VALUES (?, 3, ?, ?, ?, ?, ?)",
                (team_id, candidate_id, json.dumps({"candidate_id": candidate_id, "evidence_ids": evidence_ids}), int(is_correct), points_awarded, now),
            )

            r1_score = max(-25.0, min(50.0, float(team["round1_score"] or 0)))
            r2_score = max(0.0, min(20.0, float(team["round2_score"] or 0)))
            r3_score = float(points_awarded)
            total_score = round(r1_score + r2_score + r3_score, 2)
            cursor.execute(
                """
                UPDATE teams SET round3_score = ?, r3_score = ?, total_score = ?,
                    round3_completed_at = ?, status = 'FINISHED', current_state = 'COMPLETED',
                    updated_at = ? WHERE id = ?
                """,
                (r3_score, r3_score, total_score, now, now, team_id),
            )
            cursor.execute(
                "UPDATE round3_team_cases SET status = 'COMPLETED' WHERE team_id = ?",
                (team_id,),
            )
            cursor.execute(
                "INSERT INTO game_logs (team_id, event_type, event_data, created_at) "
                "VALUES (?, 'R3_SUBMIT', ?, ?)",
                (team_id, json.dumps({"selected_candidate": candidate_id, "evidence_ids": evidence_ids, "is_correct": is_correct, "points_awarded": points_awarded}), now),
            )
            connection.commit()
            return {
                "status": "success",
                "verdict_recorded": True,
                "completed_at": now,
                "round3_completed_at": now,
                "next_state": "COMPLETED",
                "current_state": "COMPLETED",
            }
        finally:
            connection.close()

    @staticmethod
    def get_round3_verdict(team_id: int) -> Dict[str, Any]:
        connection = get_connection()
        try:
            round2_service.ensure_tables(connection)
            cursor = connection.cursor()
            team = cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,)).fetchone()
            if not team:
                raise ValueError(f"Team ID {team_id} not found.")
            submission = cursor.execute(
                "SELECT * FROM round3_submissions WHERE team_id = ?", (team_id,)
            ).fetchone()
            if not submission:
                return {"status": "pending", "message": "No decision has been submitted for Round 3 yet.", "team_id": team_id, "team_name": team["team_name"], "current_state": team["current_state"]}

            round2_data = _round2_data(cursor, team_id, include_solution=True)
            full_case = _build_case(round2_data)
            candidates = {item["id"]: item for item in full_case["candidates"]}
            selected = candidates.get(submission["selected_candidate_id"])
            culprit = candidates[full_case["culprit_candidate_id"]]
            team_data = dict(team)
            m1_name = team_data.get("member_1_name") or team_data.get("member1_name") or ""
            m2_name = team_data.get("member_2_name") or team_data.get("member2_name") or ""
            m1_prn = team_data.get("member_1_prn") or team_data.get("member1_prn") or ""
            m2_prn = team_data.get("member_2_prn") or team_data.get("member2_prn") or ""
            return {
                "status": "success",
                "id": team_id,
                "team_id": team_id,
                "team_name": team["team_name"],
                "member_1_name": m1_name,
                "member_2_name": m2_name,
                "member_1_prn": m1_prn,
                "member_2_prn": m2_prn,
                "member1_name": m1_name,
                "member2_name": m2_name,
                "member1_prn": m1_prn,
                "member2_prn": m2_prn,
                "current_state": team["current_state"],
                "team_status": team_data.get("status") or "FINISHED",
                "round3_started_at": team["round3_started_at"],
                "round3_completed_at": team["round3_completed_at"],
                "submission": {
                    "selected_candidate_id": submission["selected_candidate_id"],
                    "selected_candidate_name": selected["name"] if selected else submission["selected_candidate_id"],
                    "selected_evidence_ids": _json_list(submission["selected_evidence_ids"]),
                    "submitted_at": submission["submitted_at"],
                },
                "verdict_details": {
                    "true_culprit_id": full_case["culprit_candidate_id"],
                    "true_culprit_name": culprit["name"],
                    "true_culprit_designation": culprit["designation"],
                    "valid_evidence_ids": full_case["valid_evidence_ids"],
                    "narrative_summary": full_case["narrative_summary"],
                },
                "round2_investigation": _client_case(full_case, round2_data)["round2_investigation"],
            }
        finally:
            connection.close()
