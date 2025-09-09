from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_session
from ...core.security import get_current_hr_user
from .schemas import (
    CreateRoomRequest,
    CreateRoomResponse,
    StartAgentRequest,
    SubmitResultsRequest,
    SubmitResultsResponse,
)
from .service import (
    create_videosdk_room,
    persist_meeting_for_application,
    start_agent_process,
    save_interview_results,
)


router = APIRouter(tags=["interview"])


@router.post("/create_room", response_model=CreateRoomResponse, dependencies=[Depends(get_current_hr_user)])
def create_room(
    payload: CreateRoomRequest,
    db: Session = Depends(get_session),
):
    try:
        room_id, playground = create_videosdk_room()
        persist_meeting_for_application(db, payload.jobApplicationId, room_id, playground)
        return CreateRoomResponse(roomId=room_id, playgroundLink=playground)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/start_agent", dependencies=[Depends(get_current_hr_user)])
def start_agent(
    payload: StartAgentRequest,
):
    try:
        pid = start_agent_process(payload.roomId)
        return {"pid": pid}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/submit_results", response_model=SubmitResultsResponse, dependencies=[Depends(get_current_hr_user)])
def submit_results(
    payload: SubmitResultsRequest,
    db: Session = Depends(get_session),
):
    try:
        interview = save_interview_results(
            db=db,
            job_application_id=payload.jobApplicationId,
            summary=payload.summary,
            strengths=payload.strengths,
            weaknesses=payload.weaknesses,
            recommendations=payload.recommendations,
            verdict=payload.verdict,
        )
        return SubmitResultsResponse(interviewId=interview.id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



