from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)

class ApplicationStatusResponse(BaseModel):
    status: MeetingStatusEnum
    vacancyID: int
    name: str
    tribe: str
    otherInfo: str

    model_config = ConfigDict(from_attributes=True)