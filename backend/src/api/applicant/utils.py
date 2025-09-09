from datetime import datetime
import os
from statistics import mean
import time

import jwt
from sqlalchemy import func

from .schemas import JobApplicationStatus
from .helpers import _extract_text_from_file
from ...core.database import SessionLocal
from ...ml.cv_estimator import evaluate_cv
from ...models.models import JobApplication, JobApplicationCVEvaluation, JobApplicationEvent, Vacancy, ApplicantResumeVersion

def format_datetime(dt: datetime) -> str:
    """Форматирует дату и время в ISO-формат."""
    return dt.isoformat() if dt else None

def evaluate_resume_background(job_application_id: int, vacancy_id: int, resume_id: int):
    """Фоновая задача для оценки резюме"""

    with SessionLocal() as db:
        job_application = db.query(JobApplication).filter_by(id=job_application_id).first()
        vacancy = db.query(Vacancy).filter_by(id=vacancy_id).first()
        resume = db.query(ApplicantResumeVersion).filter_by(id=resume_id).first()

        if not (job_application and vacancy and resume):
            return
        
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
        db.commit()

def _generate_join_token(api_key: str, api_secret: str, ttl: int = 60 * 60) -> str:
    """
    Генерация join-token (JWT) для VideoSDK.
    """
    now = int(time.time())
    payload = {
        "apikey": api_key,
        "permissions": ["allow_join", "allow_mod"],
        "iat": now,
        "exp": now + ttl,
        "version": 2,
    }
    return jwt.encode(payload, api_secret, algorithm="HS256")