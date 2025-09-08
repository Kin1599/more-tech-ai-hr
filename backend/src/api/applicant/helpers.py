from ...models.models import Vacancy

def _vacancy_to_response(v: Vacancy) -> dict:
    """Маппинг ORM -> API"""
    return {
        "vacancyId": v.id,
        "name": v.name or "",
        "status": v.status,
        "department": v.department or "",
        "date": v.date,
        "region": v.region,
        "city": v.city,
        "address": v.address,
        "offerType": v.offerType,
        "busyType": v.busyType,
        "graph": v.graph,
        "salaryMin": float(v.salaryMin or 0),
        "salaryMax": float(v.salaryMax or 0),
        "annualBonus": float(v.annualBonus or 0),
        "bonusType": v.bonusType,
        "description": v.description,
        "prompt": v.prompt,
        "exp": v.exp,
        "degree": bool(v.degree) if v.degree is not None else None,
        "specialSoftware": v.specialSoftware,
        "computerSkills": v.computerSkills,
        "foreignLanguages": v.foreignLanguages,
        "languageLevel": v.languageLevel,
        "businessTrips": bool(v.businessTrips) if v.businessTrips is not None else None,
    }