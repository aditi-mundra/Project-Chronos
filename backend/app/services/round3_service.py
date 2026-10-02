"""
Project Chronos — Round 3 Service
Implements business logic, case assignment, validation, scoring, and telemetry
for Round 3: Final Decision / Wisdom Round.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..database.connection import get_connection
from ..data.round3_cases import get_case_for_team, get_sanitized_case_for_client
from ..utils.timers import get_utc_now_iso
from ..utils.validation import validate_round3_evidence

logger = logging.getLogger("project_chronos.round3_service")
logging.basicConfig(level=logging.INFO)

class Round3Service:
    @staticmethod
    def start_round3_for_team(team_id: int) -> Dict[str, Any]:
        """
        Initializes or resumes Round 3 for a given team.
        - Assigns or retrieves a deterministically seeded scenario.
        - Sets round3_started_at timestamp if starting for the first time.
        - Transitions state to ROUND_3_ACTIVE.
        - Logs telemetry in game_logs.
        """
        connection = get_connection()
        try:
            cursor = connection.cursor()
            
            # Fetch team record
            cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
            team = cursor.fetchone()
            
            if not team:
                raise ValueError(f"Team ID {team_id} not found in database.")
            
            current_state = team["current_state"] or "ROUND_2_COMPLETED"
            started_at = team["round3_started_at"]
            
            # Check if team already completed or submitted
            is_already_submitted = current_state in ("DECISION_SUBMITTED", "FINAL_REVEAL", "COMPLETED")
            
            # If starting fresh
            if not started_at and not is_already_submitted:
                started_at = get_utc_now_iso()
                new_state = "ROUND_3_ACTIVE"
                cursor.execute("""
                    UPDATE teams
                    SET round3_started_at = ?,
                        current_state = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (started_at, new_state, started_at, team_id))
                
                # Log R3_START event
                cursor.execute("""
                    INSERT INTO game_logs (team_id, event_type, event_data, created_at)
                    VALUES (?, 'R3_START', ?, ?)
                """, (team_id, json.dumps({"action": "ROUND_3_INITIALIZED", "started_at": started_at}), started_at))
                
                connection.commit()
            
            # Fetch or generate assigned case
            cursor.execute("SELECT * FROM round3_team_cases WHERE team_id = ?", (team_id,))
            case_row = cursor.fetchone()
            
            if case_row:
                raw_case_data = json.loads(case_row["case_data"])
                culprit_id = case_row["culprit_candidate_id"]
                valid_evs = json.loads(case_row["valid_evidence_ids"])
                full_case = raw_case_data
                full_case["culprit_candidate_id"] = culprit_id
                full_case["valid_evidence_ids"] = valid_evs
            else:
                # Deterministically generate and store case
                full_case = get_case_for_team(team_id)
                sanitized_case = get_sanitized_case_for_client(full_case)
                
                cursor.execute("""
                    INSERT INTO round3_team_cases (team_id, case_id, case_data, culprit_candidate_id, valid_evidence_ids, assigned_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    team_id,
                    full_case["case_id"],
                    json.dumps(sanitized_case),
                    full_case["culprit_candidate_id"],
                    json.dumps(full_case["valid_evidence_ids"]),
                    get_utc_now_iso()
                ))
                connection.commit()
            
            sanitized_client_case = get_sanitized_case_for_client(full_case)
            
            # Check for existing submission
            cursor.execute("SELECT * FROM round3_submissions WHERE team_id = ? ORDER BY id DESC LIMIT 1", (team_id,))
            sub_row = cursor.fetchone()
            
            has_submitted = sub_row is not None
            submission_data = None
            if sub_row:
                submission_data = {
                    "selected_candidate_id": sub_row["selected_candidate_id"],
                    "selected_evidence_ids": json.loads(sub_row["selected_evidence_ids"]),
                    "is_correct": bool(sub_row["is_correct"]),
                    "points_awarded": sub_row["points_awarded"],
                    "submitted_at": sub_row["submitted_at"]
                }
            
            return {
                "status": "success",
                "team_id": team_id,
                "team_name": team["team_name"],
                "team_state": team["current_state"] if is_already_submitted else "ROUND_3_ACTIVE",
                "round3_started_at": started_at,
                "is_submitted": has_submitted,
                "submission": submission_data,
                "case": sanitized_client_case
            }
        finally:
            connection.close()

    @staticmethod
    def get_team_scenario(team_id: int) -> Dict[str, Any]:
        """
        Retrieves the active Round 3 scenario and state for the specified team.
        Used for page reload recovery and client synchronization.
        """
        return Round3Service.start_round3_for_team(team_id)

    @staticmethod
    def submit_round3_decision(
        team_id: int,
        selected_candidate_id: str,
        selected_evidence_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Validates, grades, and records the final Round 3 decision.
        - Enforces minimum 2 supporting evidence constraint.
        - Prevents duplicate submission tampering (idempotency lock).
        - Computes Round 3 score (+30 for correct culprit, 0 for incorrect).
        - Updates total_score atomically in the master teams table.
        - Records round3_completed_at as tie-breaker timestamp.
        - Logs R3_SUBMIT in game_logs and submissions table.
        """
        # Validate evidence count
        valid, msg = validate_round3_evidence(selected_evidence_ids)
        if not valid:
            return {
                "status": "error",
                "error_code": "INVALID_EVIDENCE_COUNT",
                "message": msg
            }
        
        if not selected_candidate_id or not selected_candidate_id.strip():
            return {
                "status": "error",
                "error_code": "MISSING_CANDIDATE",
                "message": "A suspect candidate must be designated for final accusation."
            }

        connection = get_connection()
        try:
            cursor = connection.cursor()
            
            # Fetch team record
            cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
            team = cursor.fetchone()
            
            if not team:
                return {
                    "status": "error",
                    "error_code": "TEAM_NOT_FOUND",
                    "message": f"Team ID {team_id} does not exist."
                }
            
            # Idempotency check: verify if already submitted
            cursor.execute("SELECT * FROM round3_submissions WHERE team_id = ?", (team_id,))
            existing_submission = cursor.fetchone()
            if existing_submission:
                # Return previously locked verdict
                return {
                    "status": "success",
                    "message": "Decision already locked for this team.",
                    "verdict_recorded": True,
                    "is_already_locked": True,
                    "points_awarded": existing_submission["points_awarded"],
                    "is_correct": bool(existing_submission["is_correct"]),
                    "round3_score": team["round3_score"],
                    "total_score": team["total_score"],
                    "completed_at": team["round3_completed_at"],
                    "next_state": team["current_state"]
                }
            
            # Fetch team assigned case solution
            cursor.execute("SELECT * FROM round3_team_cases WHERE team_id = ?", (team_id,))
            case_row = cursor.fetchone()
            
            if not case_row:
                # Generate case if not yet in DB
                full_case = get_case_for_team(team_id)
                culprit_candidate_id = full_case["culprit_candidate_id"]
                valid_evidence_ids = full_case["valid_evidence_ids"]
                narrative_summary = full_case.get("narrative_summary", "")
            else:
                culprit_candidate_id = case_row["culprit_candidate_id"]
                valid_evidence_ids = json.loads(case_row["valid_evidence_ids"])
                full_case = get_case_for_team(team_id)
                narrative_summary = full_case.get("narrative_summary", "")
            
            # Evaluate correctness
            is_correct = (selected_candidate_id.strip() == culprit_candidate_id.strip())
            points_awarded = 30 if is_correct else 0
            
            # Calculate evidence matches for forensic breakdown
            matching_evidence = [ev for ev in selected_evidence_ids if ev in valid_evidence_ids]
            
            now_iso = get_utc_now_iso()
            
            # Insert into round3_submissions
            cursor.execute("""
                INSERT INTO round3_submissions (
                    team_id,
                    selected_candidate_id,
                    selected_evidence_ids,
                    is_correct,
                    points_awarded,
                    submitted_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                team_id,
                selected_candidate_id,
                json.dumps(selected_evidence_ids),
                1 if is_correct else 0,
                points_awarded,
                now_iso
            ))
            
            # Insert into general submissions table
            cursor.execute("""
                INSERT INTO submissions (
                    team_id,
                    round,
                    reference_id,
                    answer,
                    is_correct,
                    points_awarded,
                    submitted_at
                )
                VALUES (?, 3, ?, ?, ?, ?, ?)
            """, (
                team_id,
                selected_candidate_id,
                json.dumps({
                    "candidate_id": selected_candidate_id,
                    "evidence_ids": selected_evidence_ids
                }),
                1 if is_correct else 0,
                points_awarded,
                now_iso
            ))
            
            # Calculate updated total score
            r1_score = team["round1_score"] or 0
            r2_score = team["round2_score"] or 0
            r3_score = points_awarded
            total_score = r1_score + r2_score + r3_score
            
            # Update teams table
            cursor.execute("""
                UPDATE teams
                SET round3_score = ?,
                    total_score = ?,
                    round3_completed_at = ?,
                    current_state = 'COMPLETED',
                    status = 'FINISHED',
                    updated_at = ?
                WHERE id = ?
            """, (
                r3_score,
                total_score,
                now_iso,
                now_iso,
                team_id
            ))
            
            # Log telemetry event
            cursor.execute("""
                INSERT INTO game_logs (team_id, event_type, event_data, created_at)
                VALUES (?, 'R3_SUBMIT', ?, ?)
            """, (
                team_id,
                json.dumps({
                    "selected_candidate": selected_candidate_id,
                    "evidence_count": len(selected_evidence_ids),
                    "is_correct": is_correct,
                    "points_awarded": points_awarded,
                    "total_score": total_score,
                    "completed_at": now_iso
                }),
                now_iso
            ))
            
            connection.commit()
            
            logger.info(
                f"[ROUND 3 SUBMIT] Team {team_id} ({team['team_name']}): "
                f"Selected={selected_candidate_id}, Correct={is_correct}, Points={points_awarded}, Total={total_score}"
            )
            
            return {
                "status": "success",
                "verdict_recorded": True,
                "is_correct": is_correct,
                "points_awarded": points_awarded,
                "round3_score": r3_score,
                "total_score": total_score,
                "completed_at": now_iso,
                "next_state": "COMPLETED",
                "matching_evidence_count": len(matching_evidence),
                "narrative_summary": narrative_summary
            }
        finally:
            connection.close()

    @staticmethod
    def get_round3_verdict(team_id: int) -> Dict[str, Any]:
        """
        Retrieves the completed verdict, scoring summary, and post-investigation
        debrief for the final reveal screen.
        """
        connection = get_connection()
        try:
            cursor = connection.cursor()
            
            cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
            team = cursor.fetchone()
            if not team:
                raise ValueError(f"Team ID {team_id} not found.")
            
            cursor.execute("SELECT * FROM round3_submissions WHERE team_id = ? ORDER BY id DESC LIMIT 1", (team_id,))
            submission = cursor.fetchone()
            
            full_case = get_case_for_team(team_id)
            
            if not submission:
                return {
                    "status": "pending",
                    "message": "No decision has been submitted for Round 3 yet.",
                    "team_id": team_id,
                    "team_name": team["team_name"],
                    "current_state": team["current_state"]
                }
            
            selected_cand_id = submission["selected_candidate_id"]
            selected_cand = next((c for c in full_case["candidates"] if c["id"] == selected_cand_id), None)
            culprit_cand = next((c for c in full_case["candidates"] if c["id"] == full_case["culprit_candidate_id"]), None)
            
            return {
                "status": "success",
                "team_id": team_id,
                "team_name": team["team_name"],
                "member_1_name": team["member_1_name"],
                "member_2_name": team["member_2_name"],
                "member_1_prn": team["member_1_prn"],
                "member_2_prn": team["member_2_prn"],
                "current_state": team["current_state"],
                "round1_score": team["round1_score"],
                "round2_score": team["round2_score"],
                "round3_score": team["round3_score"],
                "total_score": team["total_score"],
                "round3_started_at": team["round3_started_at"],
                "round3_completed_at": team["round3_completed_at"],
                "submission": {
                    "selected_candidate_id": selected_cand_id,
                    "selected_candidate_name": selected_cand["name"] if selected_cand else selected_cand_id,
                    "selected_evidence_ids": json.loads(submission["selected_evidence_ids"]),
                    "is_correct": bool(submission["is_correct"]),
                    "points_awarded": submission["points_awarded"],
                    "submitted_at": submission["submitted_at"]
                },
                "verdict_details": {
                    "true_culprit_id": full_case["culprit_candidate_id"],
                    "true_culprit_name": culprit_cand["name"] if culprit_cand else "",
                    "true_culprit_designation": culprit_cand["designation"] if culprit_cand else "",
                    "valid_evidence_ids": full_case["valid_evidence_ids"],
                    "narrative_summary": full_case.get("narrative_summary", "")
                }
            }
        finally:
            connection.close()
