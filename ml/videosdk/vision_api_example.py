"""
Пример API для управления Vision конфигурациями и Screen Analysis.

Демонстрирует CRUD операции для Vision моделей и тестирование анализа экрана.
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import logging
import base64
import io
from PIL import Image

# Импорты из нашего проекта
from ...core.database import get_session
from ...models.ai_models import AIModelConfiguration, InterviewModelConfiguration, ModelTypeEnum, ModelProviderEnum
from .model_service import ModelConfigurationService
from .model_factory import ModelFactory
from .screen_analysis_tool import create_screen_analysis_tool, SCREEN_ANALYSIS_PROMPTS

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vision Models & Screen Analysis API",
    description="API для управления Vision моделями и анализа экрана",
    version="1.0.0"
)

# Pydantic модели для API

class VisionConfigRequest(BaseModel):
    """Запрос на создание Vision конфигурации."""
    name: str = Field(..., description="Название конфигурации")
    description: Optional[str] = Field(None, description="Описание конфигурации")
    provider: str = Field(..., description="Провайдер Vision (google_gemini, openai_vision, etc.)")
    model_name: str = Field(..., description="Название модели")
    api_key_name: str = Field(..., description="Название переменной окружения с API ключом")
    endpoint_url: Optional[str] = Field(None, description="URL endpoint для некоторых провайдеров")
    
    # Параметры генерации
    temperature: Optional[float] = Field(0.4, description="Temperature для генерации")
    max_tokens: Optional[int] = Field(2048, description="Максимальное количество токенов")
    timeout: Optional[int] = Field(30, description="Таймаут в секундах")
    
    # Дополнительные параметры
    extra_params: Optional[Dict[str, Any]] = Field(None, description="Дополнительные параметры")
    is_active: bool = Field(True, description="Активна ли конфигурация")
    is_default: bool = Field(False, description="Конфигурация по умолчанию")

class VisionConfigResponse(BaseModel):
    """Ответ с конфигурацией Vision модели."""
    id: int
    name: str
    description: Optional[str]
    provider: str
    model_name: str
    api_key_name: str
    endpoint_url: Optional[str]
    temperature: Optional[float]
    max_tokens: Optional[int]
    timeout: Optional[int]
    extra_params: Optional[Dict[str, Any]]
    is_active: bool
    is_default: bool
    created_at: str
    updated_at: str

class ScreenAnalysisRequest(BaseModel):
    """Запрос на анализ экрана."""
    prompt: str = Field(..., description="Запрос для анализа")
    focus_area: str = Field("general", description="Область фокуса")
    image_data: Optional[str] = Field(None, description="Base64 изображение (опционально)")

class ScreenAnalysisResponse(BaseModel):
    """Ответ анализа экрана."""
    success: bool
    analysis: str
    vision_model_used: Optional[str]
    focus_area: str
    processing_time_ms: Optional[float]

class InterviewVisionConfigRequest(BaseModel):
    """Запрос на настройку Vision для интервью."""
    vacancy_id: int = Field(..., description="ID вакансии")
    vision_model_id: Optional[int] = Field(None, description="ID Vision модели")

# API Endpoints для Vision конфигураций

@app.post("/vision-configs/", response_model=VisionConfigResponse)
async def create_vision_config(
    config_request: VisionConfigRequest,
    db: Session = Depends(get_session)
):
    """
    Создать новую конфигурацию Vision модели.
    
    Поддерживает различные провайдеры:
    - google_gemini: Google Gemini Vision (1.5-flash, 1.5-pro)
    - openai_vision: OpenAI GPT-4 Vision
    - anthropic_vision: Anthropic Claude Vision
    - azure_vision: Azure Computer Vision
    """
    try:
        service = ModelConfigurationService(db)
        
        # Проверяем валидность провайдера
        if config_request.provider not in [p.value for p in ModelProviderEnum]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported provider: {config_request.provider}"
            )
        
        # Создаем конфигурацию Vision модели
        config_id = service.create_ai_model_configuration(
            name=config_request.name,
            description=config_request.description,
            model_type=ModelTypeEnum.VISION,
            provider=ModelProviderEnum(config_request.provider),
            model_name=config_request.model_name,
            api_key_name=config_request.api_key_name,
            endpoint_url=config_request.endpoint_url,
            temperature=config_request.temperature,
            max_tokens=config_request.max_tokens,
            timeout=config_request.timeout,
            extra_params=config_request.extra_params,
            is_active=config_request.is_active,
            is_default=config_request.is_default
        )
        
        if not config_id:
            raise HTTPException(status_code=500, detail="Failed to create Vision configuration")
        
        # Получаем созданную конфигурацию
        config = db.query(AIModelConfiguration).get(config_id)
        
        return VisionConfigResponse(
            id=config.id,
            name=config.name,
            description=config.description,
            provider=config.provider.value,
            model_name=config.model_name,
            api_key_name=config.api_key_name,
            endpoint_url=config.endpoint_url,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout,
            extra_params=config.extra_params,
            is_active=config.is_active,
            is_default=config.is_default,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error creating Vision configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vision-configs/", response_model=List[VisionConfigResponse])
async def list_vision_configs(
    active_only: bool = True,
    db: Session = Depends(get_session)
):
    """Получить список всех Vision конфигураций."""
    try:
        query = db.query(AIModelConfiguration).filter_by(model_type=ModelTypeEnum.VISION)
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        configs = query.all()
        
        return [
            VisionConfigResponse(
                id=config.id,
                name=config.name,
                description=config.description,
                provider=config.provider.value,
                model_name=config.model_name,
                api_key_name=config.api_key_name,
                endpoint_url=config.endpoint_url,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
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
        logger.error(f"Error listing Vision configurations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vision-configs/{config_id}", response_model=VisionConfigResponse)
async def get_vision_config(
    config_id: int,
    db: Session = Depends(get_session)
):
    """Получить конкретную Vision конфигурацию."""
    try:
        config = (
            db.query(AIModelConfiguration)
            .filter_by(id=config_id, model_type=ModelTypeEnum.VISION)
            .first()
        )
        
        if not config:
            raise HTTPException(status_code=404, detail="Vision configuration not found")
        
        return VisionConfigResponse(
            id=config.id,
            name=config.name,
            description=config.description,
            provider=config.provider.value,
            model_name=config.model_name,
            api_key_name=config.api_key_name,
            endpoint_url=config.endpoint_url,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
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
        logger.error(f"Error getting Vision configuration {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API Endpoints для анализа экрана

@app.post("/screen-analysis/test", response_model=ScreenAnalysisResponse)
async def test_screen_analysis(
    request: ScreenAnalysisRequest,
    vision_config_id: Optional[int] = None,
    db: Session = Depends(get_session)
):
    """
    Тестировать анализ экрана с Vision моделью.
    
    Если vision_config_id не указан, используется модель по умолчанию.
    """
    import time
    start_time = time.time()
    
    try:
        # Получаем Vision конфигурацию
        if vision_config_id:
            vision_config = (
                db.query(AIModelConfiguration)
                .filter_by(id=vision_config_id, model_type=ModelTypeEnum.VISION)
                .first()
            )
            if not vision_config:
                raise HTTPException(status_code=404, detail="Vision configuration not found")
        else:
            # Используем конфигурацию по умолчанию
            vision_config = (
                db.query(AIModelConfiguration)
                .filter_by(model_type=ModelTypeEnum.VISION, is_default=True, is_active=True)
                .first()
            )
            if not vision_config:
                raise HTTPException(status_code=404, detail="No default Vision configuration found")
        
        # Создаем Vision модель
        config_dict = {
            "name": vision_config.name,
            "provider": vision_config.provider.value,
            "model_name": vision_config.model_name,
            "api_key_name": vision_config.api_key_name,
            "endpoint_url": vision_config.endpoint_url,
            "temperature": vision_config.temperature,
            "max_tokens": vision_config.max_tokens,
            "timeout": vision_config.timeout,
            "extra_params": vision_config.extra_params or {}
        }
        
        vision_model = ModelFactory.create_vision_model(config_dict)
        
        # Создаем Screen Analysis Tool
        screen_tool = create_screen_analysis_tool(vision_model)
        
        # Если передано изображение, анализируем его
        if request.image_data:
            try:
                # Декодируем base64 изображение
                image_bytes = base64.b64decode(request.image_data)
                image = Image.open(io.BytesIO(image_bytes))
                
                # Имитируем обновление кадра
                # В реальности это будет VideoFrame от VideoSDK
                screen_tool.set_screenshare_status(True)
                
                # Выполняем анализ
                analysis = await screen_tool._analyze_with_vision_model(
                    image, 
                    screen_tool._adapt_prompt_for_focus(request.prompt, request.focus_area)
                )
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")
        else:
            # Без изображения возвращаем информацию о том, что нужна демонстрация экрана
            analysis = "📺 Для анализа экрана необходимо включить демонстрацию экрана или передать изображение в параметре image_data"
        
        processing_time = (time.time() - start_time) * 1000
        
        return ScreenAnalysisResponse(
            success=True,
            analysis=analysis,
            vision_model_used=f"{vision_config.provider.value}:{vision_config.model_name}",
            focus_area=request.focus_area,
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in screen analysis: {e}")
        return ScreenAnalysisResponse(
            success=False,
            analysis=f"❌ Ошибка анализа: {str(e)}",
            vision_model_used=None,
            focus_area=request.focus_area,
            processing_time_ms=(time.time() - start_time) * 1000
        )

@app.post("/screen-analysis/upload", response_model=ScreenAnalysisResponse)
async def analyze_uploaded_image(
    file: UploadFile = File(...),
    prompt: str = "Проанализируй это изображение",
    focus_area: str = "general",
    vision_config_id: Optional[int] = None,
    db: Session = Depends(get_session)
):
    """Анализировать загруженное изображение."""
    try:
        # Проверяем тип файла
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Читаем и конвертируем изображение
        image_bytes = await file.read()
        image_b64 = base64.b64encode(image_bytes).decode()
        
        # Используем существующий endpoint для анализа
        request = ScreenAnalysisRequest(
            prompt=prompt,
            focus_area=focus_area,
            image_data=image_b64
        )
        
        return await test_screen_analysis(request, vision_config_id, db)
        
    except Exception as e:
        logger.error(f"Error analyzing uploaded image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/interviews/vision-config/")
async def set_interview_vision(
    config_request: InterviewVisionConfigRequest,
    db: Session = Depends(get_session)
):
    """Настроить Vision модель для интервью по вакансии."""
    try:
        service = ModelConfigurationService(db)
        
        # Создаем или обновляем конфигурацию интервью
        config_id = service.create_interview_model_config(
            vacancy_id=config_request.vacancy_id,
            vision_model_id=config_request.vision_model_id
        )
        
        if not config_id:
            raise HTTPException(status_code=500, detail="Failed to create interview Vision configuration")
        
        return {
            "message": "Interview Vision configuration created successfully",
            "config_id": config_id,
            "vacancy_id": config_request.vacancy_id,
            "vision_model_id": config_request.vision_model_id
        }
        
    except Exception as e:
        logger.error(f"Error setting interview Vision: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/interviews/{vacancy_id}/vision-config/")
async def get_interview_vision_config(
    vacancy_id: int,
    db: Session = Depends(get_session)
):
    """Получить Vision конфигурацию для интервью."""
    try:
        service = ModelConfigurationService(db)
        models_config = service.get_interview_models_config(vacancy_id)
        
        if not models_config:
            raise HTTPException(status_code=404, detail="Interview configuration not found")
        
        vision_config = models_config.get("vision_model")
        
        return {
            "vacancy_id": vacancy_id,
            "vision_config": vision_config,
            "has_vision": vision_config is not None,
            "screen_analysis_available": vision_config is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting interview Vision configuration for vacancy {vacancy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Примеры и утилиты

@app.get("/screen-analysis/prompts/")
async def get_analysis_prompts():
    """Получить предустановленные промпты для анализа экрана."""
    return {
        "prompts": SCREEN_ANALYSIS_PROMPTS,
        "focus_areas": [
            "code", "ui", "document", "error", "general"
        ],
        "usage_examples": {
            "code_review": "Используй для анализа кода и поиска ошибок",
            "ui_help": "Используй для помощи с интерфейсом",
            "error_diagnosis": "Используй для диагностики ошибок",
            "document_analysis": "Используй для анализа документов",
            "interview_help": "Используй в контексте интервью"
        }
    }

@app.get("/examples/vision-configs/")
async def get_vision_config_examples():
    """Примеры конфигураций Vision моделей."""
    return {
        "gemini_flash": {
            "name": "Gemini 1.5 Flash Vision",
            "description": "Быстрая мультимодальная модель для анализа экрана",
            "provider": "google_gemini",
            "model_name": "gemini-1.5-flash",
            "api_key_name": "GEMINI_API_KEY",
            "temperature": 0.4,
            "max_tokens": 2048,
            "timeout": 30,
            "extra_params": {
                "max_output_tokens": 2048,
                "safety_settings": "block_none"
            }
        },
        "gemini_pro": {
            "name": "Gemini 1.5 Pro Vision",
            "description": "Продвинутая модель для сложного анализа",
            "provider": "google_gemini", 
            "model_name": "gemini-1.5-pro",
            "api_key_name": "GEMINI_API_KEY",
            "temperature": 0.3,
            "max_tokens": 4096,
            "timeout": 45
        },
        "openai_vision": {
            "name": "OpenAI GPT-4 Vision",
            "description": "GPT-4 с возможностями анализа изображений",
            "provider": "openai_vision",
            "model_name": "gpt-4-vision-preview",
            "api_key_name": "OPENAI_API_KEY",
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 30,
            "extra_params": {
                "detail": "high"
            }
        }
    }

@app.get("/health/vision/")
async def check_vision_health(db: Session = Depends(get_session)):
    """Проверить доступность Vision конфигураций."""
    try:
        # Подсчитываем активные конфигурации
        active_configs = (
            db.query(AIModelConfiguration)
            .filter_by(model_type=ModelTypeEnum.VISION, is_active=True)
            .count()
        )
        
        default_config = (
            db.query(AIModelConfiguration)
            .filter_by(model_type=ModelTypeEnum.VISION, is_default=True, is_active=True)
            .first()
        )
        
        return {
            "status": "healthy",
            "active_vision_configs": active_configs,
            "has_default_config": default_config is not None,
            "default_config_name": default_config.name if default_config else None,
            "screen_analysis_available": active_configs > 0
        }
        
    except Exception as e:
        logger.error(f"Vision health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "screen_analysis_available": False
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
