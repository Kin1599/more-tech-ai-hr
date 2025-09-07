from ...models.models import Vacancy
from .utils import to_decimal

def _map_application_status(app) -> str:
    """Сворачивает статусы встреч/заявки в единый статус на карточке."""
    meetings = getattr(app, "meetings", None) or []
    if meetings:
        last = max(meetings, key=lambda m: (m.id or 0))
        ms = (getattr(last, "status", "") or "").strip()
        return {
            "reject": "rejected",
            "approve": "approved",
            "cvReview": "cvReview",
            "waitPickTime": "interview",
            "waitMeeting": "interview",
            "waitResult": "waitResult",
        }.get(ms, "cvReview")

    s = (getattr(app, "status", "") or "").strip()
    return {
        "reject": "rejected",
        "approve": "approved",
        "review": "cvReview",
        "screening": "cvReview",
        "result": "waitResult",
    }.get(s, "cvReview")

def _vacancy_to_response(v: Vacancy) -> dict:
    """Маппинг ORM -> API"""
    return {
        "vacancyId": v.id,
        "name": v.name or "",
        "status": v.status,
        "department": v.department or "",
        "date": v.date,

        "responses": len(v.applications or []),
        "responsesWithout": len([a for a in (v.applications or []) if getattr(a, "status", None) == "review"]),

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
        "promt": v.promt,
        "exp": v.exp,
        "degree": bool(v.degree) if v.degree is not None else None,
        "specialSoftware": v.specialSoftware,
        "computerSkills": v.computerSkills,
        "foreignLanguages": v.foreignLanguages,
        "languageLevel": v.languageLevel,
        "businessTrips": bool(v.businessTrips) if v.businessTrips is not None else None,
    }

def _apply_mapped_to_vacancy(v: Vacancy, mapped: dict) -> None:
    """Единый маппинг полей из распарсенного DOCX в модель Vacancy."""
    v.name = mapped.get("name") or v.name
    v.status = mapped.get("status") or v.status
    v.region = mapped.get("region") or ""
    v.city = mapped.get("city") or ""
    v.address = mapped.get("address") or ""
    v.offerType = mapped.get("offerType") or v.offerType
    v.busyType = mapped.get("busyType") or v.busyType
    v.graph = mapped.get("graph") or ""
    v.salaryMin = to_decimal(mapped.get("salaryMin"))
    v.salaryMax = to_decimal(mapped.get("salaryMax"))
    v.annualBonus = to_decimal(mapped.get("annualBonus"))
    v.bonusType = mapped.get("bonusType") or ""
    v.description = mapped.get("description") or ""
    v.promt = mapped.get("promt") or ""
    v.exp = int(mapped.get("exp") or 0)
    v.degree = bool(mapped.get("degree") or False)
    v.specialSoftware = mapped.get("specialSoftware") or ""
    v.computerSkills = mapped.get("computerSkills") or ""
    v.foreignLanguages = mapped.get("foreignLanguages") or ""
    v.languageLevel = mapped.get("languageLevel") or ""
    v.businessTrips = bool(mapped.get("businessTrips") or False)
