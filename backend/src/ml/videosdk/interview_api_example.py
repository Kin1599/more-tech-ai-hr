#!/usr/bin/env python3
"""
Пример API endpoint для создания интервью с database-first подходом.
Демонстрирует правильную интеграцию VideoSDK Interview Agent с основным приложением.
"""

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

# Импорты основного приложения (адаптируйте под вашу структуру)
try:
    from ...core.database import get_session
    from ...models.models import Vacancy, ApplicantProfile, JobApplication
    from ...api.hr.service import get_current_hr_user
    from ...api.applicant.service import get_current_applicant_user
except ImportError:
    # Fallback для тестирования
    def get_session():
        pass
    
    def get_current_hr_user():
        pass
    
    def get_current_applicant_user():
        pass

logger = logging.getLogger(__name__)

# Pydantic модели для API
class InterviewCreateRequest(BaseModel):
    applicant_id: int
    vacancy_id: int
    max_questions: Optional[int] = 12
    interview_type: Optional[str] = "technical"

class InterviewCreateResponse(BaseModel):
    room_id: str
    interview_url: str
    applicant_name: str
    vacancy_name: str
    message: str

class InterviewStatusResponse(BaseModel):
    room_id: str
    status: str
    applicant_id: int
    vacancy_id: int
    created_at: str
    results: Optional[dict] = None

# Создаем FastAPI приложение (или добавляем в существующий)
app = FastAPI(title="Interview API", version="1.0.0")

