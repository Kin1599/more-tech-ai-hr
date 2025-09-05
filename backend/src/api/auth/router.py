import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .schemas import UserCreate, Token, UserLogin
from .service import authenticate_user, create_user
from ...core.security import create_access_token
from ...core.database import get_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_session)):
    user = authenticate_user(db, user_data.email, user_data.password)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email, "id": user.id, "role": user.role})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role
    }

@router.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_session)):
    new_user = create_user(db, user)
    
    access_token = create_access_token(data={"sub": new_user.email, "id": new_user.id, "role": new_user.role})

    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": new_user.id,
        "role": new_user.role
    }

@router.post("/token", response_model=Token)
def login_for_swagger(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email, "id": user.id, "role": user.role})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role
    }