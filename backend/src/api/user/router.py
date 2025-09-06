import os
from pathlib import Path
from fastapi import APIRouter, Depends, File, UploadFile, status, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from .schemas import ApplicantUpdate, HrUpdate, Hr, Applicant
from .service import get_user_profile, update_user_profile, save_resume_for_user

from ...models.models import User, ApplicantProfile
from ...core.database import get_session
from ...core.security import get_current_user

router = APIRouter(tags=["user"])

RESUMES_DIR  = Path(os.getenv("RESUMES_DIR", "uploads")).resolve()
RESUMES_DIR.mkdir(parents=True, exist_ok=True)

MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".txt": "text/plain",
}

@router.get('/me', response_model=Hr | Applicant)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    return await get_user_profile(current_user, db)

@router.put('/me', response_model=Hr | Applicant)
async def update_current_user_profile(
    update_data: HrUpdate | ApplicantUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):  
    if current_user.role == "hr" and not isinstance(update_data, HrUpdate):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Use schema HrUpdate"
        )
    
    if current_user.role == "applicant" and not isinstance(update_data, ApplicantUpdate):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Use schema ApplicantUpdate"
        )
    
    return await update_user_profile(current_user, update_data, db)

@router.post("/me/resume", response_model=Applicant, status_code=status.HTTP_201_CREATED)
async def upload_my_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    if current_user.role != "applicant":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only applicants can upload their resume")
    return await save_resume_for_user(db=db, user_id=current_user.id, file=file, resumes_dir=RESUMES_DIR)


@router.get('/resume/{user_id}')
async def get_resume(
    user_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    if current_user.role != "hr" and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    
    applicant_profile = db.query(ApplicantProfile).filter(ApplicantProfile.user_id == user_id).first()
    if not applicant_profile or not applicant_profile.cv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    if not os.path.exists(applicant_profile.cv):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on server")

    _, file_extension = os.path.splitext(applicant_profile.cv)
    media_type = MEDIA_TYPES.get(file_extension.lower(), "application/octet-stream")

    original_filename = os.path.basename(applicant_profile.cv)

    return FileResponse(
        applicant_profile.cv,
        media_type=media_type,
        filename=original_filename
    )