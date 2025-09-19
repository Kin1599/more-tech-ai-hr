"""
API для управления локальными Vision Language Models (VLM).

Демонстрирует создание, настройку и тестирование локальных VLM моделей
для полной независимости от внешних API.
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import logging
import base64
import io
import os
import psutil
import GPUtil
from PIL import Image

# Импорты из нашего проекта
from ...core.database import get_session
from ...models.ai_models import AIModelConfiguration, ModelTypeEnum, ModelProviderEnum
from .model_service import ModelConfigurationService
from .model_factory import ModelFactory
from .screen_analysis_tool import create_screen_analysis_tool

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Local VLM Models API",
    description="API для управления локальными Vision Language Models",
    version="1.0.0"
)

# Pydantic модели для API

class LocalVLMConfigRequest(BaseModel):
    """Запрос на создание конфигурации локальной VLM."""
    name: str = Field(..., description="Название конфигурации")
    description: Optional[str] = Field(None, description="Описание конфигурации")
    provider: str = Field(..., description="Провайдер (local_llava, local_cogvlm, etc.)")
    model_name: str = Field(..., description="Название модели")
    model_path: str = Field(..., description="Путь к локальной модели")
    
    # Параметры модели
    context_length: Optional[int] = Field(2048, description="Длина контекста")
    temperature: Optional[float] = Field(0.4, description="Temperature")
    max_tokens: Optional[int] = Field(1024, description="Максимальное количество токенов")
    timeout: Optional[int] = Field(60, description="Таймаут в секундах")
    
    # Дополнительные параметры
    extra_params: Optional[Dict[str, Any]] = Field(None, description="Дополнительные параметры")
    is_active: bool = Field(True, description="Активна ли конфигурация")
    is_default: bool = Field(False, description="Конфигурация по умолчанию")

class LocalVLMResponse(BaseModel):
    """Ответ с конфигурацией локальной VLM."""
    id: int
    name: str
    description: Optional[str]
    provider: str
    model_name: str
    model_path: str
    context_length: Optional[int]
    temperature: Optional[float]
    max_tokens: Optional[int]
    timeout: Optional[int]
    extra_params: Optional[Dict[str, Any]]
    is_active: bool
    is_default: bool
    model_size_gb: Optional[float]
    gpu_memory_required: Optional[str]
    created_at: str
    updated_at: str

class VLMTestRequest(BaseModel):
    """Запрос на тестирование VLM модели."""
    vlm_config_id: int = Field(..., description="ID конфигурации VLM")
    prompt: str = Field("Проанализируй это изображение", description="Запрос для анализа")
    image_data: Optional[str] = Field(None, description="Base64 изображение")
    load_model: bool = Field(True, description="Загружать ли модель для тестирования")

class VLMTestResponse(BaseModel):
    """Ответ тестирования VLM модели."""
    success: bool
    analysis: Optional[str]
    error: Optional[str]
    model_info: Dict[str, Any]
    performance_metrics: Dict[str, Any]

class SystemResourcesResponse(BaseModel):
    """Ответ с информацией о системных ресурсах."""
    cpu_percent: float
    memory_total_gb: float
    memory_available_gb: float
    memory_used_percent: float
    gpu_info: List[Dict[str, Any]]
    disk_space_gb: float
    recommendations: List[str]

# Константы для моделей
LOCAL_VLM_MODELS = {
    "local_llava": {
        "display_name": "LLaVA (Large Language and Vision Assistant)",
        "variants": [
            {
                "name": "LLaVA 1.5 7B",
                "model_name": "llava-v1.5-7b-hf",
                "size_gb": 14,
                "gpu_memory_gb": 16,
                "description": "Компактная модель для быстрого анализа"
            },
            {
                "name": "LLaVA 1.6 34B", 
                "model_name": "llava-v1.6-34b-hf",
                "size_gb": 68,
                "gpu_memory_gb": 48,
                "description": "Мощная модель для детального анализа"
            }
        ],
        "dependencies": ["transformers", "torch", "accelerate", "pillow"],
        "installation": "pip install transformers torch accelerate pillow"
    },
    "local_cogvlm": {
        "display_name": "CogVLM (Cognitive Vision Language Model)",
        "variants": [
            {
                "name": "CogVLM Chat",
                "model_name": "cogvlm-chat-hf",
                "size_gb": 20,
                "gpu_memory_gb": 24,
                "description": "Модель с фокусом на диалог"
            }
        ],
        "dependencies": ["transformers", "torch", "accelerate"],
        "installation": "pip install transformers torch accelerate"
    },
    "local_qwen_vl": {
        "display_name": "Qwen-VL (Qwen Vision Language)",
        "variants": [
            {
                "name": "Qwen-VL Chat",
                "model_name": "Qwen-VL-Chat",
                "size_gb": 16,
                "gpu_memory_gb": 20,
                "description": "Многоязычная модель"
            }
        ],
        "dependencies": ["transformers", "torch", "accelerate"],
        "installation": "pip install transformers torch accelerate"
    },
    "local_moondream": {
        "display_name": "MoonDream2",
        "variants": [
            {
                "name": "MoonDream2",
                "model_name": "vikhyatk/moondream2",
                "size_gb": 3,
                "gpu_memory_gb": 6,
                "description": "Легковесная модель"
            }
        ],
        "dependencies": ["transformers", "torch", "pillow"],
        "installation": "pip install transformers torch pillow"
    },
    "local_internvl": {
        "display_name": "InternVL",
        "variants": [
            {
                "name": "InternVL Chat V1.5",
                "model_name": "InternVL-Chat-V1-5",
                "size_gb": 25,
                "gpu_memory_gb": 32,
                "description": "Продвинутая модель"
            }
        ],
        "dependencies": ["transformers", "torch", "accelerate"],
        "installation": "pip install transformers torch accelerate"
    }
}

@app.get("/system/resources", response_model=SystemResourcesResponse)
async def get_system_resources():
    """Получить информацию о системных ресурсах."""
    try:
        # CPU и память
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # GPU информация
        gpu_info = []
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                gpu_info.append({
                    "id": gpu.id,
                    "name": gpu.name,
                    "memory_total_mb": gpu.memoryTotal,
                    "memory_used_mb": gpu.memoryUsed,
                    "memory_free_mb": gpu.memoryFree,
                    "memory_util_percent": gpu.memoryUtil * 100,
                    "gpu_util_percent": gpu.load * 100,
                    "temperature": gpu.temperature
                })
        except Exception as e:
            logger.warning(f"Could not get GPU info: {e}")
        
        # Дисковое пространство
        disk_usage = psutil.disk_usage('/')
        disk_space_gb = disk_usage.free / (1024**3)
        
        # Рекомендации
        recommendations = []
        
        if memory.available / (1024**3) < 8:
            recommendations.append("Рекомендуется минимум 8GB RAM для локальных VLM")
        
        if not gpu_info:
            recommendations.append("GPU не обнаружен. Рекомендуется NVIDIA GPU с 8GB+ VRAM")
        elif gpu_info and gpu_info[0]["memory_total_mb"] < 8000:
            recommendations.append("Рекомендуется GPU с минимум 8GB VRAM для VLM моделей")
        
        if disk_space_gb < 50:
            recommendations.append("Рекомендуется минимум 50GB свободного места для моделей")
        
        return SystemResourcesResponse(
            cpu_percent=cpu_percent,
            memory_total_gb=memory.total / (1024**3),
            memory_available_gb=memory.available / (1024**3),
            memory_used_percent=memory.percent,
            gpu_info=gpu_info,
            disk_space_gb=disk_space_gb,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Error getting system resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/available")
async def get_available_models():
    """Получить список доступных локальных VLM моделей."""
    return {
        "models": LOCAL_VLM_MODELS,
        "total_providers": len(LOCAL_VLM_MODELS),
        "installation_note": "Для использования локальных моделей требуется их предварительная загрузка"
    }

@app.post("/models/", response_model=LocalVLMResponse)
async def create_local_vlm_config(
    config_request: LocalVLMConfigRequest,
    db: Session = Depends(get_session)
):
    """Создать конфигурацию локальной VLM модели."""
    try:
        # Проверяем, что провайдер поддерживается
        if config_request.provider not in LOCAL_VLM_MODELS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported local VLM provider: {config_request.provider}"
            )
        
        # Проверяем существование пути к модели
        if not os.path.exists(config_request.model_path):
            logger.warning(f"Model path does not exist: {config_request.model_path}")
        
        service = ModelConfigurationService(db)
        
        # Создаем конфигурацию
        config_id = service.create_ai_model_configuration(
            name=config_request.name,
            description=config_request.description,
            model_type=ModelTypeEnum.VISION,
            provider=ModelProviderEnum(config_request.provider),
            model_name=config_request.model_name,
            model_path=config_request.model_path,
            context_length=config_request.context_length,
            temperature=config_request.temperature,
            max_tokens=config_request.max_tokens,
            timeout=config_request.timeout,
            extra_params=config_request.extra_params,
            is_active=config_request.is_active,
            is_default=config_request.is_default
        )
        
        if not config_id:
            raise HTTPException(status_code=500, detail="Failed to create VLM configuration")
        
        # Получаем созданную конфигурацию
        config = db.query(AIModelConfiguration).get(config_id)
        
        # Оцениваем размер модели
        model_size_gb = None
        gpu_memory_required = None
        
        provider_info = LOCAL_VLM_MODELS.get(config_request.provider, {})
        for variant in provider_info.get("variants", []):
            if variant["model_name"] == config_request.model_name:
                model_size_gb = variant["size_gb"]
                gpu_memory_required = f"{variant['gpu_memory_gb']}GB"
                break
        
        return LocalVLMResponse(
            id=config.id,
            name=config.name,
            description=config.description,
            provider=config.provider.value,
            model_name=config.model_name,
            model_path=config.model_path,
            context_length=config.context_length,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout,
            extra_params=config.extra_params,
            is_active=config.is_active,
            is_default=config.is_default,
            model_size_gb=model_size_gb,
            gpu_memory_required=gpu_memory_required,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error creating local VLM configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/", response_model=List[LocalVLMResponse])
async def list_local_vlm_configs(
    active_only: bool = True,
    db: Session = Depends(get_session)
):
    """Получить список конфигураций локальных VLM."""
    try:
        local_providers = [p.value for p in ModelProviderEnum if p.value.startswith('local_') and 'vlm' in p.value or p.value in LOCAL_VLM_MODELS]
        
        query = db.query(AIModelConfiguration).filter(
            AIModelConfiguration.model_type == ModelTypeEnum.VISION,
            AIModelConfiguration.provider.in_(local_providers)
        )
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        configs = query.all()
        
        results = []
        for config in configs:
            # Оцениваем размер модели
            model_size_gb = None
            gpu_memory_required = None
            
            provider_info = LOCAL_VLM_MODELS.get(config.provider.value, {})
            for variant in provider_info.get("variants", []):
                if variant["model_name"] == config.model_name:
                    model_size_gb = variant["size_gb"]
                    gpu_memory_required = f"{variant['gpu_memory_gb']}GB"
                    break
            
            results.append(LocalVLMResponse(
                id=config.id,
                name=config.name,
                description=config.description,
                provider=config.provider.value,
                model_name=config.model_name,
                model_path=config.model_path,
                context_length=config.context_length,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                timeout=config.timeout,
                extra_params=config.extra_params,
                is_active=config.is_active,
                is_default=config.is_default,
                model_size_gb=model_size_gb,
                gpu_memory_required=gpu_memory_required,
                created_at=config.created_at.isoformat(),
                updated_at=config.updated_at.isoformat()
            ))
        
        return results
        
    except Exception as e:
        logger.error(f"Error listing local VLM configurations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/{config_id}/test", response_model=VLMTestResponse)
async def test_local_vlm_model(
    config_id: int,
    request: VLMTestRequest,
    db: Session = Depends(get_session)
):
    """Протестировать локальную VLM модель."""
    import time
    start_time = time.time()
    
    try:
        # Получаем конфигурацию
        config = (
            db.query(AIModelConfiguration)
            .filter_by(id=config_id, model_type=ModelTypeEnum.VISION)
            .first()
        )
        
        if not config:
            raise HTTPException(status_code=404, detail="VLM configuration not found")
        
        model_info = {
            "name": config.name,
            "provider": config.provider.value,
            "model_name": config.model_name,
            "model_path": config.model_path
        }
        
        # Если не нужно загружать модель, возвращаем только информацию
        if not request.load_model:
            return VLMTestResponse(
                success=True,
                analysis="Модель не загружалась (load_model=False)",
                error=None,
                model_info=model_info,
                performance_metrics={"load_time_seconds": 0}
            )
        
        # Создаем конфигурационный словарь
        config_dict = {
            "name": config.name,
            "provider": config.provider.value,
            "model_name": config.model_name,
            "model_path": config.model_path,
            "context_length": config.context_length,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "timeout": config.timeout,
            "extra_params": config.extra_params or {}
        }
        
        # Загружаем и тестируем модель
        try:
            # Создаем Vision модель
            vision_model = ModelFactory.create_vision_model(config_dict)
            model_load_time = time.time() - start_time
            
            # Если передано изображение, анализируем его
            analysis = None
            if request.image_data:
                try:
                    # Декодируем base64 изображение
                    image_bytes = base64.b64decode(request.image_data)
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    # Выполняем анализ
                    inference_start = time.time()
                    analysis = vision_model.analyze_image(image, request.prompt)
                    inference_time = time.time() - inference_start
                    
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")
            else:
                analysis = "Тест успешен! Модель загружена и готова к анализу изображений."
                inference_time = 0
            
            total_time = time.time() - start_time
            
            return VLMTestResponse(
                success=True,
                analysis=analysis,
                error=None,
                model_info=model_info,
                performance_metrics={
                    "model_load_time_seconds": model_load_time,
                    "inference_time_seconds": inference_time,
                    "total_time_seconds": total_time
                }
            )
            
        except Exception as e:
            error_time = time.time() - start_time
            logger.error(f"Error testing VLM model: {e}")
            
            return VLMTestResponse(
                success=False,
                analysis=None,
                error=str(e),
                model_info=model_info,
                performance_metrics={
                    "error_time_seconds": error_time
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in VLM test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/{config_id}/test/upload")
async def test_vlm_with_upload(
    config_id: int,
    file: UploadFile = File(...),
    prompt: str = Form("Проанализируй это изображение"),
    load_model: bool = Form(True),
    db: Session = Depends(get_session)
):
    """Протестировать VLM модель с загруженным изображением."""
    try:
        # Проверяем тип файла
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Читаем и конвертируем изображение
        image_bytes = await file.read()
        image_b64 = base64.b64encode(image_bytes).decode()
        
        # Используем существующий endpoint для тестирования
        request = VLMTestRequest(
            vlm_config_id=config_id,
            prompt=prompt,
            image_data=image_b64,
            load_model=load_model
        )
        
        return await test_local_vlm_model(config_id, request, db)
        
    except Exception as e:
        logger.error(f"Error testing VLM with upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/recommendations")
async def get_model_recommendations():
    """Получить рекомендации по выбору локальных VLM моделей."""
    try:
        # Получаем информацию о системе
        system_info = await get_system_resources()
        
        recommendations = []
        
        # Анализируем доступные ресурсы
        available_memory_gb = system_info.memory_available_gb
        gpu_memory_gb = 0
        
        if system_info.gpu_info:
            gpu_memory_gb = max(gpu["memory_total_mb"] for gpu in system_info.gpu_info) / 1024
        
        # Рекомендуем модели на основе ресурсов
        for provider, info in LOCAL_VLM_MODELS.items():
            for variant in info["variants"]:
                suitable = True
                reasons = []
                
                if variant["gpu_memory_gb"] > gpu_memory_gb:
                    suitable = False
                    reasons.append(f"Требует {variant['gpu_memory_gb']}GB GPU, доступно {gpu_memory_gb:.1f}GB")
                
                if variant["size_gb"] > system_info.disk_space_gb:
                    suitable = False
                    reasons.append(f"Требует {variant['size_gb']}GB места, доступно {system_info.disk_space_gb:.1f}GB")
                
                recommendations.append({
                    "provider": provider,
                    "variant": variant,
                    "suitable": suitable,
                    "reasons": reasons,
                    "performance_tier": (
                        "high" if variant["size_gb"] > 30 else
                        "medium" if variant["size_gb"] > 10 else
                        "lightweight"
                    )
                })
        
        # Сортируем по пригодности и производительности
        recommendations.sort(key=lambda x: (x["suitable"], x["variant"]["size_gb"]), reverse=True)
        
        return {
            "system_resources": {
                "memory_gb": available_memory_gb,
                "gpu_memory_gb": gpu_memory_gb,
                "disk_space_gb": system_info.disk_space_gb
            },
            "recommendations": recommendations,
            "best_choice": recommendations[0] if recommendations else None
        }
        
    except Exception as e:
        logger.error(f"Error getting model recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/installation/guide")
async def get_installation_guide():
    """Получить руководство по установке локальных VLM."""
    return {
        "title": "Руководство по установке локальных VLM моделей",
        "steps": [
            {
                "step": 1,
                "title": "Системные требования",
                "description": "Убедитесь, что система соответствует требованиям",
                "requirements": {
                    "python": "3.8+",
                    "cuda": "11.8+ (для GPU)",
                    "memory": "8GB+ RAM",
                    "gpu_memory": "8GB+ VRAM (рекомендуется)",
                    "disk_space": "50GB+ свободного места"
                }
            },
            {
                "step": 2,
                "title": "Установка зависимостей",
                "description": "Установите необходимые Python пакеты",
                "commands": [
                    "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118",
                    "pip install transformers accelerate",
                    "pip install pillow",
                    "pip install bitsandbytes  # для квантизации"
                ]
            },
            {
                "step": 3,
                "title": "Загрузка моделей",
                "description": "Загрузите модели через Hugging Face Hub",
                "examples": [
                    {
                        "model": "LLaVA 1.5 7B",
                        "command": "huggingface-cli download llava-hf/llava-1.5-7b-hf --local-dir /models/llava/llava-v1.5-7b"
                    },
                    {
                        "model": "MoonDream2",
                        "command": "huggingface-cli download vikhyatk/moondream2 --local-dir /models/moondream/moondream2"
                    }
                ]
            },
            {
                "step": 4,
                "title": "Конфигурация",
                "description": "Создайте конфигурацию через API",
                "api_example": {
                    "method": "POST",
                    "url": "/models/",
                    "body": {
                        "name": "LLaVA 1.5 7B Local",
                        "provider": "local_llava",
                        "model_name": "llava-v1.5-7b-hf",
                        "model_path": "/models/llava/llava-v1.5-7b",
                        "extra_params": {
                            "device": "cuda",
                            "dtype": "float16",
                            "load_in_4bit": True
                        }
                    }
                }
            },
            {
                "step": 5,
                "title": "Тестирование",
                "description": "Протестируйте модель",
                "test_command": "POST /models/{config_id}/test"
            }
        ],
        "troubleshooting": [
            {
                "problem": "CUDA out of memory",
                "solutions": [
                    "Используйте load_in_4bit: true для квантизации",
                    "Уменьшите max_tokens",
                    "Выберите модель меньшего размера"
                ]
            },
            {
                "problem": "Медленная загрузка модели",
                "solutions": [
                    "Убедитесь, что модель на SSD",
                    "Увеличьте timeout",
                    "Используйте dtype: float16"
                ]
            }
        ]
    }

@app.get("/health/local-vlm")
async def check_local_vlm_health():
    """Проверить состояние локальных VLM."""
    try:
        health_status = {
            "status": "healthy",
            "checks": []
        }
        
        # Проверяем системные ресурсы
        resources = await get_system_resources()
        
        # Проверка GPU
        if resources.gpu_info:
            health_status["checks"].append({
                "name": "GPU Available",
                "status": "pass",
                "details": f"{len(resources.gpu_info)} GPU(s) detected"
            })
        else:
            health_status["checks"].append({
                "name": "GPU Available",
                "status": "warn",
                "details": "No GPU detected, models will run on CPU (slower)"
            })
        
        # Проверка памяти
        if resources.memory_available_gb >= 8:
            health_status["checks"].append({
                "name": "Memory Available",
                "status": "pass",
                "details": f"{resources.memory_available_gb:.1f}GB available"
            })
        else:
            health_status["checks"].append({
                "name": "Memory Available",
                "status": "fail",
                "details": f"Only {resources.memory_available_gb:.1f}GB available, need 8GB+"
            })
            health_status["status"] = "unhealthy"
        
        # Проверка дискового пространства
        if resources.disk_space_gb >= 50:
            health_status["checks"].append({
                "name": "Disk Space",
                "status": "pass",
                "details": f"{resources.disk_space_gb:.1f}GB available"
            })
        else:
            health_status["checks"].append({
                "name": "Disk Space",
                "status": "warn",
                "details": f"Only {resources.disk_space_gb:.1f}GB available, need 50GB+ for models"
            })
        
        # Проверка зависимостей
        try:
            import torch
            health_status["checks"].append({
                "name": "PyTorch",
                "status": "pass",
                "details": f"Version {torch.__version__}"
            })
        except ImportError:
            health_status["checks"].append({
                "name": "PyTorch",
                "status": "fail",
                "details": "PyTorch not installed"
            })
            health_status["status"] = "unhealthy"
        
        try:
            import transformers
            health_status["checks"].append({
                "name": "Transformers",
                "status": "pass",
                "details": f"Version {transformers.__version__}"
            })
        except ImportError:
            health_status["checks"].append({
                "name": "Transformers",
                "status": "fail",
                "details": "Transformers not installed"
            })
            health_status["status"] = "unhealthy"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Local VLM health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "checks": []
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
