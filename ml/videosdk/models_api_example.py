#!/usr/bin/env python3
"""
Пример API endpoints для управления настройками AI моделей интервью.
Демонстрирует CRUD операции для конфигурации моделей.
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

# Импорты основного приложения
try:
    from ...core.database import get_session
    from ...models.ai_models import (
        AIModelConfiguration, 
        InterviewModelConfiguration,
        ModelUsageLog,
        ModelTypeEnum, 
        ModelProviderEnum
    )
    from ...api.hr.service import get_current_hr_user
    from ...api.admin.service import get_current_admin_user  # Предполагаемый сервис админа
except ImportError:
    # Fallback для тестирования
    def get_session():
        pass
    
    def get_current_hr_user():
        pass
    
    def get_current_admin_user():
        pass

from model_service import ModelConfigurationService
from model_factory import ModelFactory, test_model_availability

logger = logging.getLogger(__name__)

# Pydantic модели для API
class AIModelConfigurationCreate(BaseModel):
    name: str = Field(..., max_length=100, description="Название модели")
    description: Optional[str] = Field(None, description="Описание модели")
    model_type: str = Field(..., description="Тип модели: llm, stt, tts")
    provider: str = Field(..., description="Провайдер модели")
    model_name: str = Field(..., max_length=200, description="Название модели у провайдера")
    endpoint_url: Optional[str] = Field(None, max_length=500, description="URL endpoint для локальных/кастомных моделей")
    api_key_name: Optional[str] = Field(None, max_length=100, description="Название переменной окружения с API ключом")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Температура генерации")
    max_tokens: Optional[int] = Field(None, ge=1, description="Максимальное количество токенов")
    timeout: Optional[int] = Field(30, ge=1, description="Таймаут в секундах")
    extra_params: Optional[str] = Field(None, description="Дополнительные параметры в формате JSON")
    is_default: bool = Field(False, description="Модель по умолчанию для типа")

class AIModelConfigurationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    endpoint_url: Optional[str] = Field(None, max_length=500)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)
    timeout: Optional[int] = Field(None, ge=1)
    extra_params: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class AIModelConfigurationResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    model_type: str
    provider: str
    model_name: str
    endpoint_url: Optional[str]
    api_key_name: Optional[str]
    temperature: Optional[float]
    max_tokens: Optional[int]
    timeout: Optional[int]
    is_active: bool
    is_default: bool
    created_at: str
    updated_at: str

class InterviewModelConfigurationCreate(BaseModel):
    vacancy_id: int = Field(..., description="ID вакансии")
    llm_model_id: Optional[int] = Field(None, description="ID LLM модели")
    stt_model_id: Optional[int] = Field(None, description="ID STT модели")
    tts_model_id: Optional[int] = Field(None, description="ID TTS модели")
    max_questions: int = Field(12, ge=1, le=50, description="Максимальное количество вопросов")
    interview_timeout: int = Field(3600, ge=300, description="Таймаут интервью в секундах")
    use_voice_activity_detection: bool = Field(True, description="Использовать детекцию голосовой активности")
    use_turn_detection: bool = Field(True, description="Использовать детекцию смены говорящего")
    silence_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Порог тишины")
    name: Optional[str] = Field(None, max_length=200, description="Название конфигурации")
    description: Optional[str] = Field(None, description="Описание конфигурации")

class InterviewModelConfigurationResponse(BaseModel):
    id: int
    vacancy_id: int
    llm_model: Optional[AIModelConfigurationResponse]
    stt_model: Optional[AIModelConfigurationResponse]
    tts_model: Optional[AIModelConfigurationResponse]
    max_questions: int
    interview_timeout: int
    use_voice_activity_detection: bool
    use_turn_detection: bool
    silence_threshold: float
    name: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str

class ModelUsageStatsResponse(BaseModel):
    model_name: str
    provider: str
    usage_count: int
    total_tokens: Optional[int]
    total_duration: Optional[float]
    total_cost: Optional[float]
    avg_tokens_per_use: Optional[float]
    avg_duration_per_use: Optional[float]

# Создаем FastAPI приложение
app = FastAPI(
    title="AI Models Configuration API",
    description="API для управления настройками AI моделей интервью",
    version="1.0.0"
)

# === CRUD для AI Model Configurations ===

@app.get("/api/admin/ai-models", response_model=List[AIModelConfigurationResponse])
async def get_ai_models(
    model_type: Optional[str] = Query(None, description="Фильтр по типу модели"),
    provider: Optional[str] = Query(None, description="Фильтр по провайдеру"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    db: Session = Depends(get_session),
    current_admin = Depends(get_current_admin_user)
):
    """
    Получить список всех AI моделей.
    Доступно только администраторам.
    """
    try:
        service = ModelConfigurationService(db)
        models = service.get_available_models(model_type)
        
        # Применяем дополнительные фильтры
        if provider:
            models = [m for m in models if m.get('provider') == provider]
        if is_active is not None:
            # Для этого фильтра нужно расширить get_available_models
            pass
        
        return models
        
    except Exception as e:
        logger.error(f"Error fetching AI models: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@app.post("/api/admin/ai-models", response_model=AIModelConfigurationResponse)
async def create_ai_model(
    config: AIModelConfigurationCreate,
    db: Session = Depends(get_session),
    current_admin = Depends(get_current_admin_user)
):
    """
    Создать новую AI модель.
    Доступно только администраторам.
    """
    try:
        # Валидация конфигурации
        config_dict = config.dict()
        if not ModelFactory.validate_model_config(config_dict):
            raise HTTPException(status_code=400, detail="Невалидная конфигурация модели")
        
        # Тестирование доступности модели (опционально)
        if not test_model_availability(config_dict):
            logger.warning(f"Model {config.name} may not be available")
        
        # Создание модели
        model = AIModelConfiguration(
            name=config.name,
            description=config.description,
            model_type=ModelTypeEnum(config.model_type),
            provider=ModelProviderEnum(config.provider),
            model_name=config.model_name,
            endpoint_url=config.endpoint_url,
            api_key_name=config.api_key_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout,
            extra_params=config.extra_params,
            is_default=config.is_default
        )
        
        db.add(model)
        db.commit()
        db.refresh(model)
        
        logger.info(f"Created AI model: {model.name} (ID: {model.id})")
        
        return AIModelConfigurationResponse(
            id=model.id,
            name=model.name,
            description=model.description,
            model_type=model.model_type.value,
            provider=model.provider.value,
            model_name=model.model_name,
            endpoint_url=model.endpoint_url,
            api_key_name=model.api_key_name,
            temperature=model.temperature,
            max_tokens=model.max_tokens,
            timeout=model.timeout,
            is_active=model.is_active,
            is_default=model.is_default,
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating AI model: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@app.put("/api/admin/ai-models/{model_id}", response_model=AIModelConfigurationResponse)
async def update_ai_model(
    model_id: int,
    config: AIModelConfigurationUpdate,
    db: Session = Depends(get_session),
    current_admin = Depends(get_current_admin_user)
):
    """
    Обновить AI модель.
    Доступно только администраторам.
    """
    try:
        model = db.query(AIModelConfiguration).get(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Модель не найдена")
        
        # Обновляем только переданные поля
        update_data = config.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(model, field, value)
        
        db.commit()
        db.refresh(model)
        
        logger.info(f"Updated AI model: {model.name} (ID: {model.id})")
        
        return AIModelConfigurationResponse(
            id=model.id,
            name=model.name,
            description=model.description,
            model_type=model.model_type.value,
            provider=model.provider.value,
            model_name=model.model_name,
            endpoint_url=model.endpoint_url,
            api_key_name=model.api_key_name,
            temperature=model.temperature,
            max_tokens=model.max_tokens,
            timeout=model.timeout,
            is_active=model.is_active,
            is_default=model.is_default,
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error updating AI model: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@app.delete("/api/admin/ai-models/{model_id}")
async def delete_ai_model(
    model_id: int,
    db: Session = Depends(get_session),
    current_admin = Depends(get_current_admin_user)
):
    """
    Удалить AI модель.
    Доступно только администраторам.
    """
    try:
        model = db.query(AIModelConfiguration).get(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Модель не найдена")
        
        # Проверяем, используется ли модель в интервью
        usage_count = db.query(InterviewModelConfiguration).filter(
            (InterviewModelConfiguration.llm_model_id == model_id) |
            (InterviewModelConfiguration.stt_model_id == model_id) |
            (InterviewModelConfiguration.tts_model_id == model_id)
        ).count()
        
        if usage_count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Модель используется в {usage_count} конфигурациях интервью"
            )
        
        db.delete(model)
        db.commit()
        
        logger.info(f"Deleted AI model: {model.name} (ID: {model.id})")
        
        return {"message": f"Модель {model.name} успешно удалена"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting AI model: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# === CRUD для Interview Model Configurations ===

@app.get("/api/hr/vacancies/{vacancy_id}/models", response_model=Optional[InterviewModelConfigurationResponse])
async def get_vacancy_models_config(
    vacancy_id: int,
    db: Session = Depends(get_session),
    current_hr = Depends(get_current_hr_user)
):
    """
    Получить конфигурацию моделей для вакансии.
    """
    try:
        service = ModelConfigurationService(db)
        config = service.get_interview_models_config(vacancy_id)
        
        if not config:
            return None
        
        # Преобразуем в response модель
        return InterviewModelConfigurationResponse(**config)
        
    except Exception as e:
        logger.error(f"Error fetching models config for vacancy {vacancy_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@app.post("/api/hr/vacancies/{vacancy_id}/models", response_model=InterviewModelConfigurationResponse)
async def create_vacancy_models_config(
    vacancy_id: int,
    config: InterviewModelConfigurationCreate,
    db: Session = Depends(get_session),
    current_hr = Depends(get_current_hr_user)
):
    """
    Создать конфигурацию моделей для вакансии.
    """
    try:
        # Проверяем права доступа к вакансии
        from ...models.models import Vacancy
        vacancy = db.query(Vacancy).get(vacancy_id)
        if not vacancy:
            raise HTTPException(status_code=404, detail="Вакансия не найдена")
        
        if vacancy.hr_id != current_hr.id:
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Проверяем, что модели существуют
        if config.llm_model_id:
            llm_model = db.query(AIModelConfiguration).get(config.llm_model_id)
            if not llm_model or llm_model.model_type != ModelTypeEnum.LLM:
                raise HTTPException(status_code=400, detail="Неверная LLM модель")
        
        if config.stt_model_id:
            stt_model = db.query(AIModelConfiguration).get(config.stt_model_id)
            if not stt_model or stt_model.model_type != ModelTypeEnum.STT:
                raise HTTPException(status_code=400, detail="Неверная STT модель")
        
        if config.tts_model_id:
            tts_model = db.query(AIModelConfiguration).get(config.tts_model_id)
            if not tts_model or tts_model.model_type != ModelTypeEnum.TTS:
                raise HTTPException(status_code=400, detail="Неверная TTS модель")
        
        # Создаем конфигурацию
        service = ModelConfigurationService(db)
        config_id = service.create_interview_model_config(
            vacancy_id=vacancy_id,
            **config.dict()
        )
        
        if not config_id:
            raise HTTPException(status_code=500, detail="Не удалось создать конфигурацию")
        
        # Возвращаем созданную конфигурацию
        created_config = service.get_interview_models_config(vacancy_id)
        return InterviewModelConfigurationResponse(**created_config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating models config for vacancy {vacancy_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# === Аналитика и мониторинг ===

@app.get("/api/admin/models/usage-stats", response_model=List[ModelUsageStatsResponse])
async def get_models_usage_stats(
    days: int = Query(30, ge=1, le=365, description="Количество дней для статистики"),
    db: Session = Depends(get_session),
    current_admin = Depends(get_current_admin_user)
):
    """
    Получить статистику использования моделей.
    """
    try:
        # SQL запрос для получения статистики
        query = """
        SELECT 
            amc.name as model_name,
            amc.provider,
            COUNT(*) as usage_count,
            SUM(mul.tokens_used) as total_tokens,
            SUM(mul.duration_seconds) as total_duration,
            SUM(mul.cost_usd) as total_cost,
            AVG(mul.tokens_used) as avg_tokens_per_use,
            AVG(mul.duration_seconds) as avg_duration_per_use
        FROM model_usage_logs mul
        JOIN ai_model_configurations amc ON mul.ai_model_id = amc.id
        WHERE mul.started_at >= NOW() - INTERVAL %s DAY
        GROUP BY mul.ai_model_id, amc.name, amc.provider
        ORDER BY usage_count DESC
        """
        
        result = db.execute(query, (days,))
        stats = []
        
        for row in result:
            stats.append(ModelUsageStatsResponse(
                model_name=row.model_name,
                provider=row.provider,
                usage_count=row.usage_count,
                total_tokens=row.total_tokens,
                total_duration=row.total_duration,
                total_cost=row.total_cost,
                avg_tokens_per_use=row.avg_tokens_per_use,
                avg_duration_per_use=row.avg_duration_per_use
            ))
        
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching usage stats: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@app.post("/api/admin/models/test/{model_id}")
async def test_model(
    model_id: int,
    db: Session = Depends(get_session),
    current_admin = Depends(get_current_admin_user)
):
    """
    Протестировать доступность модели.
    """
    try:
        model = db.query(AIModelConfiguration).get(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Модель не найдена")
        
        # Конвертируем модель в словарь для тестирования
        config = {
            "name": model.name,
            "model_type": model.model_type.value,
            "provider": model.provider.value,
            "model_name": model.model_name,
            "endpoint_url": model.endpoint_url,
            "api_key_name": model.api_key_name,
            "temperature": model.temperature,
            "max_tokens": model.max_tokens,
            "timeout": model.timeout
        }
        
        is_available = test_model_availability(config)
        
        return {
            "model_name": model.name,
            "is_available": is_available,
            "message": "Модель доступна" if is_available else "Модель недоступна"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing model {model_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Middleware для CORS
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
    uvicorn.run(app, host="0.0.0.0", port=8002)
