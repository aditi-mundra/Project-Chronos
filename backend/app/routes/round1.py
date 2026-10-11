from fastapi import APIRouter

from ..services.round1_service import (
    get_round1_items,
    submit_answer,
    finish_round1,
    get_round1_status
)

router = APIRouter()


@router.get("/items")
def get_items(team_id: int):
    """
    Get the 25 Round 1 images assigned to the team.
    """
    return get_round1_items(team_id)


from typing import Optional
from fastapi import HTTPException
from pydantic import BaseModel


class Round1SubmitPayload(BaseModel):
    team_id: Optional[int] = None
    item_id: Optional[int] = None
    answer: Optional[str] = None


@router.post("/submit")
def submit(
    team_id: Optional[int] = None,
    item_id: Optional[int] = None,
    answer: Optional[str] = None,
    payload: Optional[Round1SubmitPayload] = None
):
    """
    Submit a classification answer for one image. Supports both query params and JSON body.
    """
    tid = payload.team_id if (payload and payload.team_id is not None) else team_id
    iid = payload.item_id if (payload and payload.item_id is not None) else item_id
    ans = payload.answer if (payload and payload.answer is not None) else answer

    if tid is None or iid is None or ans is None:
        raise HTTPException(status_code=422, detail="team_id, item_id, and answer are required.")

    return submit_answer(
        tid,
        iid,
        ans
    )


@router.post("/finish")
@router.post("/complete")
def finish(team_id: int):
    """
    Finish/check Round 1.

    The backend verifies that all assigned
    items have been submitted before allowing
    the team to proceed to Round 2.
    """
    return finish_round1(team_id)


@router.get("/status")
def status(team_id: int):
    """
    Round 1 progress for a team: whether it has started or completed, the
    remaining time (server clock), and the result once completed.
    """
    return get_round1_status(team_id)
