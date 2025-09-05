from sqlalchemy.orm import Session
from ...models.models import Application, Meeting, Vacancy

def get_application_status(db: Session, applicant_id: int, vacancy_id: int):
    """Получает статус заявки и данные встречи для соискателя и вакансии."""
    application = db.query(Application).filter_by(applicant_id=applicant_id, vacancy_id=vacancy_id).first()
    if not application:
        return None
    meeting = db.query(Meeting).filter_by(application_id=application.id).first()
    vacancy = db.query(Vacancy).filter_by(id=vacancy_id).first()
    
    response = {
        "vacancyData": {"id": vacancy.id, "name": vacancy.name} if vacancy else {},
        "status": meeting.status if meeting else None,
        "hrContact": meeting.hrContact if meeting else None,
        "meetLink": meeting.meetLink if meeting else None,
        "calendarLink": meeting.calendarLink if meeting else None
    }
    return response

def get_applicant_applications(db: Session, applicant_id: int):
    """Получает список всех заявок соискателя."""
    applications = db.query(Application).filter_by(applicant_id=applicant_id).all()
    return [
        {
            "status": a.status,
            "vacancyID": a.vacancy_id,
            "name": a.vacancy.name if a.vacancy else "Unknown",
            "tribe": a.vacancy.department if a.vacancy else "Unknown",
            "otherInfo": a.contacts
        }
        for a in applications
    ]