from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from enum import Enum


class CreateRoomRequest(BaseModel):
    jobApplicationId: int


class CreateRoomResponse(BaseModel):
    roomId: str
    playgroundLink: str | None = None
    model_config = ConfigDict(from_attributes=True)


class StartAgentRequest(BaseModel):
    jobApplicationId: int
    roomId: str


class InterviewVerdictEnum(str, Enum):
    strong_hire = "strong_hire"
    hire = "hire"
    borderline = "borderline"
    no_hire = "no_hire"


class SubmitResultsRequest(BaseModel):
    jobApplicationId: int
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: str
    verdict: InterviewVerdictEnum


class SubmitResultsResponse(BaseModel):
    interviewId: int
    model_config = ConfigDict(from_attributes=True)