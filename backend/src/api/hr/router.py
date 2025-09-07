from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from ...core.security import get_current_hr_user
from ...core.database import get_session
from ...models.models import User
from .schemas import ( 
    VacancyDetailResponse,
    VacancyResponse,
    VacancyStatusUpdateRequest,
    VacancyStatusUpdateResponse, 
)
from .service import (
    change_vacancy_status,
    get_vacancies, 
    create_vacancy,
    change_vacancy,
    get_vacancy_detail,
)

router = APIRouter(tags=["hr"])



@router.get('/vacancies', response_model=list[VacancyResponse], dependencies=[Depends(get_current_hr_user)])
def get_vacancies_endpoint(
    offset: int = Query(0, ge=0, description="Смещение (0, 20, 40, ...)"),
    limit: int = Query(20, ge=1, le=200, description="Размер страницы (1..200)"),
    db: Session = Depends(get_session),
):
    """Постраничный список вакансий"""
    return get_vacancies(db, offset, limit)



@router.post('/vacancies', response_model=VacancyResponse, status_code=status.HTTP_201_CREATED)
def create_vacancy_endpoint(
    file: UploadFile = File(..., description="DOCX file vacancy"),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_hr_user),
):
    """Создать вакансию из DOCX."""
    try:
        return create_vacancy(db=db, current_user=current_user, file=file)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



@router.put('/vacancies/{vacancy_id}', response_model=VacancyResponse, dependencies=[Depends(get_current_hr_user)])
def change_vacancy_endpoint(
    vacancy_id: int,
    file: UploadFile = File(..., description="DOCX update file vacancy"),
    db: Session = Depends(get_session),
):
    """Обновить вакансию из DOCX. Пустые значения не затирают уже заполненные поля."""
    try:
        return change_vacancy(db=db, vacancy_id=vacancy_id, file=file)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



@router.put("/vacancies/{vacancy_id}/status", response_model=VacancyStatusUpdateResponse, dependencies=[Depends(get_current_hr_user)])
def change_vacancy_status_endpoint(
    vacancy_id: int,
    body: VacancyStatusUpdateRequest,
    db: Session = Depends(get_session),
):
    """Сменить статус вакансии."""
    try:
        return change_vacancy_status(db=db, vacancy_id=vacancy_id, new_status=body.status)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to change vacancy status: {str(e)}")



@router.get('/vacancies/{vacancy_id}', response_model=VacancyDetailResponse, dependencies=[Depends(get_current_hr_user)])
def get_vacancy_detail_endpoint(
    vacancy_id: int, 
    db: Session = Depends(get_session)
):
    """Детальная вакансия + список откликов."""
    try:
        return get_vacancy_detail(db=db, vacancy_id=vacancy_id)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")