from sqlalchemy.orm import Session
from ...models.models import Vacancy, Application, ApplicantProfile, ApplicationEvent
from .utils import format_datetime, calculate_sum_grade

def get_vacancies(db: Session):
    """Получает список всех вакансий с количеством откликов."""
    vacancies = db.query(Vacancy).all()
    return [
        {
            "vacancyId": v.id,
            "name": v.name,
            "status": v.status,
            "department": v.department,
            "responses": len(v.applications),
            "responsesWithout": len([a for a in v.applications if a.status == "review"]),
            "date": format_datetime(v.date)
        }
        for v in vacancies
    ]

def get_vacancy_applications(db: Session, vacancy_id: int):
    """Получает список заявок для указанной вакансии."""
    applications = db.query(Application).filter_by(vacancy_id=vacancy_id).all()
    return [
        {
            "applicantId": a.applicant_id,
            "name": a.applicant_profile.name,
            "status": a.status,
            "soft": float(a.soft) if a.soft else None,
            "tech": float(a.tech) if a.tech else None,
            "salary": float(a.salary) if a.salary else None,
            "contacts": a.contacts,
            "sumGrade": calculate_sum_grade(a.soft, a.tech)
        }
        for a in applications
    ]

def get_applicant_details(db: Session, vacancy_id: int, applicant_id: int):
    """Получает детали соискателя для указанной вакансии и заявки."""
    application = db.query(Application).filter_by(vacancy_id=vacancy_id, applicant_id=applicant_id).first()
    if not application:
        return None
    applicant = application.applicant_profile
    return {
        "name": applicant.name,
        "surname": applicant.surname,
        "patronymic": applicant.patronymic,
        "status": application.status,
        "soft": float(application.soft) if application.soft else None,
        "tech": float(application.tech) if application.tech else None,
        "salary": float(application.salary) if application.salary else None,
        "contacts": application.contacts,
        "sumGrade": calculate_sum_grade(application.soft, application.tech),
        "cv": applicant.cv
    }

def update_application_event(db: Session, applicant_id: int, req_type: str):
    """Обновляет статус заявки на основе типа запроса."""
    application = db.query(Application).filter_by(applicant_id=applicant_id).first()
    if not application:
        return None
    event = ApplicationEvent(application_id=application.id, reqType=req_type, status=application.status)
    db.add(event)
    db.commit()
    return {"status": application.status}

def get_applicant_summary(db: Session, applicant_id: int):
    """Получает сводку соискателя."""
    applicant = db.query(ApplicantProfile).filter_by(id=applicant_id).first()
    if not applicant:
        return None
    return {"summary": applicant.summary}