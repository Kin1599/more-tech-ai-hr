import os
from pathlib import Path
from statistics import mean
from typing import List
import PyPDF2
from docx import Document
from fastapi import HTTPException, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ...models.models import (
    ApplicantProfile,
    ApplicantResumeVersion,
    JobApplication,
    JobApplicationCVEvaluation,
    JobApplicationEvent,
    Vacancy,
    HRProfile,
    Meeting,
)
from .schemas import JobApplicationListItem, JobApplicationDetail, HRBrief, InterviewLinkResponse, JobApplicationStatus

def _hr_full_name(hr: HRProfile) -> str:
    parts = [hr.name, hr.patronymic, hr.surname]
    return " ".join([p for p in parts if p])



def _extract_text_from_file(file_path: str) -> str:
    """Извлечь текст из файла резюме (.pdf, .docx, .txt)."""
    ext = Path(file_path).suffix.lower()
    try:
        if ext == ".pdf":
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text.strip()
        elif ext == ".docx" or ext == '.doc':
            doc = Document(file_path)
            return " ".join([para.text for para in doc.paragraphs]).strip()
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read().strip()
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Неподдерживаемый формат файла: {ext}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при извлечении текста из резюме: {str(e)}"
        )



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
    for _, v, hr in rows:
        result.append(
            JobApplicationListItem(
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
    
    return InterviewLinkResponse(interviewLink=meeting.meetLink if meeting else None)


def apply_for_job(db: Session, user_id: int, vacancy_id: int) -> JobApplicationListItem:
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

    model = "qwen/qwen3-32b"

    try:
        resume_text = _extract_text_from_file(resume.storage_path)
        job_description = vacancy.description or ""
        criteria = ["hard skills", "soft skills", "scalability mindset"]
        evaluation = evaluate_cv(
            job_description=job_description,
            resume_text=resume_text,
            criteria=criteria,
            api_key=os.getenv("GROQ_API_KEY"),
            model=model,
        )
        
        if evaluation.get("parse_error", False):
            cv_evaluation = JobApplicationCVEvaluation(
                job_application_id=job_application.id,
                resume_version_id=resume.id,
                model=model,
                name="error",
                score=0,
                strengths=[],
                weaknesses=[f"Ошибка парсинга ответа модели: {evaluation['raw_model_output']}"],
                created_at=func.now(),
                updated_at=func.now(),
            )
            db.add(cv_evaluation)
            # Устанавливаем wait при ошибке парсинга
            job_application.status = JobApplicationStatus.cvReview
            req_type = "wait"
        else: 
            for crit in evaluation["criteria"]:
                cv_evaluation = JobApplicationCVEvaluation(
                    job_application_id=job_application.id,
                    resume_version_id=resume.id,
                    model=model,
                    name=crit["name"],
                    score=crit["score"],
                    strengths=crit["strengths"],
                    weaknesses=crit["weaknesses"],
                    created_at=func.now(),
                    updated_at=func.now(),
                )
                db.add(cv_evaluation)

                scores = [crit["score"] for crit in evaluation["criteria"] if isinstance(crit["score"], (int, float))]
                average_score = mean(scores) if scores else 0

                if average_score < 50:
                    job_application.status = JobApplicationStatus.rejected
                    req_type = "reject"
                else:
                    job_application.status = JobApplicationStatus.interview
                    req_type = "next"

    except Exception as e:
        print(f"Ошибка при оценке резюме: {str(e)}")
        cv_evaluation = JobApplicationCVEvaluation(
            job_application_id=job_application.id,
            resume_version_id=resume.id,
            model=model,
            name="error",
            score=0,
            strengths=[],
            weaknesses=[f"Ошибка оценки: {str(e)}"],
            created_at=func.now(),
            updated_at=func.now(),
        )
        db.add(cv_evaluation)
        job_application.status = JobApplicationStatus.waitResult
        req_type = "wait"

    application_event = JobApplicationEvent(
        application_id=job_application.id,
        reqType=req_type,
        status=job_application.status,
        created_at=func.now(),  
    )
    db.add(application_event)
    db.flush()

    db.commit()

    hr = db.query(HRProfile).filter_by(id=vacancy.hr_id).first()
    if not hr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="HR-профиль не найден"
        )
    
    return JobApplicationListItem(
        vacancyId=vacancy.id,
        name=vacancy.name or "",
        region=vacancy.region,
        busyType=vacancy.busyType,
        hr=HRBrief(name=_hr_full_name(hr), contact=hr.contacts),
    )