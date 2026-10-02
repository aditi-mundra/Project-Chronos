"""
Project Chronos — Validation and Integrity Utilities
State machine transition guards and request validation rules.
"""

from typing import List, Tuple

VALID_GAME_STATES = [
    "REGISTERED",
    "READY",
    "ROUND_1_ACTIVE",
    "ROUND_1_COMPLETED",
    "ROUND_2_LOCKED",
    "ROUND_2_ACTIVE",
    "OMEGA_DISCOVERED",
    "ROUND_2_COMPLETED",
    "ROUND_3_ACTIVE",
    "DECISION_SUBMITTED",
    "FINAL_REVEAL",
    "COMPLETED",
    "TIMEOUT"
]

def is_valid_state_transition(current_state: str, target_state: str) -> bool:
    """
    Checks whether a state machine transition is allowed.
    Permits direct recovery or advancement according to Project Chronos rules.
    """
    if current_state == target_state:
        return True
    
    # Specific allowed transitions
    allowed_map = {
        "REGISTERED": ["READY", "ROUND_1_ACTIVE"],
        "READY": ["ROUND_1_ACTIVE"],
        "ROUND_1_ACTIVE": ["ROUND_1_COMPLETED", "TIMEOUT"],
        "ROUND_1_COMPLETED": ["ROUND_2_LOCKED", "ROUND_2_ACTIVE", "ROUND_3_ACTIVE"],
        "ROUND_2_LOCKED": ["ROUND_2_ACTIVE"],
        "ROUND_2_ACTIVE": ["OMEGA_DISCOVERED", "ROUND_2_COMPLETED", "TIMEOUT", "ROUND_3_ACTIVE"],
        "OMEGA_DISCOVERED": ["ROUND_2_COMPLETED", "ROUND_3_ACTIVE"],
        "ROUND_2_COMPLETED": ["ROUND_3_ACTIVE"],
        "ROUND_3_ACTIVE": ["DECISION_SUBMITTED", "COMPLETED", "TIMEOUT"],
        "DECISION_SUBMITTED": ["FINAL_REVEAL", "COMPLETED"],
        "FINAL_REVEAL": ["COMPLETED"],
        "COMPLETED": []
    }
    
    # Allow developer / flexible transitions for debugging if state is unknown
    if current_state not in allowed_map:
        return True
    
    return target_state in allowed_map.get(current_state, [])

def validate_round3_evidence(evidence_ids: List[str]) -> Tuple[bool, str]:
    """
    Validates Round 3 evidence requirements:
    Must select at least 2 pieces of supporting evidence.
    """
    if not isinstance(evidence_ids, list):
        return False, "Evidence selection must be a list of evidence IDs."
    if len(evidence_ids) < 2:
        return False, "A minimum of two (2) verified supporting evidence items must be selected."
    return True, ""
