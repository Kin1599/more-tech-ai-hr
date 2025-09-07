from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...models.models import User
from ...core.security import get_current_applicant_user
from ...core.database import get_session
from .schemas import JobApplicationListItem
from .service import apply_for_job, get_interview_link, get_job_application, list_job_applications

router = APIRouter(tags=["applicant"])

@router.get("/job_applications", response_model=list[JobApplicationListItem])
def list_job_applications_endpoint(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_applicant_user),
):
    """Получить список всех откликов для соискателя"""
    items = list_job_applications(db, current_user.id)
    return items

@router.get("/job_applications/{vacancy_id}")
def get_job_application_endpoint(
    vacancy_id: int,
    current_user: User = Depends(get_current_applicant_user),
    db: Session = Depends(get_session),
):
    """Получить детальную информацию об отклике для соискателя"""
    try:
        return get_job_application(db, current_user.id, vacancy_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/job_applications/{vacancyId}/interview")
def get_interview_link_endpoint(
    vacancy_id: int,
    current_user: User = Depends(get_current_applicant_user),
    db: Session = Depends(get_session),
):
    """Получить ссылку на созвон для соискателя"""
    try:
        return get_interview_link(db, current_user.id, vacancy_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/job_applications/{vacancy_id}")
def apply_for_job_endpoint(
    vacancy_id: int,
    current_user: User = Depends(get_current_applicant_user),
    db: Session = Depends(get_session),
):
    """Откликнуться на вакансию"""
    try:
        return apply_for_job(db, current_user.id, vacancy_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))