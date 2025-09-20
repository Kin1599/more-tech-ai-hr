"""
API для работы с моделью T-pro-it-1.0 от T-Tech.

Предоставляет REST API для создания конфигураций T-pro модели и тестирования.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import logging
import asyncio
from contextlib import asynccontextmanager

# Импорты из нашего проекта
from ...core.database import get_session
from ...models.ai_models import AIModelConfiguration, ModelTypeEnum, ModelProviderEnum
from .model_service import ModelConfigurationService
from .model_factory import ModelFactory
from .t_pro_llm import TProLLM, TProLLMWithVLLM, get_tpro_benchmarks
from .streaming_config import StreamingConfig, load_preset_config

logger = logging.getLogger(__name__)

# Глобальные переменные для кэширования моделей
_tpro_models_cache = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Инициализация при запуске
    logger.info("Инициализация T-pro API...")
    yield
    # Очистка при завершении
    logger.info("Очистка T-pro моделей...")
    for model in _tpro_models_cache.values():
        if hasattr(model, 'aclose'):
            await model.aclose()
    _tpro_models_cache.clear()

app = FastAPI(
    title="T-pro Model API",
    description="API для работы с моделью T-pro-it-1.0 от T-Tech",
    version="1.0.0",
    lifespan=lifespan
)

# Pydantic модели для API

class TProConfigRequest(BaseModel):
    """Запрос на создание конфигурации T-pro модели."""
    name: str = Field(..., description="Название конфигурации")
    description: Optional[str] = Field(None, description="Описание конфигурации")
    model_name: str = Field("t-tech/T-pro-it-1.0", description="Название модели T-pro")
    
    # Параметры модели
    temperature: Optional[float] = Field(0.7, description="Temperature для генерации")
    max_tokens: Optional[int] = Field(512, description="Максимальное количество токенов")
    top_p: Optional[float] = Field(0.8, description="Top-p параметр")
    top_k: Optional[int] = Field(70, description="Top-k параметр")
    repetition_penalty: Optional[float] = Field(1.05, description="Штраф за повторения")
    
    # Параметры загрузки
    device: Optional[str] = Field("auto", description="Устройство для загрузки модели")
    torch_dtype: Optional[str] = Field("auto", description="Тип данных PyTorch")
    use_vllm: Optional[bool] = Field(False, description="Использовать VLLM для оптимизации")
    max_model_len: Optional[int] = Field(8192, description="Максимальная длина модели для VLLM")
    
    # Дополнительные параметры
    cache_dir: Optional[str] = Field(None, description="Директория для кэша модели")
    trust_remote_code: Optional[bool] = Field(True, description="Доверять удаленному коду")
    
    is_active: bool = Field(True, description="Активна ли конфигурация")
    is_default: bool = Field(False, description="Конфигурация по умолчанию")

class TProConfigResponse(BaseModel):
    """Ответ с конфигурацией T-pro модели."""
    id: int
    name: str
    description: Optional[str]
    model_name: str
    temperature: Optional[float]
    max_tokens: Optional[int]
    top_p: Optional[float]
    top_k: Optional[int]
    repetition_penalty: Optional[float]
    device: Optional[str]
    torch_dtype: Optional[str]
    use_vllm: Optional[bool]
    max_model_len: Optional[int]
    cache_dir: Optional[str]
    trust_remote_code: Optional[bool]
    is_active: bool
    is_default: bool
    created_at: str
    updated_at: str

class TProTestRequest(BaseModel):
    """Запрос на тестирование T-pro модели."""
    config_id: Optional[int] = Field(None, description="ID конфигурации")
    prompt: str = Field("Напиши стих про машинное обучение", description="Промпт для тестирования")
    streaming: bool = Field(True, description="Использовать потоковое получение")
    max_tokens: Optional[int] = Field(256, description="Максимальное количество токенов для теста")

class TProTestResponse(BaseModel):
    """Ответ тестирования T-pro модели."""
    success: bool
    response: Optional[str]
    error: Optional[str]
    model_info: Optional[Dict[str, Any]]
    performance_metrics: Optional[Dict[str, Any]]

class TProInterviewRequest(BaseModel):
    """Запрос на проведение интервью с T-pro."""
    candidate_name: str = Field(..., description="Имя кандидата")
    position: str = Field(..., description="Позиция")
    config_id: Optional[int] = Field(None, description="ID конфигурации T-pro")
    interview_type: str = Field("technical", description="Тип интервью: technical, behavioral, general")

class TProInterviewResponse(BaseModel):
    """Ответ проведения интервью."""
    success: bool
    interview_log: Optional[List[Dict[str, Any]]]
    error: Optional[str]
    duration_seconds: Optional[float]

# API Endpoints

@app.post("/configs/", response_model=TProConfigResponse)
async def create_tpro_config(
    config_request: TProConfigRequest,
    db: Session = Depends(get_session)
):
    """Создать конфигурацию T-pro модели."""
    try:
        service = ModelConfigurationService(db)
        
        # Собираем extra_params
        extra_params = {
            "temperature": config_request.temperature,
            "max_tokens": config_request.max_tokens,
            "top_p": config_request.top_p,
            "top_k": config_request.top_k,
            "repetition_penalty": config_request.repetition_penalty,
            "device": config_request.device,
            "torch_dtype": config_request.torch_dtype,
            "use_vllm": config_request.use_vllm,
            "max_model_len": config_request.max_model_len,
            "cache_dir": config_request.cache_dir,
            "trust_remote_code": config_request.trust_remote_code
        }
        
        # Создаем конфигурацию
        config_id = service.create_ai_model_configuration(
            name=config_request.name,
            description=config_request.description,
            model_type=ModelTypeEnum.LLM,
            provider=ModelProviderEnum.T_TECH,
            model_name=config_request.model_name,
            api_key_name=None,  # T-pro не требует API ключа
            endpoint_url=None,
            temperature=config_request.temperature,
            max_tokens=config_request.max_tokens,
            timeout=300,  # 5 минут для загрузки модели
            extra_params=extra_params,
            is_active=config_request.is_active,
            is_default=config_request.is_default
        )
        
        if not config_id:
            raise HTTPException(status_code=500, detail="Failed to create T-pro configuration")
        
        # Получаем созданную конфигурацию
        config = db.query(AIModelConfiguration).get(config_id)
        
        return TProConfigResponse(
            id=config.id,
            name=config.name,
            description=config.description,
            model_name=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.extra_params.get("top_p"),
            top_k=config.extra_params.get("top_k"),
            repetition_penalty=config.extra_params.get("repetition_penalty"),
            device=config.extra_params.get("device"),
            torch_dtype=config.extra_params.get("torch_dtype"),
            use_vllm=config.extra_params.get("use_vllm"),
            max_model_len=config.extra_params.get("max_model_len"),
            cache_dir=config.extra_params.get("cache_dir"),
            trust_remote_code=config.extra_params.get("trust_remote_code"),
            is_active=config.is_active,
            is_default=config.is_default,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error creating T-pro configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/configs/", response_model=List[TProConfigResponse])
async def list_tpro_configs(
    active_only: bool = True,
    db: Session = Depends(get_session)
):
    """Получить список конфигураций T-pro моделей."""
    try:
        query = db.query(AIModelConfiguration).filter(
            AIModelConfiguration.model_type == ModelTypeEnum.LLM,
            AIModelConfiguration.provider == ModelProviderEnum.T_TECH
        )
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        configs = query.all()
        
        return [
            TProConfigResponse(
                id=config.id,
                name=config.name,
                description=config.description,
                model_name=config.model_name,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.extra_params.get("top_p"),
                top_k=config.extra_params.get("top_k"),
                repetition_penalty=config.extra_params.get("repetition_penalty"),
                device=config.extra_params.get("device"),
                torch_dtype=config.extra_params.get("torch_dtype"),
                use_vllm=config.extra_params.get("use_vllm"),
                max_model_len=config.extra_params.get("max_model_len"),
                cache_dir=config.extra_params.get("cache_dir"),
                trust_remote_code=config.extra_params.get("trust_remote_code"),
                is_active=config.is_active,
                is_default=config.is_default,
                created_at=config.created_at.isoformat(),
                updated_at=config.updated_at.isoformat()
            )
            for config in configs
        ]
        
    except Exception as e:
        logger.error(f"Error listing T-pro configurations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test", response_model=TProTestResponse)
async def test_tpro_model(
    request: TProTestRequest,
    db: Session = Depends(get_session)
):
    """Протестировать T-pro модель."""
    import time
    start_time = time.time()
    
    try:
        # Получаем конфигурацию
        if request.config_id:
            config = (
                db.query(AIModelConfiguration)
                .filter_by(id=request.config_id, model_type=ModelTypeEnum.LLM, provider=ModelProviderEnum.T_TECH)
                .first()
            )
            if not config:
                raise HTTPException(status_code=404, detail="T-pro configuration not found")
        else:
            # Используем конфигурацию по умолчанию
            config = (
                db.query(AIModelConfiguration)
                .filter_by(model_type=ModelTypeEnum.LLM, provider=ModelProviderEnum.T_TECH, is_default=True, is_active=True)
                .first()
            )
            if not config:
                raise HTTPException(status_code=404, detail="No default T-pro configuration found")
        
        # Создаем модель
        config_dict = {
            "name": config.name,
            "provider": "t_tech",
            "model_name": config.model_name,
            "temperature": config.temperature,
            "max_tokens": request.max_tokens or config.max_tokens,
            "top_p": config.extra_params.get("top_p"),
            "top_k": config.extra_params.get("top_k"),
            "repetition_penalty": config.extra_params.get("repetition_penalty"),
            "device": config.extra_params.get("device"),
            "torch_dtype": config.extra_params.get("torch_dtype"),
            "use_vllm": config.extra_params.get("use_vllm"),
            "max_model_len": config.extra_params.get("max_model_len"),
            "cache_dir": config.extra_params.get("cache_dir"),
            "trust_remote_code": config.extra_params.get("trust_remote_code")
        }
        
        # Создаем модель
        model = ModelFactory.create_llm_model(config_dict)
        
        # Получаем информацию о модели
        model_info = model.get_model_info() if hasattr(model, 'get_model_info') else {}
        
        # Тестируем модель
        from videosdk.agents import ChatContext, ChatMessage, ChatRole
        
        messages = ChatContext()
        messages.add_message(ChatMessage(
            role=ChatRole.USER,
            content=request.prompt
        ))
        
        # Генерируем ответ
        inference_start = time.time()
        response_chunks = []
        
        if request.streaming:
            async for chunk in model.chat(messages):
                response_chunks.append(chunk.content)
        else:
            # Для не-потокового режима собираем все чанки
            async for chunk in model.chat(messages):
                response_chunks.append(chunk.content)
        
        inference_time = time.time() - inference_start
        total_time = time.time() - start_time
        
        response_text = "".join(response_chunks)
        
        return TProTestResponse(
            success=True,
            response=response_text,
            error=None,
            model_info=model_info,
            performance_metrics={
                "inference_time_seconds": inference_time,
                "total_time_seconds": total_time,
                "tokens_generated": len(response_text.split()),
                "streaming_enabled": request.streaming
            }
        )
        
    except Exception as e:
        error_time = time.time() - start_time
        logger.error(f"Error testing T-pro model: {e}")
        
        return TProTestResponse(
            success=False,
            response=None,
            error=str(e),
            model_info=None,
            performance_metrics={
                "error_time_seconds": error_time
            }
        )

@app.post("/interview", response_model=TProInterviewResponse)
async def conduct_interview(
    request: TProInterviewRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session)
):
    """Провести интервью с использованием T-pro модели."""
    import time
    start_time = time.time()
    
    try:
        # Получаем конфигурацию
        if request.config_id:
            config = (
                db.query(AIModelConfiguration)
                .filter_by(id=request.config_id, model_type=ModelTypeEnum.LLM, provider=ModelProviderEnum.T_TECH)
                .first()
            )
            if not config:
                raise HTTPException(status_code=404, detail="T-pro configuration not found")
        else:
            config = (
                db.query(AIModelConfiguration)
                .filter_by(model_type=ModelTypeEnum.LLM, provider=ModelProviderEnum.T_TECH, is_default=True, is_active=True)
                .first()
            )
            if not config:
                raise HTTPException(status_code=404, detail="No default T-pro configuration found")
        
        # Создаем модель
        config_dict = {
            "name": config.name,
            "provider": "t_tech",
            "model_name": config.model_name,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.extra_params.get("top_p"),
            "top_k": config.extra_params.get("top_k"),
            "repetition_penalty": config.extra_params.get("repetition_penalty"),
            "device": config.extra_params.get("device"),
            "torch_dtype": config.extra_params.get("torch_dtype"),
            "use_vllm": config.extra_params.get("use_vllm"),
            "max_model_len": config.extra_params.get("max_model_len"),
            "cache_dir": config.extra_params.get("cache_dir"),
            "trust_remote_code": config.extra_params.get("trust_remote_code")
        }
        
        model = ModelFactory.create_llm_model(config_dict)
        
        # Устанавливаем системный промпт для интервью
        interview_prompt = f"""
        Ты T-pro, профессиональный HR-ассистент от Т-Технологии. 
        Твоя задача - проводить {request.interview_type} интервью с кандидатом {request.candidate_name} на позицию {request.position}.
        
        Твои качества:
        - Профессиональный и вежливый тон
        - Глубокие знания в области IT и разработки
        - Умение задавать правильные вопросы
        - Способность оценивать ответы кандидатов
        - Поддержка кандидата в процессе интервью
        
        Начинай интервью с приветствия и краткого представления.
        """
        
        if hasattr(model, 'set_system_prompt'):
            model.set_system_prompt(interview_prompt)
        
        # Проводим интервью
        from videosdk.agents import ChatContext, ChatMessage, ChatRole
        
        messages = ChatContext()
        messages.add_message(ChatMessage(
            role=ChatRole.USER,
            content=f"Начни интервью с кандидатом {request.candidate_name} на позицию {request.position}"
        ))
        
        interview_log = []
        
        # Получаем начальный ответ
        response_chunks = []
        async for chunk in model.chat(messages):
            response_chunks.append(chunk.content)
        
        initial_response = "".join(response_chunks)
        
        interview_log.append({
            "speaker": "T-pro",
            "message": initial_response,
            "timestamp": time.time() - start_time
        })
        
        duration = time.time() - start_time
        
        return TProInterviewResponse(
            success=True,
            interview_log=interview_log,
            error=None,
            duration_seconds=duration
        )
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error conducting interview: {e}")
        
        return TProInterviewResponse(
            success=False,
            interview_log=None,
            error=str(e),
            duration_seconds=duration
        )

@app.get("/benchmarks/")
async def get_benchmarks():
    """Получить результаты бенчмарков T-pro."""
    try:
        benchmarks = get_tpro_benchmarks()
        return {
            "model": "t-tech/T-pro-it-1.0",
            "benchmarks": benchmarks,
            "note": "T-pro показывает отличные результаты на русских бенчмарках"
        }
    except Exception as e:
        logger.error(f"Error getting benchmarks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/")
async def check_tpro_health(db: Session = Depends(get_session)):
    """Проверить состояние T-pro конфигураций."""
    try:
        # Подсчитываем активные конфигурации
        active_configs = (
            db.query(AIModelConfiguration)
            .filter_by(model_type=ModelTypeEnum.LLM, provider=ModelProviderEnum.T_TECH, is_active=True)
            .count()
        )
        
        default_config = (
            db.query(AIModelConfiguration)
            .filter_by(model_type=ModelTypeEnum.LLM, provider=ModelProviderEnum.T_TECH, is_default=True, is_active=True)
            .first()
        )
        
        return {
            "status": "healthy",
            "active_tpro_configs": active_configs,
            "has_default_config": default_config is not None,
            "default_config_name": default_config.name if default_config else None,
            "model_info": {
                "name": "t-tech/T-pro-it-1.0",
                "provider": "T-Tech",
                "language": "Russian",
                "base_model": "Qwen 2.5",
                "parameters": "32.8B"
            }
        }
        
    except Exception as e:
        logger.error(f"T-pro health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
