from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ...core.security import get_password_hash, verify_password
from ...models.models import User, HRProfile, ApplicantProfile
from .schemas import RoleEnum, UserCreate

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate) -> User:
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_password = get_password_hash(user.password)

    new_user = User(
        email=user.email,
        password_hash=hashed_password,
        role=user.role,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if user.role == RoleEnum.hr:
        db.add(HRProfile(user_id=new_user.id))
    elif user.role == RoleEnum.applicant:
        db.add(ApplicantProfile(user_id=new_user.id))
    
    db.commit()
    return new_user

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return None
        
    return user

def get_user_info_from_token(db: Session, email: str) -> User:
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user