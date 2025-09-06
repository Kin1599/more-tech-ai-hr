import os
import uuid
import aiofiles
from pathlib import Path
import aiofiles
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ...models.models import User, HRProfile, ApplicantProfile
from .schemas import HrUpdate, ApplicantUpdate, Hr, Applicant

ALLOWED_EXTS = {".pdf", ".docx", ".doc", ".txt"}
MAX_FILE_MB = 10
CHUNK_SIZE = 1024 * 1024

async def get_user_profile(current_user: User, db: Session) -> Hr | Applicant:
    if current_user.role == "hr":
        profile = db.query(HRProfile).filter(HRProfile.user_id == current_user.id).first()
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HR profile not found")
        return Hr.model_validate(profile)
    else:
        profile = db.query(ApplicantProfile).filter(ApplicantProfile.user_id == current_user.id).first()
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Applicant profile not found")
        return Applicant.model_validate(profile)
    
async def update_user_profile(current_user: User, update_data: HrUpdate | ApplicantUpdate, db: Session) -> Hr | Applicant:
    if current_user.role == "hr":
        profile = db.query(HRProfile).filter(HRProfile.user_id == current_user.id).first()
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HR profile not found")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(profile, key, value)
        
        db.commit()
        db.refresh(profile)
        return Hr.model_validate(profile)
    else:
        profile = db.query(ApplicantProfile).filter(ApplicantProfile.user_id == current_user.id).first()
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Applicant profile not found")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(profile, key, value)
        
        db.commit()
        db.refresh(profile)
        return Applicant.model_validate(profile)

async def save_resume_for_user(db: Session, user_id: int, file: UploadFile, resumes_dir: Path) -> Applicant:
    profile = db.query(ApplicantProfile).filter(ApplicantProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Applicant profile not found")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {ext}"
        )

    resumes_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{user_id}_{uuid.uuid4().hex}{ext}"
    dest_path = resumes_dir / filename

    total = 0
    try:
        async with aiofiles.open(dest_path, "wb") as out:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_FILE_MB * 1024 * 1024:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large (> {MAX_FILE_MB} MB)"
                    )
                await out.write(chunk)
    finally:
        await file.close()

    old = profile.cv
    profile.cv = str(dest_path)
    db.commit()
    db.refresh(profile)

    if old and os.path.exists(old) and old != str(dest_path):
        try:
            os.remove(old)
        except OSError:
            pass

    return Applicant.model_validate(profile, from_attributes=True)