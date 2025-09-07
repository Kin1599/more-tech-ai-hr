from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from .helpers import _apply_mapped_to_vacancy, _map_application_status, _vacancy_to_response
from ...models.models import HRProfile, User, Vacancy, JobApplication
from .utils import parse_vacancy_docx, to_decimal, vacancy_to_txt



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



def get_vacancy_detail(db: Session, vacancy_id: int) -> dict:
    v = (
        db.query(Vacancy)
          .options(
              joinedload(Vacancy.job_applications).joinedload(JobApplication.applicant_profile),
              joinedload(Vacancy.job_applications).joinedload(JobApplication.meetings), 
          )
          .filter(Vacancy.id == vacancy_id)
          .first()
    )
    if not v:
        raise FileNotFoundError("vacancy not found")

    base = _vacancy_to_response(v)

    detail = []
    for app in (v.job_applications or []):
        prof = getattr(app, "applicant_profile", None)
        full_name = " ".join(filter(None, [
            getattr(prof, "name", None),
            getattr(prof, "surname", None),
        ])).strip() or "Кандидат"

        try:
            score = float(app.sumGrade) if app.sumGrade is not None else float(app.soft or 0) + float(app.tech or 0)
        except Exception:
            score = 0.0

        detail.append({
            "applicantId": getattr(app, "applicant_id", None),
            "name": full_name,
            "score": score,
            "status": _map_application_status(app),
            "checked": False,
        })

    base["detailResponses"] = detail
    return base