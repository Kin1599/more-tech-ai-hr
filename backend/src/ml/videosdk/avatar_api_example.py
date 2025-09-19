"""
Пример API для управления Avatar конфигурациями в интервью.

Демонстрирует CRUD операции для Simli Avatar и других Avatar провайдеров.
"""

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import logging

# Импорты из нашего проекта
from ...core.database import get_session
from ...models.ai_models import AIModelConfiguration, InterviewModelConfiguration, ModelTypeEnum, ModelProviderEnum
from .model_service import ModelConfigurationService

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Avatar Configuration API",
    description="API для управления Avatar конфигурациями интервью",
    version="1.0.0"
)

# Pydantic модели для API

class AvatarConfigRequest(BaseModel):
    """Запрос на создание Avatar конфигурации."""
    name: str = Field(..., description="Название конфигурации")
    description: Optional[str] = Field(None, description="Описание конфигурации")
    provider: str = Field(..., description="Провайдер Avatar (simli, custom_endpoint, etc.)")
    model_name: str = Field(..., description="Название модели")
    api_key_name: Optional[str] = Field(None, description="Название переменной окружения с API ключом")
    endpoint_url: Optional[str] = Field(None, description="URL endpoint для кастомных провайдеров")
    
    # Avatar-специфичные параметры
    face_id: Optional[str] = Field(None, description="ID лица для Avatar")
    max_session_length: Optional[int] = Field(1800, description="Максимальная длительность сессии (сек)")
    max_idle_time: Optional[int] = Field(300, description="Максимальное время бездействия (сек)")
    
    # Общие параметры
    timeout: Optional[int] = Field(30, description="Таймаут в секундах")
    extra_params: Optional[Dict[str, Any]] = Field(None, description="Дополнительные параметры")
    is_active: bool = Field(True, description="Активна ли конфигурация")
    is_default: bool = Field(False, description="Конфигурация по умолчанию")

class AvatarConfigResponse(BaseModel):
    """Ответ с конфигурацией Avatar."""
    id: int
    name: str
    description: Optional[str]
    provider: str
    model_name: str
    api_key_name: Optional[str]
    endpoint_url: Optional[str]
    face_id: Optional[str]
    max_session_length: Optional[int]
    max_idle_time: Optional[int]
    timeout: Optional[int]
    extra_params: Optional[Dict[str, Any]]
    is_active: bool
    is_default: bool
    created_at: str
    updated_at: str

class InterviewAvatarConfigRequest(BaseModel):
    """Запрос на настройку Avatar для интервью."""
    vacancy_id: int = Field(..., description="ID вакансии")
    avatar_model_id: Optional[int] = Field(None, description="ID Avatar модели")
    max_questions: int = Field(12, description="Максимальное количество вопросов")
    interview_timeout: int = Field(3600, description="Таймаут интервью в секундах")

# API Endpoints

