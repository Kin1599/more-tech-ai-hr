from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class VacancyStatusEnum(str, Enum):
    hold = "hold"
    found = "found"
    approve = "approve"

class ApplicationStatusEnum(str, Enum):
    review = "review"
    screening = "screening"
    result = "result"
    reject = "reject"
    approve = "approve"

class VacancyResponse(BaseModel):
    vacancyId: int
    name: str
    status: VacancyStatusEnum
    department: str
    responses: int
    responsesWithout: int
    date: datetime

    class Config:
        orm_mode = True

class ApplicationResponse(BaseModel):
    applicantId: int
    name: str
    status: ApplicationStatusEnum
    soft: Optional[float] = None
    tech: Optional[float] = None
    salary: Optional[float] = None
    contacts: str
    sumGrade: Optional[float] = None

    class Config:
        orm_mode = True

class ApplicantDetailResponse(BaseModel):
    name: str
    surname: str
    patronymic: str
    status: ApplicationStatusEnum
    soft: Optional[float] = None
    tech: Optional[float] = None
    salary: Optional[float] = None
    contacts: str
    sumGrade: Optional[float] = None
    cv: str

    class Config:
        orm_mode = True

class EventRequest(BaseModel):
    reqType: str  # "reject" | "next"

class EventResponse(BaseModel):
    status: ApplicationStatusEnum

class ApplicantSummaryResponse(BaseModel):
    summary: str

    class Config:
        orm_mode = True