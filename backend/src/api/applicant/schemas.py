from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
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

class BusyType(str, Enum):
    allTime = "allTime"
    projectTime = "projectTime"

class JobApplicationStatus(str, Enum):
    cvReview = "cvReview"
    interview = "interview"
    waitResult = "waitResult"
    rejected = "rejected"
    approved = "approved"    

class HRBrief(BaseModel):
    name: str
    contact: Optional[str] = None

class JobApplicationListItem(BaseModel):
    applicationId: int
    vacancyId: int
    name: str
    region: Optional[str] = None
    busyType: BusyType
    hr: HRBrief

    model_config = ConfigDict(from_attributes=True)

class JobApplicationDetail(BaseModel):
    applicationId: int
    name: str
    region: Optional[str] = None
    busyType: BusyType
    hr: HRBrief
    status: JobApplicationStatus
    interviewLink: Optional[str] = None
    interviewRecommendation: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class InterviewLinkResponse(BaseModel):
    interviewLink: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class VacancyResponse(BaseModel):
    vacancyId: int
    name: str
    status: VacancyStatusEnum
    department: str
    date: datetime    
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