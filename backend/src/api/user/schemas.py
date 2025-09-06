from enum import Enum
from typing import Optional
from pydantic import AliasPath, BaseModel, ConfigDict, EmailStr, Field

class RoleEnum(str, Enum):
    hr = "hr"
    applicant = "applicant"

class Hr(BaseModel):
    email: EmailStr = Field(validation_alias=AliasPath('user', 'email'))
    name: Optional[str] = None
    surname: Optional[str] = None
    patronymic: Optional[str] = None
    department: Optional[str] = None
    contacts: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class Applicant(BaseModel):
    email: EmailStr = Field(validation_alias=AliasPath('user', 'email'))
    name: Optional[str] = None
    surname: Optional[str] = None
    patronymic: Optional[str] = None
    contacts: Optional[str] = None
    cv: Optional[str] = None
    summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ProfileUpdateBase(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    patronymic: Optional[str] = None
    contacts: Optional[str] = None

class HrUpdate(ProfileUpdateBase):
    department: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ApplicantUpdate(ProfileUpdateBase):
    summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)