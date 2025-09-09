from pathlib import Path

import PyPDF2
from docx import Document
from fastapi import HTTPException, status
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
