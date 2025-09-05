from pydantic import BaseModel
from typing import Optional
from enum import Enum

class MeetingStatusEnum(str, Enum):
    cvReview = "cvReview"
    waitPickTime = "waitPickTime"
    waitMeeting = "waitMeeting"
    waitResult = "waitResult"
    reject = "reject"
    approve = "approve"

class MeetingResponse(BaseModel):
    vacancyData: dict
    status: Optional[MeetingStatusEnum] = None
    hrContact: Optional[str] = None
    meetLink: Optional[str] = None
    calendarLink: Optional[str] = None

    class Config:
        orm_mode = True

class ApplicationStatusResponse(BaseModel):
    status: MeetingStatusEnum
    vacancyID: int
    name: str
    tribe: str
    otherInfo: str

    class Config:
        orm_mode = True