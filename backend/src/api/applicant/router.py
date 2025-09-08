from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...models.models import User
from ...core.security import get_current_applicant_user
from ...core.database import get_session
from .schemas import InterviewLinkResponse, JobApplicationDetail, JobApplicationListItem, VacancyResponse
from .service import apply_for_job, get_interview_link, get_job_application, get_vacancies, list_job_applications

router = APIRouter(tags=["applicant"])

@router.get('/vacancies', response_model=list[VacancyResponse], dependencies=[Depends(get_current_applicant_user)])
def get_vacancies_endpoint(
    offset: int = Query(0, ge=0, description="Смещение (0, 20, 40, ...)"),
    limit: int = Query(20, ge=1, le=200, description="Размер страницы (1..200)"),
    db: Session = Depends(get_session),
):
    """Постраничный список вакансий"""
    return get_vacancies(db, offset, limit)

@router.get('/vacancies/{vacancy_id}', response_model=list[VacancyResponse], dependencies=[Depends(get_current_applicant_user)])
def get_detail_vacancy_endpoint(
    vacancy_id: int,
    db: Session = Depends(get_session),
):
    """Получить детальную информацию о вакансии"""
    return get_vacancies(db, vacancy_id=vacancy_id)

@router.get("/job_applications", response_model=list[JobApplicationListItem])
def list_job_applications_endpoint(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_applicant_user),
):
    """Получить список всех откликов для соискателя"""
    items = list_job_applications(db, current_user.id)
    return items

@router.get("/job_applications/{vacancy_id}", response_model=JobApplicationDetail)
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

@router.get("/job_applications/{vacancyId}/interview", response_model=InterviewLinkResponse)
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

@router.post("/job_applications/{vacancy_id}", response_model=JobApplicationListItem)
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