@app.post("/api/interview/create", response_model=InterviewCreateResponse)
async def create_interview(
    request: InterviewCreateRequest,
    db: Session = Depends(get_session),
    current_hr = Depends(get_current_hr_user)
):
    """
    Создает новое видеособеседование для кандидата на вакансию.
    
    Требует:
    - HR должен быть авторизован
    - Кандидат должен существовать
    - Вакансия должна существовать  
    - Должна быть заявка кандидата на вакансию
    """
    try:
        # Валидация данных
        validation_result = await validate_interview_request(
            request.applicant_id, 
            request.vacancy_id, 
            db
        )
        
        applicant = validation_result["applicant"]
        vacancy = validation_result["vacancy"]
        application = validation_result["application"]
        
        # Проверяем права HR (может проводить интервью только для своих вакансий)
        if vacancy.hr_id != current_hr.id:
            raise HTTPException(
                status_code=403, 
                detail="Вы можете проводить интервью только для своих вакансий"
            )
        
        # Проверяем статус заявки
        if application.status not in ["screening_passed", "interview_scheduled"]:
            raise HTTPException(
                status_code=400,
                detail=f"Интервью невозможно для заявки со статусом {application.status}"
            )
        
        # Создаем VideoSDK комнату с метаданными
        room_data = await create_videosdk_room({
            'applicant_id': request.applicant_id,
            'vacancy_id': request.vacancy_id,
            'max_questions': request.max_questions,
            'interview_type': request.interview_type,
            'hr_id': current_hr.id,
            'created_by': 'api'
        })
        
        # Обновляем статус заявки
        application.status = "interview_in_progress"
        db.add(application)
        db.commit()
        
        logger.info(f"Создано интервью для кандидата {applicant.id} на вакансию {vacancy.id}")
        
        return InterviewCreateResponse(
            room_id=room_data["room_id"],
            interview_url=room_data["join_url"],
            applicant_name=f"{applicant.name} {applicant.surname}",
            vacancy_name=vacancy.name,
            message=f"Интервью успешно создано для {applicant.name} {applicant.surname} на позицию {vacancy.name}"
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка создания интервью: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@app.get("/api/interview/{room_id}/status", response_model=InterviewStatusResponse)
async def get_interview_status(
    room_id: str,
    db: Session = Depends(get_session),
    current_hr = Depends(get_current_hr_user)
):
    """
    Получает статус интервью по ID комнаты.
    """
    try:
        # Получаем информацию о комнате из VideoSDK
        room_info = await get_videosdk_room_info(room_id)
        
        if not room_info:
            raise HTTPException(status_code=404, detail="Интервью не найдено")
        
        metadata = room_info.get("metadata", {})
        applicant_id = metadata.get("applicant_id")
        vacancy_id = metadata.get("vacancy_id")
        
        # Проверяем права доступа
        vacancy = db.query(Vacancy).get(vacancy_id)
        if not vacancy or vacancy.hr_id != current_hr.id:
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Получаем результаты интервью, если есть
        results = await get_interview_results(room_id)
        
        return InterviewStatusResponse(
            room_id=room_id,
            status=room_info["status"],
            applicant_id=applicant_id,
            vacancy_id=vacancy_id,
            created_at=room_info["created_at"],
            results=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения статуса интервью: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@app.post("/api/interview/{room_id}/finish")
async def finish_interview(
    room_id: str,
    db: Session = Depends(get_session),
    current_hr = Depends(get_current_hr_user)
):
    """
    Завершает интервью и обновляет статус заявки.
    """
    try:
        # Получаем информацию о комнате
        room_info = await get_videosdk_room_info(room_id)
        if not room_info:
            raise HTTPException(status_code=404, detail="Интервью не найдено")
        
        metadata = room_info.get("metadata", {})
        applicant_id = metadata.get("applicant_id")
        vacancy_id = metadata.get("vacancy_id")
        
        # Проверяем права
        vacancy = db.query(Vacancy).get(vacancy_id)
        if not vacancy or vacancy.hr_id != current_hr.id:
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Завершаем VideoSDK сессию
        await close_videosdk_room(room_id)
        
        # Получаем результаты интервью
        results = await get_interview_results(room_id)
        
        # Обновляем статус заявки на основе результатов
        application = db.query(JobApplication).filter_by(
            applicant_id=applicant_id,
            vacancy_id=vacancy_id
        ).first()
        
        if application and results:
            verdict = results.get("verdict", "unknown")
            if verdict == "hire":
                application.status = "interview_passed"
            elif verdict == "reject":
                application.status = "interview_failed"
            else:
                application.status = "interview_completed"
            
            db.add(application)
            db.commit()
        
        logger.info(f"Завершено интервью {room_id} с результатом {verdict}")
        
        return {
            "message": "Интервью успешно завершено",
            "results": results,
            "new_status": application.status if application else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка завершения интервью: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Вспомогательные функции

class ValidationError(Exception):
    pass

async def validate_interview_request(applicant_id: int, vacancy_id: int, db: Session) -> dict:
    """
    Валидирует возможность создания интервью.
    
    Returns:
        dict: Содержит applicant, vacancy, application
        
    Raises:
        ValidationError: Если валидация не прошла
    """
    # Проверяем кандидата
    applicant = db.query(ApplicantProfile).get(applicant_id)
    if not applicant:
        raise ValidationError(f"Кандидат с ID {applicant_id} не найден")
    
    if not applicant.cv:
        raise ValidationError(f"У кандидата {applicant_id} отсутствует резюме")
    
    # Проверяем вакансию
    vacancy = db.query(Vacancy).get(vacancy_id)
    if not vacancy:
        raise ValidationError(f"Вакансия с ID {vacancy_id} не найдена")
    
    if vacancy.status != "active":
        raise ValidationError(f"Вакансия {vacancy_id} не активна")
    
    # Проверяем заявку
    application = db.query(JobApplication).filter_by(
        applicant_id=applicant_id,
        vacancy_id=vacancy_id
    ).first()
    
    if not application:
        raise ValidationError(f"Заявка не найдена для кандидата {applicant_id} на вакансию {vacancy_id}")
    
    return {
        "applicant": applicant,
        "vacancy": vacancy,
        "application": application
    }

async def create_videosdk_room(metadata: dict) -> dict:
    """
    Создает комнату VideoSDK с указанными метаданными.
    
    В реальном приложении здесь должна быть интеграция с VideoSDK API.
    """
    # Пример интеграции с VideoSDK
    import uuid
    
    room_id = str(uuid.uuid4())
    join_url = f"https://your-app.com/interview/{room_id}"
    
    # Здесь должен быть реальный вызов VideoSDK API
    # room = await videosdk.create_room(
    #     options=RoomOptions(metadata=metadata)
    # )
    
    logger.info(f"Создана VideoSDK комната {room_id} с метаданными: {metadata}")
    
    return {
        "room_id": room_id,
        "join_url": join_url,
        "metadata": metadata
    }

async def get_videosdk_room_info(room_id: str) -> dict:
    """
    Получает информацию о комнате VideoSDK.
    """
    # Здесь должен быть реальный вызов VideoSDK API
    # return await videosdk.get_room_info(room_id)
    
    return {
        "room_id": room_id,
        "status": "active",
        "created_at": "2025-01-01T12:00:00Z",
        "metadata": {
            "applicant_id": 123,
            "vacancy_id": 456
        }
    }

async def get_interview_results(room_id: str) -> Optional[dict]:
    """
    Получает результаты интервью из базы данных или VideoSDK.
    """
    # Здесь должна быть логика получения результатов интервью
    # Результаты могли быть сохранены InterviewAgent автоматически
    
    return {
        "verdict": "hire",
        "overall_score": 85,
        "competency_scores": {
            "Python": 90,
            "Django": 80,
            "Databases": 85
        },
        "feedback": "Отличные знания Python и Django, рекомендуем к найму"
    }

async def close_videosdk_room(room_id: str):
    """
    Закрывает комнату VideoSDK.
    """
    # Здесь должен быть реальный вызов VideoSDK API
    # await videosdk.close_room(room_id)
    
    logger.info(f"Закрыта VideoSDK комната {room_id}")

# Middleware для CORS (если нужно)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
