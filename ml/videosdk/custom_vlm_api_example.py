"""
API для управления и тестирования Custom Endpoint VLM моделей.

Поддерживает любые VLM API endpoints с различными форматами запросов и аутентификации.
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import logging
import base64
import io
import requests
from PIL import Image

# Импорты из нашего проекта
from ...core.database import get_session
from ...models.ai_models import AIModelConfiguration, ModelTypeEnum, ModelProviderEnum
from .model_service import ModelConfigurationService
from .model_factory import ModelFactory

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Custom VLM Endpoints API",
    description="API для управления кастомными VLM endpoints",
    version="1.0.0"
)

# Pydantic модели для API

class CustomVLMConfigRequest(BaseModel):
    """Запрос на создание конфигурации кастомного VLM endpoint."""
    name: str = Field(..., description="Название конфигурации")
    description: Optional[str] = Field(None, description="Описание конфигурации")
    model_name: str = Field(..., description="Название модели")
    endpoint_url: str = Field(..., description="URL endpoint API")
    api_key_name: Optional[str] = Field(None, description="Название переменной окружения с API ключом")
    
    # Параметры модели
    temperature: Optional[float] = Field(0.7, description="Temperature")
    max_tokens: Optional[int] = Field(4096, description="Максимальное количество токенов")
    timeout: Optional[int] = Field(30, description="Таймаут в секундах")
    
    # Параметры интеграции
    request_format: str = Field("openai", description="Формат запроса: openai, anthropic, gemini, custom")
    auth_type: str = Field("bearer", description="Тип аутентификации: bearer, api_key, anthropic, none, custom_header")
    auth_header: Optional[str] = Field(None, description="Кастомный заголовок для аутентификации")
    endpoint_path: Optional[str] = Field(None, description="Путь endpoint для кастомных API")
    response_field: Optional[str] = Field("text", description="Поле ответа для извлечения текста")
    
    # Дополнительные параметры
    custom_params: Optional[Dict[str, Any]] = Field(None, description="Кастомные параметры запроса")
    headers: Optional[Dict[str, str]] = Field(None, description="Дополнительные заголовки")
    
    is_active: bool = Field(True, description="Активна ли конфигурация")
    is_default: bool = Field(False, description="Конфигурация по умолчанию")

class CustomVLMResponse(BaseModel):
    """Ответ с конфигурацией кастомного VLM endpoint."""
    id: int
    name: str
    description: Optional[str]
    model_name: str
    endpoint_url: str
    api_key_name: Optional[str]
    temperature: Optional[float]
    max_tokens: Optional[int]
    timeout: Optional[int]
    request_format: str
    auth_type: str
    is_active: bool
    is_default: bool
    created_at: str
    updated_at: str

class VLMEndpointTestRequest(BaseModel):
    """Запрос на тестирование VLM endpoint."""
    endpoint_id: int = Field(..., description="ID конфигурации endpoint")
    prompt: str = Field("Проанализируй это изображение", description="Запрос для анализа")
    image_data: Optional[str] = Field(None, description="Base64 изображение")
    test_connectivity_only: bool = Field(False, description="Только проверка соединения")

class VLMEndpointTestResponse(BaseModel):
    """Ответ тестирования VLM endpoint."""
    success: bool
    analysis: Optional[str]
    error: Optional[str]
    endpoint_info: Dict[str, Any]
    connectivity_test: Dict[str, Any]
    performance_metrics: Dict[str, Any]

# Предустановленные шаблоны для популярных сервисов
ENDPOINT_TEMPLATES = {
    "oollama": {
        "name": "Oollama Vision API",
        "endpoint_url": "http://localhost:11434",
        "model_name": "llava:13b",
        "request_format": "custom",
        "auth_type": "none",
        "endpoint_path": "/api/generate",
        "custom_params": {
            "stream": False,
            "format": "json"
        },
        "response_field": "response"
    },
    "vllm": {
        "name": "vLLM Vision Server",
        "endpoint_url": "http://localhost:8000",
        "model_name": "llava-hf/llava-1.5-7b-hf",
        "request_format": "openai",
        "auth_type": "none"
    },
    "text_generation_inference": {
        "name": "Hugging Face TGI",
        "endpoint_url": "http://localhost:8080",
        "model_name": "llava-hf/llava-1.5-7b-hf",
        "request_format": "custom",
        "auth_type": "bearer",
        "endpoint_path": "/generate",
        "custom_params": {
            "parameters": {
                "max_new_tokens": 2048,
                "do_sample": True
            }
        },
        "response_field": "generated_text"
    },
    "openai_compatible": {
        "name": "OpenAI Compatible API",
        "endpoint_url": "https://api.your-provider.com",
        "model_name": "gpt-4-vision-preview",
        "request_format": "openai",
        "auth_type": "bearer"
    },
    "anthropic_compatible": {
        "name": "Anthropic Compatible API",
        "endpoint_url": "https://api.your-provider.com",
        "model_name": "claude-3-sonnet-20240229",
        "request_format": "anthropic",
        "auth_type": "anthropic"
    }
}

@app.get("/templates/")
async def get_endpoint_templates():
    """Получить шаблоны для популярных VLM endpoints."""
    return {
        "templates": ENDPOINT_TEMPLATES,
        "usage": "Используйте эти шаблоны как основу для создания конфигураций",
        "note": "Не забудьте изменить endpoint_url и API ключи под ваши настройки"
    }

@app.post("/endpoints/", response_model=CustomVLMResponse)
async def create_custom_vlm_endpoint(
    config_request: CustomVLMConfigRequest,
    db: Session = Depends(get_session)
):
    """Создать конфигурацию кастомного VLM endpoint."""
    try:
        service = ModelConfigurationService(db)
        
        # Собираем extra_params
        extra_params = {
            "request_format": config_request.request_format,
            "auth_type": config_request.auth_type,
            "detail": "high"  # для OpenAI формата
        }
        
        if config_request.auth_header:
            extra_params["auth_header"] = config_request.auth_header
        
        if config_request.endpoint_path:
            extra_params["endpoint_path"] = config_request.endpoint_path
        
        if config_request.response_field:
            extra_params["response_field"] = config_request.response_field
        
        if config_request.custom_params:
            extra_params["custom_params"] = config_request.custom_params
        
        if config_request.headers:
            extra_params["headers"] = config_request.headers
        
        # Создаем конфигурацию
        config_id = service.create_ai_model_configuration(
            name=config_request.name,
            description=config_request.description,
            model_type=ModelTypeEnum.VISION,
            provider=ModelProviderEnum.CUSTOM_ENDPOINT,
            model_name=config_request.model_name,
            api_key_name=config_request.api_key_name,
            endpoint_url=config_request.endpoint_url,
            temperature=config_request.temperature,
            max_tokens=config_request.max_tokens,
            timeout=config_request.timeout,
            extra_params=extra_params,
            is_active=config_request.is_active,
            is_default=config_request.is_default
        )
        
        if not config_id:
            raise HTTPException(status_code=500, detail="Failed to create custom VLM endpoint configuration")
        
        # Получаем созданную конфигурацию
        config = db.query(AIModelConfiguration).get(config_id)
        
        return CustomVLMResponse(
            id=config.id,
            name=config.name,
            description=config.description,
            model_name=config.model_name,
            endpoint_url=config.endpoint_url,
            api_key_name=config.api_key_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout,
            request_format=config.extra_params.get("request_format", "openai"),
            auth_type=config.extra_params.get("auth_type", "bearer"),
            is_active=config.is_active,
            is_default=config.is_default,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error creating custom VLM endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/endpoints/from-template/{template_name}", response_model=CustomVLMResponse)
async def create_from_template(
    template_name: str,
    endpoint_url: str = Form(..., description="URL вашего endpoint"),
    api_key_name: Optional[str] = Form(None, description="Название переменной с API ключом"),
    model_name: Optional[str] = Form(None, description="Переопределить название модели"),
    db: Session = Depends(get_session)
):
    """Создать конфигурацию на основе шаблона."""
    try:
        if template_name not in ENDPOINT_TEMPLATES:
            raise HTTPException(status_code=404, detail=f"Template {template_name} not found")
        
        template = ENDPOINT_TEMPLATES[template_name].copy()
        
        # Переопределяем параметры
        template["endpoint_url"] = endpoint_url
        if api_key_name:
            template["api_key_name"] = api_key_name
        if model_name:
            template["model_name"] = model_name
        
        # Создаем запрос
        config_request = CustomVLMConfigRequest(
            name=template["name"],
            description=f"Создано из шаблона {template_name}",
            model_name=template["model_name"],
            endpoint_url=template["endpoint_url"],
            api_key_name=template.get("api_key_name"),
            request_format=template["request_format"],
            auth_type=template["auth_type"],
            endpoint_path=template.get("endpoint_path"),
            response_field=template.get("response_field", "text"),
            custom_params=template.get("custom_params"),
            headers=template.get("headers")
        )
        
        return await create_custom_vlm_endpoint(config_request, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating from template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/endpoints/", response_model=List[CustomVLMResponse])
async def list_custom_vlm_endpoints(
    active_only: bool = True,
    db: Session = Depends(get_session)
):
    """Получить список кастомных VLM endpoints."""
    try:
        query = db.query(AIModelConfiguration).filter(
            AIModelConfiguration.model_type == ModelTypeEnum.VISION,
            AIModelConfiguration.provider == ModelProviderEnum.CUSTOM_ENDPOINT
        )
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        configs = query.all()
        
        return [
            CustomVLMResponse(
                id=config.id,
                name=config.name,
                description=config.description,
                model_name=config.model_name,
                endpoint_url=config.endpoint_url,
                api_key_name=config.api_key_name,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                timeout=config.timeout,
                request_format=config.extra_params.get("request_format", "openai"),
                auth_type=config.extra_params.get("auth_type", "bearer"),
                is_active=config.is_active,
                is_default=config.is_default,
                created_at=config.created_at.isoformat(),
                updated_at=config.updated_at.isoformat()
            )
            for config in configs
        ]
        
    except Exception as e:
        logger.error(f"Error listing custom VLM endpoints: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/endpoints/{endpoint_id}/test", response_model=VLMEndpointTestResponse)
async def test_custom_vlm_endpoint(
    endpoint_id: int,
    request: VLMEndpointTestRequest,
    db: Session = Depends(get_session)
):
    """Протестировать кастомный VLM endpoint."""
    import time
    start_time = time.time()
    
    try:
        # Получаем конфигурацию
        config = (
            db.query(AIModelConfiguration)
            .filter_by(id=endpoint_id, model_type=ModelTypeEnum.VISION, provider=ModelProviderEnum.CUSTOM_ENDPOINT)
            .first()
        )
        
        if not config:
            raise HTTPException(status_code=404, detail="Custom VLM endpoint not found")
        
        endpoint_info = {
            "name": config.name,
            "endpoint_url": config.endpoint_url,
            "model_name": config.model_name,
            "request_format": config.extra_params.get("request_format", "openai"),
            "auth_type": config.extra_params.get("auth_type", "bearer")
        }
        
        # Тест соединения
        connectivity_test = await _test_connectivity(config.endpoint_url, config.timeout)
        
        if request.test_connectivity_only:
            return VLMEndpointTestResponse(
                success=connectivity_test["success"],
                analysis="Тест соединения выполнен",
                error=connectivity_test.get("error"),
                endpoint_info=endpoint_info,
                connectivity_test=connectivity_test,
                performance_metrics={"connectivity_time_seconds": time.time() - start_time}
            )
        
        # Если нет изображения, возвращаем информацию о готовности
        if not request.image_data:
            return VLMEndpointTestResponse(
                success=connectivity_test["success"],
                analysis="Endpoint готов к анализу. Передайте image_data для полного тестирования.",
                error=None,
                endpoint_info=endpoint_info,
                connectivity_test=connectivity_test,
                performance_metrics={"setup_time_seconds": time.time() - start_time}
            )
        
        # Создаем конфигурационный словарь
        config_dict = {
            "name": config.name,
            "provider": "custom_endpoint",
            "model_name": config.model_name,
            "endpoint_url": config.endpoint_url,
            "api_key_name": config.api_key_name,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "timeout": config.timeout,
            "extra_params": config.extra_params or {}
        }
        
        # Тестируем Vision модель
        try:
            vision_model = ModelFactory.create_vision_model(config_dict)
            model_creation_time = time.time() - start_time
            
            # Декодируем изображение
            image_bytes = base64.b64decode(request.image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Выполняем анализ
            inference_start = time.time()
            analysis = vision_model.analyze_image(image, request.prompt)
            inference_time = time.time() - inference_start
            
            total_time = time.time() - start_time
            
            return VLMEndpointTestResponse(
                success=True,
                analysis=analysis,
                error=None,
                endpoint_info=endpoint_info,
                connectivity_test=connectivity_test,
                performance_metrics={
                    "model_creation_time_seconds": model_creation_time,
                    "inference_time_seconds": inference_time,
                    "total_time_seconds": total_time
                }
            )
            
        except Exception as e:
            error_time = time.time() - start_time
            logger.error(f"Error testing custom VLM endpoint: {e}")
            
            return VLMEndpointTestResponse(
                success=False,
                analysis=None,
                error=str(e),
                endpoint_info=endpoint_info,
                connectivity_test=connectivity_test,
                performance_metrics={
                    "error_time_seconds": error_time
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in custom VLM endpoint test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _test_connectivity(endpoint_url: str, timeout: int = 30) -> Dict[str, Any]:
    """Тест соединения с endpoint."""
    import time
    start_time = time.time()
    
    try:
        # Простая проверка доступности
        response = requests.get(
            f"{endpoint_url.rstrip('/')}/health",
            timeout=min(timeout, 10)
        )
        
        connectivity_time = time.time() - start_time
        
        if response.status_code == 200:
            return {
                "success": True,
                "status_code": response.status_code,
                "response_time_ms": connectivity_time * 1000,
                "endpoint_available": True
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "response_time_ms": connectivity_time * 1000,
                "endpoint_available": False,
                "error": f"Unexpected status code: {response.status_code}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "endpoint_available": False,
            "error": "Connection failed - endpoint not reachable"
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "endpoint_available": False,
            "error": "Connection timeout"
        }
    except Exception as e:
        return {
            "success": False,
            "endpoint_available": False,
            "error": f"Connectivity test failed: {str(e)}"
        }

@app.post("/endpoints/{endpoint_id}/test/upload")
async def test_endpoint_with_upload(
    endpoint_id: int,
    file: UploadFile = File(...),
    prompt: str = Form("Проанализируй это изображение"),
    test_connectivity_only: bool = Form(False),
    db: Session = Depends(get_session)
):
    """Протестировать endpoint с загруженным изображением."""
    try:
        # Проверяем тип файла
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Читаем и конвертируем изображение
        image_bytes = await file.read()
        image_b64 = base64.b64encode(image_bytes).decode()
        
        # Используем существующий endpoint для тестирования
        request = VLMEndpointTestRequest(
            endpoint_id=endpoint_id,
            prompt=prompt,
            image_data=image_b64,
            test_connectivity_only=test_connectivity_only
        )
        
        return await test_custom_vlm_endpoint(endpoint_id, request, db)
        
    except Exception as e:
        logger.error(f"Error testing endpoint with upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/examples/configurations/")
async def get_configuration_examples():
    """Получить примеры конфигураций для различных сценариев."""
    return {
        "examples": {
            "oollama_local": {
                "name": "Oollama Local LLaVA",
                "description": "Локальный Oollama с LLaVA моделью",
                "endpoint_url": "http://localhost:11434",
                "model_name": "llava:13b",
                "request_format": "custom",
                "auth_type": "none",
                "endpoint_path": "/api/generate",
                "custom_params": {
                    "stream": False,
                    "format": "json"
                },
                "response_field": "response"
            },
            "vllm_server": {
                "name": "vLLM Production Server",
                "description": "Production vLLM сервер с LLaVA",
                "endpoint_url": "http://your-vllm-server:8000",
                "model_name": "llava-hf/llava-1.5-13b-hf",
                "request_format": "openai",
                "auth_type": "bearer",
                "api_key_name": "VLLM_API_KEY"
            },
            "replicate_api": {
                "name": "Replicate Vision API",
                "description": "Replicate с Vision моделями",
                "endpoint_url": "https://api.replicate.com",
                "model_name": "yorickvp/llava-13b",
                "request_format": "custom",
                "auth_type": "custom_header",
                "auth_header": "Authorization",
                "api_key_name": "REPLICATE_API_TOKEN",
                "endpoint_path": "/v1/predictions",
                "custom_params": {
                    "version": "model_version_hash",
                    "input": {}
                },
                "response_field": "output"
            },
            "huggingface_inference": {
                "name": "Hugging Face Inference API",
                "description": "HF Inference API с Vision моделью",
                "endpoint_url": "https://api-inference.huggingface.co",
                "model_name": "llava-hf/llava-1.5-7b-hf",
                "request_format": "custom",
                "auth_type": "bearer",
                "api_key_name": "HUGGINGFACE_API_KEY",
                "endpoint_path": "/models/llava-hf/llava-1.5-7b-hf",
                "response_field": "generated_text"
            }
        },
        "usage_note": "Адаптируйте примеры под ваши конкретные endpoints и модели"
    }

@app.get("/health/custom-endpoints")
async def check_custom_endpoints_health(db: Session = Depends(get_session)):
    """Проверить состояние всех кастомных endpoints."""
    try:
        endpoints = db.query(AIModelConfiguration).filter(
            AIModelConfiguration.model_type == ModelTypeEnum.VISION,
            AIModelConfiguration.provider == ModelProviderEnum.CUSTOM_ENDPOINT,
            AIModelConfiguration.is_active == True
        ).all()
        
        health_results = []
        
        for endpoint in endpoints:
            connectivity = await _test_connectivity(endpoint.endpoint_url, endpoint.timeout or 30)
            
            health_results.append({
                "id": endpoint.id,
                "name": endpoint.name,
                "endpoint_url": endpoint.endpoint_url,
                "status": "healthy" if connectivity["success"] else "unhealthy",
                "connectivity": connectivity
            })
        
        overall_status = "healthy" if all(r["status"] == "healthy" for r in health_results) else "degraded"
        
        return {
            "status": overall_status,
            "total_endpoints": len(endpoints),
            "healthy_endpoints": len([r for r in health_results if r["status"] == "healthy"]),
            "endpoints": health_results
        }
        
    except Exception as e:
        logger.error(f"Custom endpoints health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "endpoints": []
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
