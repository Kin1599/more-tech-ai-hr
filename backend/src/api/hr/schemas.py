from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class OfferTypeEnum(str, Enum):
    TK = "TK"
    GPH = "GPH"
    IP = "IP"

class BusyTypeEnum(str, Enum):
    allTime = "allTime"
    projectTime = "projectTime"

class VacancyStatusEnum(str, Enum):
    active = "active"
    closed = "closed"
    stopped = "stopped"

class VacancyStatusUpdateRequest(BaseModel):
    status: VacancyStatusEnum

class VacancyStatusUpdateResponse(BaseModel):
    status: VacancyStatusEnum

class ApplicantStatusEnum(str, Enum):
    rejected = "rejected"
    cvReview = "cvReview"
    interview = "interview"
    waitResult = "waitResult"
    approved = "approved"

class VacancyResponse(BaseModel):
    vacancyId: int
    name: str
    status: VacancyStatusEnum
    department: str
    date: datetime

    responses: int = 0
    
    region: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    offerType: Optional[OfferTypeEnum] = None
    busyType: Optional[BusyTypeEnum] = None
    graph: Optional[str] = None
    salaryMin: Optional[float] = None
    salaryMax: Optional[float] = None
    annualBonus: Optional[float] = None
    bonusType: Optional[str] = None
    description: Optional[str] = None
    prompt: Optional[str] = None
    exp: Optional[int] = None
    degree: Optional[bool] = None
    specialSoftware: Optional[str] = None
    computerSkills: Optional[str] = None
    foreignLanguages: Optional[str] = None
    languageLevel: Optional[str] = None
    businessTrips: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)

class VacancyDetailApplicant(BaseModel):
    applicantId: int
    name: str
    score: float
    status: ApplicantStatusEnum
    checked: Optional[bool] = False

class VacancyDetailResponse(VacancyResponse):
    detailResponses: List[VacancyDetailApplicant]