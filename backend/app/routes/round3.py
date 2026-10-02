"""
Project Chronos — Round 3 API Routes
FastAPI endpoints for Round 3: Final Decision / Wisdom Round.
"""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from ..services.round3_service import Round3Service
from ..data.round3_cases import ROUND_3_SCENARIO_TEMPLATES

router = APIRouter(prefix="/api/round3", tags=["Round 3: Final Decision"])

# =============================================================================
# Pydantic Schemas
# =============================================================================

class Round3StartRequest(BaseModel):
    team_id: int = Field(..., description="Unique database ID of the investigating team", example=1)

class Round3SubmitRequest(BaseModel):
    team_id: int = Field(..., description="Unique database ID of the team", example=1)
    selected_candidate_id: str = Field(..., description="ID of the accused suspect", example="cand_a")
    selected_evidence_ids: List[str] = Field(..., min_items=2, description="At least two corroborating evidence IDs", example=["ev_01_timeline", "ev_04_auth"])

# =============================================================================
# Endpoints
# =============================================================================

@router.post("/start", summary="Start or Resume Round 3")
def start_round3(payload: Round3StartRequest):
    """
    Initializes Round 3 for the team:
    - Sets state to ROUND_3_ACTIVE and logs round3_started_at.
    - Generates or retrieves the assigned scenario deterministically.
    - Returns sanitized scenario data without secret solution keys.
    """
    try:
        result = Round3Service.start_round3_for_team(payload.team_id)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to start Round 3: {str(ex)}")

@router.get("/scenario", summary="Get Current Scenario for Team")
def get_scenario(team_id: int = Query(..., description="Team ID to fetch scenario for", example=1)):
    """
    Fetches the team's assigned scenario and active state for page refresh recovery.
    """
    try:
        result = Round3Service.get_team_scenario(team_id)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch scenario: {str(ex)}")

@router.post("/submit", summary="Submit Final Accusation Decision")
def submit_decision(payload: Round3SubmitRequest):
    """
    Evaluates and records the team's final decision:
    - Validates minimum 2 supporting evidence items.
    - Evaluates suspect against secret case solution.
    - Awards 30 points for correct culprit, 0 for incorrect.
    - Atomically updates total_score and round3_completed_at.
    - Enforces idempotency to prevent duplicate score awards.
    """
    try:
        result = Round3Service.submit_round3_decision(
            team_id=payload.team_id,
            selected_candidate_id=payload.selected_candidate_id,
            selected_evidence_ids=payload.selected_evidence_ids
        )
        if result.get("status") == "error":
            error_code = result.get("error_code")
            if error_code == "TEAM_NOT_FOUND":
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("message"))
            elif error_code in ("INVALID_EVIDENCE_COUNT", "MISSING_CANDIDATE"):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result.get("message"))
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Submission processing error: {str(ex)}")

@router.get("/verdict", summary="Get Verdict and Narrative Debrief")
def get_verdict(team_id: int = Query(..., description="Team ID to fetch verdict for", example=1)):
    """
    Retrieves the final decision outcome, forensic breakdown, and narrative resolution
    for the team's completion view.
    """
    try:
        result = Round3Service.get_round3_verdict(team_id)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch verdict: {str(ex)}")

@router.get("/debug-cases", summary="List All Scenario Templates (Admin / Testing)")
def list_debug_cases():
    """
    Returns the master catalog of scenario templates for inspection and verification.
    """
    return {
        "count": len(ROUND_3_SCENARIO_TEMPLATES),
        "cases": ROUND_3_SCENARIO_TEMPLATES
    }
