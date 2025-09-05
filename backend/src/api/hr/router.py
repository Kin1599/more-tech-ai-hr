from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.security import get_current_hr_user
from ...core.database import get_session
from .schemas import VacancyResponse, ApplicationResponse, ApplicantDetailResponse, EventRequest, EventResponse, ApplicantSummaryResponse
from .service import get_vacancies, get_vacancy_applications, get_applicant_details, update_application_event, get_applicant_summary

router = APIRouter(tags=["hr"])

@router.get('/vacancies', response_model=list[VacancyResponse], dependencies=[Depends(get_current_hr_user)])
def get_vacancies_endpoint(db: Session = Depends(get_session)):
    return get_vacancies(db)

@router.get('/vacancies/{vacancy_id}', response_model=list[ApplicationResponse], dependencies=[Depends(get_current_hr_user)])
def get_vacancy_applications_endpoint(vacancy_id: int, db: Session = Depends(get_session)):
    applications = get_vacancy_applications(db, vacancy_id)
    if not applications:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    return applications

@router.get('/vacancies/{vacancy_id}/{applicant_id}', response_model=ApplicantDetailResponse, dependencies=[Depends(get_current_hr_user)])
def get_applicant_details_endpoint(vacancy_id: int, applicant_id: int, db: Session = Depends(get_session)):
    details = get_applicant_details(db, vacancy_id, applicant_id)
    if not details:
        raise HTTPException(status_code=404, detail="Applicant or application not found")
    return details

@router.post('/applicants/{applicant_id}', response_model=EventResponse, dependencies=[Depends(get_current_hr_user)])
def update_application_event_endpoint(applicant_id: int, request: EventRequest, db: Session = Depends(get_session)):
    result = update_application_event(db, applicant_id, request.reqType)
    if not result:
        raise HTTPException(status_code=404, detail="Applicant not found")
    return result

@router.get('/applicants/{applicant_id}', response_model=ApplicantSummaryResponse, dependencies=[Depends(get_current_hr_user)])
def get_applicant_summary_endpoint(applicant_id: int, db: Session = Depends(get_session)):
    summary = get_applicant_summary(db, applicant_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Applicant not found")
    return summary