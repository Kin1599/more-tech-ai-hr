from datetime import datetime
from statistics import mean
from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from .helpers import _apply_mapped_to_vacancy, _vacancy_to_response
from ...models.models import HRProfile, User, Vacancy, JobApplication
from .utils import parse_vacancy_docx, to_decimal, vacancy_to_txt
from .schemas import ApplicantDetailResponse, CVEvaluation, InterviewDetail, InterviewVerdictEnum, VacancyDetailResponse, VacancyDetailApplicant


def get_vacancies(db: Session, offset: int = 0, limit: int = 20):
    vacancies = (
        db.query(Vacancy)
          .order_by(desc(Vacancy.date), desc(Vacancy.id))
          .offset(offset)
          .limit(limit)
          .all()
    )
    return [_vacancy_to_response(v) for v in vacancies]



def create_vacancy(db: Session, current_user: User, file):
    hr_profile: HRProfile | None = getattr(current_user, "hr_profile", None)
    if not hr_profile or not hr_profile.id:
        raise ValueError("У пользователя нет HR-профиля. Невозможно создать вакансию.")

    raw_fields: dict = parse_vacancy_docx(file)
    mapped = vacancy_to_txt(raw_fields, as_text=False)

    now_dt = datetime.now()
    vacancy = Vacancy(
        hr_id=hr_profile.id,
        department=hr_profile.department or "",
        # дефолты как при создании
        name="",
        status="active",
        date=now_dt,
        region="",
        city="",
        address="",
        offerType="TK",
        busyType="allTime",
        graph="",
        salaryMin=to_decimal(0),
        salaryMax=to_decimal(0),
        annualBonus=to_decimal(0),
        bonusType="",
        description="",
        prompt="",
        exp=0,
        degree=False,
        specialSoftware="",
        computerSkills="",
        foreignLanguages="",
        languageLevel="",
        businessTrips=False,
    )

    # применяем единый маппинг
    _apply_mapped_to_vacancy(vacancy, mapped)

    db.add(vacancy)
    db.commit()
    db.refresh(vacancy)

    return _vacancy_to_response(vacancy)



def change_vacancy(db: Session, vacancy_id: int, file):
    v = db.get(Vacancy, vacancy_id)
    if not v:
        raise FileNotFoundError("vacancy not found")

    raw_fields: dict = parse_vacancy_docx(file)
    mapped = vacancy_to_txt(raw_fields, as_text=False)

    _apply_mapped_to_vacancy(v, mapped)

    db.add(v)
    db.commit()
    db.refresh(v)

    return _vacancy_to_response(v)



def change_vacancy_status(db: Session, vacancy_id: int, new_status: str):
    v = db.get(Vacancy, vacancy_id)
    if not v:
        raise FileNotFoundError("vacancy not found")

    v.status = new_status
    db.add(v)
    db.commit()
    db.refresh(v)

    return {"status": v.status}



def get_vacancy_detail(db: Session, vacancy_id: int) -> VacancyDetailResponse:
    """Получить детальную информацию о вакансии и её откликах."""
    v = (
        db.query(Vacancy)
          .options(
              joinedload(Vacancy.job_applications).joinedload(JobApplication.applicant_profile),
              joinedload(Vacancy.job_applications).joinedload(JobApplication.cv_evaluations), 
          )
          .filter(Vacancy.id == vacancy_id)
          .first()
    )
    if not v:
        raise FileNotFoundError("vacancy not found")

    base = _vacancy_to_response(v)

    detail = []
    for job_application in (v.job_applications or []):
        prof = getattr(job_application, "applicant_profile", None)
        full_name = " ".join(filter(None, [
            getattr(prof, "name", None),
            getattr(prof, "surname", None),
        ])).strip() or "Кандидат"
        
        evaluations = getattr(job_application, "cv_evaluations", [])
        scores = [eval.score for eval in evaluations if isinstance(eval.score, (int, float)) and eval.name != "error"]
        score = float(mean(scores)) if scores else 0.0

        detail.append(VacancyDetailApplicant(
            applicationId=job_application.id,
            applicantId=job_application.applicant_id,
            name=full_name,
            score=score,
            status=job_application.status,
            checked=False,
        ))

    return VacancyDetailResponse(
        **base,
        detailResponses=detail
    )

def get_applicant_detail(db: Session, applicant_id: int, vacancy_id: int):
    """Получить детальную информацию о соискателе и его отклике на вакансию."""
    job_application = (
        db.query(JobApplication)
        .options(
            joinedload(JobApplication.cv_evaluations),
            joinedload(JobApplication.applicant_profile)
        )
        .filter(JobApplication.applicant_id == applicant_id, JobApplication.vacancy_id == vacancy_id)
        .first()
    )
    if not job_application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Application not found")

    cv_evaluations = [
        CVEvaluation(
            name=eval.name,
            score=eval.score,
            strengths=eval.strengths,
            weaknesses=eval.weaknesses
        )
        for eval in job_application.cv_evaluations
    ]

    interview = InterviewDetail(
        summary="Интервью ещё не проведено",
        strengths=["Не оценено"],
        weaknesses=["Не оценено"],
        recommendations="Нет рекомендаций",
        verdict=InterviewVerdictEnum.no_hire,
        risk_notes=["Интервью не проводилось"]
    )

    return ApplicantDetailResponse(
        status=job_application.status,
        cv=cv_evaluations,
        interview=interview if job_application.status in ["interview", "waitResult", "approved"] else None
    )
