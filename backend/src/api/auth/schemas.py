from enum import Enum
from pydantic import BaseModel, EmailStr

class RoleEnum(str, Enum):
    hr = "hr"
    applicant = "applicant"

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: RoleEnum

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    role: RoleEnum