@app.post("/avatar-configs/", response_model=AvatarConfigResponse)
async def create_avatar_config(
    config_request: AvatarConfigRequest,
    db: Session = Depends(get_session)
):
    """
    Создать новую конфигурацию Avatar.
    
    Поддерживает различные провайдеры:
    - simli: Simli Avatar с face_id
    - custom_endpoint: Кастомный Avatar API
    - custom_local: Локальный кастомный Avatar
    """
    try:
        service = ModelConfigurationService(db)
        
        # Проверяем валидность провайдера
        if config_request.provider not in [p.value for p in ModelProviderEnum]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported provider: {config_request.provider}"
            )
        
        # Создаем конфигурацию Avatar
        config_id = service.create_ai_model_configuration(
            name=config_request.name,
            description=config_request.description,
            model_type=ModelTypeEnum.AVATAR,
            provider=ModelProviderEnum(config_request.provider),
            model_name=config_request.model_name,
            api_key_name=config_request.api_key_name,
            endpoint_url=config_request.endpoint_url,
            face_id=config_request.face_id,
            max_session_length=config_request.max_session_length,
            max_idle_time=config_request.max_idle_time,
            timeout=config_request.timeout,
            extra_params=config_request.extra_params,
            is_active=config_request.is_active,
            is_default=config_request.is_default
        )
        
        if not config_id:
            raise HTTPException(status_code=500, detail="Failed to create Avatar configuration")
        
        # Получаем созданную конфигурацию
        config = db.query(AIModelConfiguration).get(config_id)
        
        return AvatarConfigResponse(
            id=config.id,
            name=config.name,
            description=config.description,
            provider=config.provider.value,
            model_name=config.model_name,
            api_key_name=config.api_key_name,
            endpoint_url=config.endpoint_url,
            face_id=config.face_id,
            max_session_length=config.max_session_length,
            max_idle_time=config.max_idle_time,
            timeout=config.timeout,
            extra_params=config.extra_params,
            is_active=config.is_active,
            is_default=config.is_default,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error creating Avatar configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/avatar-configs/", response_model=List[AvatarConfigResponse])
async def list_avatar_configs(
    active_only: bool = True,
    db: Session = Depends(get_session)
):
    """Получить список всех Avatar конфигураций."""
    try:
        query = db.query(AIModelConfiguration).filter_by(model_type=ModelTypeEnum.AVATAR)
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        configs = query.all()
        
        return [
            AvatarConfigResponse(
                id=config.id,
                name=config.name,
                description=config.description,
                provider=config.provider.value,
                model_name=config.model_name,
                api_key_name=config.api_key_name,
                endpoint_url=config.endpoint_url,
                face_id=config.face_id,
                max_session_length=config.max_session_length,
                max_idle_time=config.max_idle_time,
                timeout=config.timeout,
                extra_params=config.extra_params,
                is_active=config.is_active,
                is_default=config.is_default,
                created_at=config.created_at.isoformat(),
                updated_at=config.updated_at.isoformat()
            )
            for config in configs
        ]
        
    except Exception as e:
        logger.error(f"Error listing Avatar configurations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/avatar-configs/{config_id}", response_model=AvatarConfigResponse)
async def get_avatar_config(
    config_id: int,
    db: Session = Depends(get_session)
):
    """Получить конкретную Avatar конфигурацию."""
    try:
        config = (
            db.query(AIModelConfiguration)
            .filter_by(id=config_id, model_type=ModelTypeEnum.AVATAR)
            .first()
        )
        
        if not config:
            raise HTTPException(status_code=404, detail="Avatar configuration not found")
        
        return AvatarConfigResponse(
            id=config.id,
            name=config.name,
            description=config.description,
            provider=config.provider.value,
            model_name=config.model_name,
            api_key_name=config.api_key_name,
            endpoint_url=config.endpoint_url,
            face_id=config.face_id,
            max_session_length=config.max_session_length,
            max_idle_time=config.max_idle_time,
            timeout=config.timeout,
            extra_params=config.extra_params,
            is_active=config.is_active,
            is_default=config.is_default,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Avatar configuration {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/avatar-configs/{config_id}", response_model=AvatarConfigResponse)
async def update_avatar_config(
    config_id: int,
    config_request: AvatarConfigRequest,
    db: Session = Depends(get_session)
):
    """Обновить Avatar конфигурацию."""
    try:
        config = (
            db.query(AIModelConfiguration)
            .filter_by(id=config_id, model_type=ModelTypeEnum.AVATAR)
            .first()
        )
        
        if not config:
            raise HTTPException(status_code=404, detail="Avatar configuration not found")
        
        # Обновляем поля
        config.name = config_request.name
        config.description = config_request.description
        config.provider = ModelProviderEnum(config_request.provider)
        config.model_name = config_request.model_name
        config.api_key_name = config_request.api_key_name
        config.endpoint_url = config_request.endpoint_url
        config.face_id = config_request.face_id
        config.max_session_length = config_request.max_session_length
        config.max_idle_time = config_request.max_idle_time
        config.timeout = config_request.timeout
        config.extra_params = config_request.extra_params
        config.is_active = config_request.is_active
        config.is_default = config_request.is_default
        
        db.commit()
        db.refresh(config)
        
        return AvatarConfigResponse(
            id=config.id,
            name=config.name,
            description=config.description,
            provider=config.provider.value,
            model_name=config.model_name,
            api_key_name=config.api_key_name,
            endpoint_url=config.endpoint_url,
            face_id=config.face_id,
            max_session_length=config.max_session_length,
            max_idle_time=config.max_idle_time,
            timeout=config.timeout,
            extra_params=config.extra_params,
            is_active=config.is_active,
            is_default=config.is_default,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Avatar configuration {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/avatar-configs/{config_id}")
async def delete_avatar_config(
    config_id: int,
    db: Session = Depends(get_session)
):
    """Удалить Avatar конфигурацию."""
    try:
        config = (
            db.query(AIModelConfiguration)
            .filter_by(id=config_id, model_type=ModelTypeEnum.AVATAR)
            .first()
        )
        
        if not config:
            raise HTTPException(status_code=404, detail="Avatar configuration not found")
        
        db.delete(config)
        db.commit()
        
        return {"message": "Avatar configuration deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Avatar configuration {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/interviews/avatar-config/")
async def set_interview_avatar(
    config_request: InterviewAvatarConfigRequest,
    db: Session = Depends(get_session)
):
    """Настроить Avatar для интервью по вакансии."""
    try:
        service = ModelConfigurationService(db)
        
        # Создаем или обновляем конфигурацию интервью
        config_id = service.create_interview_model_config(
            vacancy_id=config_request.vacancy_id,
            avatar_model_id=config_request.avatar_model_id,
            max_questions=config_request.max_questions,
            interview_timeout=config_request.interview_timeout
        )
        
        if not config_id:
            raise HTTPException(status_code=500, detail="Failed to create interview Avatar configuration")
        
        return {
            "message": "Interview Avatar configuration created successfully",
            "config_id": config_id,
            "vacancy_id": config_request.vacancy_id,
            "avatar_model_id": config_request.avatar_model_id
        }
        
    except Exception as e:
        logger.error(f"Error setting interview Avatar: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/interviews/{vacancy_id}/avatar-config/")
async def get_interview_avatar_config(
    vacancy_id: int,
    db: Session = Depends(get_session)
):
    """Получить Avatar конфигурацию для интервью."""
    try:
        service = ModelConfigurationService(db)
        models_config = service.get_interview_models_config(vacancy_id)
        
        if not models_config:
            raise HTTPException(status_code=404, detail="Interview configuration not found")
        
        avatar_config = models_config.get("avatar_model")
        
        return {
            "vacancy_id": vacancy_id,
            "avatar_config": avatar_config,
            "has_avatar": avatar_config is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting interview Avatar configuration for vacancy {vacancy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Примеры использования

@app.get("/examples/simli-avatar-config/")
async def get_simli_example():
    """Пример конфигурации Simli Avatar."""
    return {
        "name": "Simli Professional Avatar",
        "description": "Профессиональный Avatar для интервью с использованием Simli",
        "provider": "simli",
        "model_name": "professional-interviewer",
        "api_key_name": "SIMLI_API_KEY",
        "face_id": "0c2b8b04-5274-41f1-a21c-d5c98322efa9",
        "max_session_length": 1800,  # 30 минут
        "max_idle_time": 300,  # 5 минут
        "timeout": 30,
        "extra_params": {
            "voice_quality": "high",
            "animation_style": "professional",
            "background": "office"
        },
        "is_active": True,
        "is_default": False
    }

@app.get("/examples/custom-avatar-config/")
async def get_custom_example():
    """Пример конфигурации кастомного Avatar."""
    return {
        "name": "Custom Corporate Avatar",
        "description": "Корпоративный Avatar с кастомным API",
        "provider": "custom_endpoint",
        "model_name": "corporate-avatar-v2",
        "api_key_name": "CORPORATE_AVATAR_API_KEY",
        "endpoint_url": "https://api.company.com/avatar/v2",
        "face_id": "corporate-face-001",
        "max_session_length": 2400,  # 40 минут
        "max_idle_time": 600,  # 10 минут
        "timeout": 45,
        "extra_params": {
            "company_branding": True,
            "language": "ru",
            "voice_accent": "moscow",
            "dress_code": "business_casual"
        },
        "is_active": True,
        "is_default": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
