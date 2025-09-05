from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.database import get_session
from .schemas import MeetingResponse, ApplicationStatusResponse
from .service import get_application_status, get_applicant_applications

router = APIRouter(tags=["applicant"])

@router.get('/{applicant_id}/{vacancy_id}', response_model=MeetingResponse)
def get_application_status_endpoint(applicant_id: int, vacancy_id: int, db: Session = Depends(get_session)):
    status = get_application_status(db, applicant_id, vacancy_id)
    if not status:
        raise HTTPException(status_code=404, detail="Application or meeting not found")
    return status

@router.get('/{applicant_id}', response_model=list[ApplicationStatusResponse])
def get_applicant_applications_endpoint(applicant_id: int, db: Session = Depends(get_session)):
    applications = get_applicant_applications(db, applicant_id)
    if not applications:
        raise HTTPException(status_code=404, detail="No applications found")
    return applications