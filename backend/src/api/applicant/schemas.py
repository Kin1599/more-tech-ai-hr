from pydantic import BaseModel, ConfigDict
from typing import Optional
from enum import Enum

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
    vacancyId: int
    name: str
    region: Optional[str] = None
    busyType: BusyType
    hr: HRBrief

    model_config = ConfigDict(from_attributes=True)

class JobApplicationDetail(BaseModel):
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