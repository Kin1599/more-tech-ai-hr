import os
from typing import List, Optional
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ...models.models import (
    ApplicantProfile,
    ApplicantResumeVersion,
    JobApplication,
    JobApplicationEvent,
    Vacancy,
    HRProfile,
    Meeting,
)
from .schemas import JobApplicationListItem, JobApplicationDetail, HRBrief, InterviewLinkResponse, JobApplicationStatus
from .helpers import _vacancy_to_response
from .utils import _generate_join_token, evaluate_resume_background

def _hr_full_name(hr: HRProfile) -> str:
    parts = [hr.name, hr.patronymic, hr.surname]
    return " ".join([p for p in parts if p])

def get_vacancies(db: Session, offset: int = 0, limit: int = 20, vacancy_id: Optional[int] = None):

    if vacancy_id is not None:
        vacancy = db.query(Vacancy).filter_by(id=vacancy_id).first()
        if not vacancy:
            return []
        return [_vacancy_to_response(vacancy)]
    
    vacancies = (
        db.query(Vacancy)
          .order_by(desc(Vacancy.date), desc(Vacancy.id))
          .offset(offset)
          .limit(limit)
          .all()
    )

    return [_vacancy_to_response(v) for v in vacancies]

def list_job_applications(db: Session, user_id: int) -> List[JobApplicationListItem]:
    """
    Возвращает список заявок соискателя (по всем вакансиям) с нужными полями.
    """

    applicant_profile = db.query(ApplicantProfile).filter_by(user_id=user_id).first()
    if not applicant_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль соискателя не найден"
        )
    applicant_id = applicant_profile.id

    rows = (
        db.query(JobApplication, Vacancy, HRProfile)
        .join(Vacancy, JobApplication.vacancy_id == Vacancy.id)
        .join(HRProfile, Vacancy.hr_id == HRProfile.id)
        .filter(JobApplication.applicant_id == applicant_id)
        .all()
    )

    result: List[JobApplicationListItem] = []
    for app, v, hr in rows:
        result.append(
            JobApplicationListItem(
                applicationId=app.id,
                vacancyId=v.id,
                name=v.name or "",
                region=v.region,
                busyType=v.busyType.value if hasattr(v.busyType, "value") else v.busyType,
                hr=HRBrief(name=_hr_full_name(hr), contact=hr.contacts),
            )
        )
    return result
    


def get_job_application(db: Session, user_id: int, vacancy_id: int) -> JobApplicationDetail:
    """Получить детальную информацию об отклике соискателя на вакансию."""
    applicant_profile = db.query(ApplicantProfile).filter_by(user_id=user_id).first()
    if not applicant_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль соискателя не найден"
        )

    # Находим отклик
    application = (
        db.query(JobApplication)
        .filter_by(applicant_id=applicant_profile.id, vacancy_id=vacancy_id)
        .first()
    )
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отклик на вакансию не найден"
        )

    # Находим вакансию
    vacancy = db.query(Vacancy).filter_by(id=vacancy_id).first()
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вакансия не найдена"
        )

    # Находим HR-профиль
    hr = db.query(HRProfile).filter_by(id=vacancy.hr_id).first()
    if not hr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HR-профиль не найден"
        )

    # Находим последнее собрание
    meeting = (
        db.query(Meeting)
        .filter_by(application_id=application.id)
        .order_by(desc(Meeting.created_at))
        .first()
    )

    return JobApplicationDetail(
        applicationId=application.id,
        name=vacancy.name or "",
        region=vacancy.region,
        busyType=vacancy.busyType,
        hr=HRBrief(name=_hr_full_name(hr), contact=hr.contacts),
        status=application.status,
        interviewLink=meeting.meetLink if meeting else None,
        interviewRecommendation=meeting.hrContact if meeting else None,
    )


def get_interview_link(db: Session, user_id: int, vacancy_id: int) -> InterviewLinkResponse:
    applicant_profile = db.query(ApplicantProfile).filter_by(user_id=user_id).first()
    if not applicant_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль соискателя не найден"
        )

    # Проверяем, существует ли вакансия и активна ли она
    vacancy = db.query(Vacancy).filter_by(id=vacancy_id).first()
    if not vacancy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вакансия не найдена")
    if vacancy.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Вакансия не активна")

    application = (
        db.query(JobApplication)
        .filter_by(applicant_id=applicant_profile.id, vacancy_id=vacancy_id)
        .first()
    )
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отклик на вакансию не найден"
        )

    meeting = (
        db.query(Meeting)
        .filter_by(application_id=application.id)
        .order_by(desc(Meeting.created_at))
        .first()
    )

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Митинг для этого отклика не найден"
        )

    print(f"Meeting debug: roomId={meeting.roomId}, meetLink={meeting.meetLink}")
    
    api_key = os.getenv("VIDEOSDK_API_KEY")
    api_secret = os.getenv("VIDEOSDK_API_SECRET")
    if not api_key or not api_secret:
        raise RuntimeError("VIDEOSDK_API_KEY и VIDEOSDK_API_SECRET должны быть заданы")
    
    join_token = _generate_join_token(api_key, api_secret)

    return InterviewLinkResponse(
        roomId=meeting.roomId, 
        interviewLink=meeting.meetLink,
        token=join_token,
    )


def apply_for_job(db: Session, user_id: int, vacancy_id: int, background_tasks: BackgroundTasks) -> JobApplicationListItem:
    """Отклик на вакансию"""

    from ...ml.cv_estimator import evaluate_cv

    applicant_profile = db.query(ApplicantProfile).filter_by(user_id=user_id).first()
    if not applicant_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль соискателя не найден"
        )
    applicant_id = applicant_profile.id

    # Проверяем, существует ли вакансия и активна ли она
    vacancy = db.query(Vacancy).filter_by(id=vacancy_id).first()
    if not vacancy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вакансия не найдена")
    if vacancy.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Вакансия не активна")

    # Проверяем, есть ли у соискателя актуальное резюме
    resume = (
        db.query(ApplicantResumeVersion)
        .filter_by(applicant_id=applicant_id, is_current=True)
        .first()
    )
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У соискателя нет актуального резюме"
        )

    # Проверяем, не откликался ли соискатель на эту вакансию ранее
    existing_application = (
        db.query(JobApplication)
        .filter_by(applicant_id=applicant_id, vacancy_id=vacancy_id)
        .first()
    )
    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже откликнулись на эту вакансию"
        )
    
    job_application = JobApplication(
        vacancy_id=vacancy_id,
        applicant_id=applicant_id,
        resume_version_id=resume.id,
        status=JobApplicationStatus.cvReview,
    )

    db.add(job_application)
    db.flush()

    application_event = JobApplicationEvent(
        application_id=job_application.id,
        reqType='wait',
        status=JobApplicationStatus.cvReview,
        created_at=func.now(),
    )

    db.add(application_event)
    db.commit()

    background_tasks.add_task(evaluate_resume_background, job_application.id, vacancy.id, resume.id)

    hr = db.query(HRProfile).filter_by(id=vacancy.hr_id).first()
    if not hr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="HR-профиль не найден"
        )
    
    return JobApplicationListItem(
        applicationId=job_application.id, 
        vacancyId=vacancy.id,
        name=vacancy.name or "",
        region=vacancy.region,
        busyType=vacancy.busyType,
        hr=HRBrief(name=_hr_full_name(hr), contact=hr.contacts),
    )