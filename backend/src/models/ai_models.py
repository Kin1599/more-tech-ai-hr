"""
Модели базы данных для настройки AI моделей интервью.
Позволяет настраивать LLM, STT, TTS модели для каждого интервью отдельно.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class ModelTypeEnum(enum.Enum):
    """Типы AI моделей."""
    LLM = "llm"          # Large Language Model (для чатбота)
    STT = "stt"          # Speech-to-Text
    TTS = "tts"          # Text-to-Speech
    AVATAR = "avatar"    # Virtual Avatar (для визуального представления)
    VISION = "vision"    # Vision Model (для анализа изображений и скриншотов)


class ModelProviderEnum(enum.Enum):
    """Провайдеры AI моделей."""
    # API провайдеры
    OPENAI = "openai"
    GROQ = "groq"
    ANTHROPIC = "anthropic"
    CARTESIA = "cartesia"
    HUGGINGFACE = "huggingface"
    REPLICATE = "replicate"
    COHERE = "cohere"
    
    # Локальные провайдеры
    LOCAL_Oollama = "local_oollama"
    LOCAL_WHISPER = "local_whisper"
    LOCAL_COQUI = "local_coqui"
    LOCAL_BARK = "local_bark"
    LOCAL_VLLM = "local_vllm"
    LOCAL_ollamaCPP = "local_ollamacpp"
    LOCAL_TRANSFORMERS = "local_transformers"
    LOCAL_ONNX = "local_onnx"
    LOCAL_TENSORRT = "local_tensorrt"
    
    # Avatar провайдеры
    SIMLI = "simli"
    
    # Vision провайдеры
    GOOGLE_GEMINI = "google_gemini"
    OPENAI_VISION = "openai_vision"
    ANTHROPIC_VISION = "anthropic_vision"
    AZURE_VISION = "azure_vision"
    
    # Локальные Vision провайдеры
    LOCAL_LLAVA = "local_llava"
    LOCAL_COGVLM = "local_cogvlm"
    LOCAL_BLIP2 = "local_blip2"
    LOCAL_INSTRUCTBLIP = "local_instructblip"
    LOCAL_MINIGPT4 = "local_minigpt4"
    LOCAL_QWEN_VL = "local_qwen_vl"
    LOCAL_INTERNVL = "local_internvl"
    LOCAL_MOONDREAM = "local_moondream"
    LOCAL_BAKLLAVA = "local_bakllava"
    
    # Кастомные и универсальные
    CUSTOM_ENDPOINT = "custom_endpoint"
    CUSTOM_LOCAL = "custom_local"
    OPENAI_COMPATIBLE = "openai_compatible"  # Для любых OpenAI-совместимых API


class AIModelConfiguration(Base):
    """
    Конфигурация AI модели.
    Определяет параметры для использования конкретной модели (LLM, STT, TTS).
    """
    __tablename__ = "ai_model_configurations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Основные параметры
    name = Column(String(100), nullable=False, index=True)  # Человекочитаемое название
    description = Column(Text, nullable=True)  # Описание модели
    model_type = Column(SQLEnum(ModelTypeEnum), nullable=False, index=True)
    provider = Column(SQLEnum(ModelProviderEnum), nullable=False, index=True)
    
    # Параметры модели
    model_name = Column(String(200), nullable=False)  # Название модели у провайдера
    endpoint_url = Column(String(500), nullable=True)  # URL для custom endpoints
    api_key_name = Column(String(100), nullable=True)  # Название переменной окружения с API ключом
    model_path = Column(String(500), nullable=True)  # Путь к локальному файлу модели
    engine_path = Column(String(500), nullable=True)  # Путь к engine файлу (для TensorRT)
    context_length = Column(Integer, nullable=True)  # Длина контекста для локальных моделей
    
    # Avatar-специфичные параметры
    face_id = Column(String(100), nullable=True)  # ID лица для Simli Avatar
    max_session_length = Column(Integer, nullable=True)  # Максимальная длительность сессии (сек)
    max_idle_time = Column(Integer, nullable=True)  # Максимальное время бездействия (сек)
    
    # Параметры генерации
    temperature = Column(Float, nullable=True, default=0.7)
    max_tokens = Column(Integer, nullable=True)
    timeout = Column(Integer, nullable=True, default=30)  # Таймаут в секундах
    
    # Дополнительные параметры (JSON как строка)
    extra_params = Column(Text, nullable=True)  # JSON строка с дополнительными параметрами
    
    # Метаданные
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)  # Модель по умолчанию для типа
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Связи
    interview_configs = relationship("InterviewModelConfiguration", back_populates="ai_model")


class InterviewModelConfiguration(Base):
    """
    Конфигурация моделей для конкретного интервью.
    Связывает вакансию с набором AI моделей для проведения интервью.
    """
    __tablename__ = "interview_model_configurations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Связь с вакансией
    vacancy_id = Column(Integer, ForeignKey("vacancies.id"), nullable=False, index=True)
    
    # Модели для интервью
    llm_model_id = Column(Integer, ForeignKey("ai_model_configurations.id"), nullable=True)
    stt_model_id = Column(Integer, ForeignKey("ai_model_configurations.id"), nullable=True)
    tts_model_id = Column(Integer, ForeignKey("ai_model_configurations.id"), nullable=True)
    avatar_model_id = Column(Integer, ForeignKey("ai_model_configurations.id"), nullable=True)
    vision_model_id = Column(Integer, ForeignKey("ai_model_configurations.id"), nullable=True)
    
    # Настройки интервью
    max_questions = Column(Integer, default=12)
    interview_timeout = Column(Integer, default=3600)  # Таймаут интервью в секундах
    
    # Дополнительные настройки
    use_voice_activity_detection = Column(Boolean, default=True)
    use_turn_detection = Column(Boolean, default=True)
    silence_threshold = Column(Float, default=0.5)
    
    # Метаданные
    name = Column(String(200), nullable=True)  # Название конфигурации
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Связи
    vacancy = relationship("Vacancy", back_populates="interview_model_config")
    llm_model = relationship("AIModelConfiguration", foreign_keys=[llm_model_id])
    stt_model = relationship("AIModelConfiguration", foreign_keys=[stt_model_id])
    tts_model = relationship("AIModelConfiguration", foreign_keys=[tts_model_id])
    avatar_model = relationship("AIModelConfiguration", foreign_keys=[avatar_model_id])
    vision_model = relationship("AIModelConfiguration", foreign_keys=[vision_model_id])


class ModelUsageLog(Base):
    """
    Лог использования моделей для аналитики и биллинга.
    """
    __tablename__ = "model_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Связи
    interview_config_id = Column(Integer, ForeignKey("interview_model_configurations.id"), nullable=False)
    ai_model_id = Column(Integer, ForeignKey("ai_model_configurations.id"), nullable=False)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id"), nullable=False)
    applicant_id = Column(Integer, ForeignKey("applicant_profiles.id"), nullable=False)
    
    # Метрики использования
    tokens_used = Column(Integer, nullable=True)  # Для LLM
    duration_seconds = Column(Float, nullable=True)  # Для STT/TTS
    request_count = Column(Integer, default=1)
    
    # Стоимость (если известна)
    cost_usd = Column(Float, nullable=True)
    
    # Метаданные
    session_id = Column(String(100), nullable=True)  # ID сессии VideoSDK
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    
    # Связи
    interview_config = relationship("InterviewModelConfiguration")
    ai_model = relationship("AIModelConfiguration")


# Предустановленные конфигурации моделей
DEFAULT_MODEL_CONFIGS = [
    # LLM модели
    {
        "name": "Groq qwen3-32b 8x7B",
        "description": "Быстрая и качественная модель для интервью",
        "model_type": ModelTypeEnum.LLM,
        "provider": ModelProviderEnum.GROQ,
        "model_name": "qwen3-32b",
        "api_key_name": "GROQ_API_KEY",
        "temperature": 0.7,
        "max_tokens": 4000,
        "is_default": True
    },
    {
        "name": "OpenAI GPT-4",
        "description": "Премиум модель для сложных интервью",
        "model_type": ModelTypeEnum.LLM,
        "provider": ModelProviderEnum.OPENAI,
        "model_name": "gpt-4",
        "api_key_name": "OPENAI_API_KEY",
        "temperature": 0.7,
        "max_tokens": 3000
    },
    {
        "name": "Local Oollama ollama3",
        "description": "Локальная модель для конфиденциальных интервью",
        "model_type": ModelTypeEnum.LLM,
        "provider": ModelProviderEnum.LOCAL_Oollama,
        "model_name": "ollama3:8b",
        "endpoint_url": "http://localhost:11434",
        "temperature": 0.7
    },
    
    # STT модели
    {
        "name": "Groq Whisper Large",
        "description": "Быстрое распознавание речи через API",
        "model_type": ModelTypeEnum.STT,
        "provider": ModelProviderEnum.GROQ,
        "model_name": "whisper-large-v3",
        "api_key_name": "GROQ_API_KEY",
        "is_default": True
    },
    {
        "name": "OpenAI Whisper",
        "description": "Высококачественное распознавание речи",
        "model_type": ModelTypeEnum.STT,
        "provider": ModelProviderEnum.OPENAI,
        "model_name": "whisper-1",
        "api_key_name": "OPENAI_API_KEY"
    },
    {
        "name": "Local Whisper",
        "description": "Локальное распознавание речи",
        "model_type": ModelTypeEnum.STT,
        "provider": ModelProviderEnum.LOCAL_WHISPER,
        "model_name": "openai/whisper-large-v3",
        "endpoint_url": "http://localhost:8000"
    },
    
    # TTS модели
    {
        "name": "Cartesia Sonic",
        "description": "Быстрый и качественный синтез речи",
        "model_type": ModelTypeEnum.TTS,
        "provider": ModelProviderEnum.CARTESIA,
        "model_name": "sonic-english",
        "api_key_name": "CARTESIA_API_KEY",
        "is_default": True
    },
    {
        "name": "OpenAI TTS",
        "description": "Высококачественный синтез речи",
        "model_type": ModelTypeEnum.TTS,
        "provider": ModelProviderEnum.OPENAI,
        "model_name": "tts-1",
        "api_key_name": "OPENAI_API_KEY"
    },
    {
        "name": "Local Coqui TTS",
        "description": "Локальный синтез речи",
        "model_type": ModelTypeEnum.TTS,
        "provider": ModelProviderEnum.LOCAL_COQUI,
        "model_name": "tts_models/en/ljspeech/tacotron2-DDC",
        "endpoint_url": "http://localhost:5002"
    },
    
    # Avatar модели
    {
        "name": "Simli Default Avatar",
        "description": "Стандартный Simli Avatar для интервью",
        "model_type": ModelTypeEnum.AVATAR,
        "provider": ModelProviderEnum.SIMLI,
        "model_name": "default-face",
        "api_key_name": "SIMLI_API_KEY",
        "face_id": "0c2b8b04-5274-41f1-a21c-d5c98322efa9",  # Default face ID
        "max_session_length": 1800,  # 30 минут
        "max_idle_time": 300,  # 5 минут
        "timeout": 30,
        "is_active": True
    },
    
    # Vision модели
    {
        "name": "Gemini 1.5 Flash Vision",
        "description": "Быстрая мультимодальная модель Google для анализа экрана",
        "model_type": ModelTypeEnum.VISION,
        "provider": ModelProviderEnum.GOOGLE_GEMINI,
        "model_name": "gemini-1.5-flash",
        "api_key_name": "GEMINI_API_KEY",
        "timeout": 30,
        "extra_params": {
            "max_output_tokens": 2048,
            "temperature": 0.4,
            "safety_settings": "block_none"
        },
        "is_active": True,
        "is_default": True
    },
    {
        "name": "Gemini 1.5 Pro Vision",
        "description": "Продвинутая мультимодальная модель Google для сложного анализа",
        "model_type": ModelTypeEnum.VISION,
        "provider": ModelProviderEnum.GOOGLE_GEMINI,
        "model_name": "gemini-1.5-pro",
        "api_key_name": "GEMINI_API_KEY",
        "timeout": 45,
        "extra_params": {
            "max_output_tokens": 4096,
            "temperature": 0.3
        },
        "is_active": True
    },
    {
        "name": "OpenAI GPT-4 Vision",
        "description": "GPT-4 с возможностями анализа изображений",
        "model_type": ModelTypeEnum.VISION,
        "provider": ModelProviderEnum.OPENAI_VISION,
        "model_name": "gpt-4-vision-preview",
        "api_key_name": "OPENAI_API_KEY",
        "max_tokens": 4096,
        "timeout": 30,
        "extra_params": {
            "max_tokens": 4096,
            "detail": "high"
        },
        "is_active": True
    },
    
    # Локальные Vision модели
    {
        "name": "LLaVA 1.6 34B",
        "description": "Мощная локальная Vision модель для детального анализа",
        "model_type": ModelTypeEnum.VISION,
        "provider": ModelProviderEnum.LOCAL_LLAVA,
        "model_name": "llava-v1.6-34b-hf",
        "model_path": "/models/llava/llava-v1.6-34b",
        "context_length": 4096,
        "temperature": 0.3,
        "max_tokens": 2048,
        "timeout": 60,
        "extra_params": {
            "device": "cuda",
            "dtype": "float16",
            "max_new_tokens": 2048,
            "do_sample": True,
            "top_p": 0.9
        },
        "is_active": True
    },
    {
        "name": "LLaVA 1.5 7B",
        "description": "Компактная локальная Vision модель для быстрого анализа",
        "model_type": ModelTypeEnum.VISION,
        "provider": ModelProviderEnum.LOCAL_LLAVA,
        "model_name": "llava-v1.5-7b-hf",
        "model_path": "/models/llava/llava-v1.5-7b",
        "context_length": 2048,
        "temperature": 0.4,
        "max_tokens": 1024,
        "timeout": 30,
        "extra_params": {
            "device": "cuda",
            "dtype": "float16",
            "load_in_4bit": True
        },
        "is_active": True,
        "is_default": True
    },
    {
        "name": "CogVLM Chat",
        "description": "Локальная Vision модель с фокусом на диалог",
        "model_type": ModelTypeEnum.VISION,
        "provider": ModelProviderEnum.LOCAL_COGVLM,
        "model_name": "cogvlm-chat-hf",
        "model_path": "/models/cogvlm/cogvlm-chat",
        "context_length": 2048,
        "temperature": 0.3,
        "max_tokens": 1024,
        "timeout": 45,
        "extra_params": {
            "device": "cuda",
            "dtype": "bfloat16"
        },
        "is_active": True
    },
    {
        "name": "Qwen-VL Chat",
        "description": "Многоязычная локальная Vision модель",
        "model_type": ModelTypeEnum.VISION,
        "provider": ModelProviderEnum.LOCAL_QWEN_VL,
        "model_name": "Qwen-VL-Chat",
        "model_path": "/models/qwen/Qwen-VL-Chat",
        "context_length": 8192,
        "temperature": 0.4,
        "max_tokens": 2048,
        "timeout": 45,
        "extra_params": {
            "device": "cuda",
            "dtype": "float16",
            "trust_remote_code": True
        },
        "is_active": True
    },
    {
        "name": "MoonDream2",
        "description": "Легковесная локальная Vision модель",
        "model_type": ModelTypeEnum.VISION,
        "provider": ModelProviderEnum.LOCAL_MOONDREAM,
        "model_name": "vikhyatk/moondream2",
        "model_path": "/models/moondream/moondream2",
        "context_length": 2048,
        "temperature": 0.4,
        "max_tokens": 1024,
        "timeout": 20,
        "extra_params": {
            "device": "cuda",
            "dtype": "float16",
            "revision": "2024-04-02"
        },
        "is_active": True
    },
    {
        "name": "InternVL Chat V1.5",
        "description": "Продвинутая локальная Vision модель",
        "model_type": ModelTypeEnum.VISION,
        "provider": ModelProviderEnum.LOCAL_INTERNVL,
        "model_name": "InternVL-Chat-V1-5",
        "model_path": "/models/internvl/InternVL-Chat-V1-5",
        "context_length": 4096,
        "temperature": 0.3,
        "max_tokens": 2048,
        "timeout": 50,
        "extra_params": {
            "device": "cuda",
            "dtype": "bfloat16",
            "num_gpus": 1
        },
        "is_active": True
    },
    
    # Custom Endpoint VLM модели
    {
        "name": "OpenAI Compatible VLM",
        "description": "Любой OpenAI-совместимый VLM API endpoint",
        "model_type": ModelTypeEnum.VISION,
        "provider": ModelProviderEnum.CUSTOM_ENDPOINT,
        "model_name": "gpt-4-vision-preview",
        "api_key_name": "CUSTOM_VLM_API_KEY",
        "endpoint_url": "https://api.your-vlm-provider.com",
        "temperature": 0.7,
        "max_tokens": 4096,
        "timeout": 30,
        "extra_params": {
            "request_format": "openai",
            "auth_type": "bearer",
            "detail": "high"
        },
        "is_active": True
    },
    {
        "name": "Anthropic Compatible VLM",
        "description": "Anthropic-совместимый VLM API endpoint",
        "model_type": ModelTypeEnum.VISION,
        "provider": ModelProviderEnum.CUSTOM_ENDPOINT,
        "model_name": "claude-3-sonnet-20240229",
        "api_key_name": "CUSTOM_ANTHROPIC_KEY",
        "endpoint_url": "https://api.your-anthropic-compatible.com",
        "temperature": 0.7,
        "max_tokens": 4096,
        "timeout": 30,
        "extra_params": {
            "request_format": "anthropic",
            "auth_type": "anthropic"
        },
        "is_active": True
    },
    {
        "name": "Oollama Vision API",
        "description": "Oollama с Vision моделями через API",
        "model_type": ModelTypeEnum.VISION,
        "provider": ModelProviderEnum.CUSTOM_ENDPOINT,
        "model_name": "llava:13b",
        "endpoint_url": "http://localhost:11434",
        "temperature": 0.4,
        "max_tokens": 2048,
        "timeout": 60,
        "extra_params": {
            "request_format": "custom",
            "auth_type": "none",
            "endpoint_path": "/api/generate",
            "custom_params": {
                "stream": False,
                "format": "json"
            },
            "response_field": "response"
        },
        "is_active": True
    },
    {
        "name": "vLLM Vision Server",
        "description": "vLLM сервер с Vision моделями",
        "model_type": ModelTypeEnum.VISION,
        "provider": ModelProviderEnum.CUSTOM_ENDPOINT,
        "model_name": "llava-hf/llava-1.5-7b-hf",
        "endpoint_url": "http://localhost:8000",
        "temperature": 0.4,
        "max_tokens": 2048,
        "timeout": 45,
        "extra_params": {
            "request_format": "openai",
            "auth_type": "none"
        },
        "is_active": True
    },
    {
        "name": "Custom VLM API",
        "description": "Полностью кастомный VLM API endpoint",
        "model_type": ModelTypeEnum.VISION,
        "provider": ModelProviderEnum.CUSTOM_ENDPOINT,
        "model_name": "custom-vision-model",
        "api_key_name": "CUSTOM_VLM_KEY",
        "endpoint_url": "https://your-custom-vlm-api.com",
        "temperature": 0.5,
        "max_tokens": 2048,
        "timeout": 30,
        "extra_params": {
            "request_format": "custom",
            "auth_type": "custom_header",
            "auth_header": "X-Custom-API-Key",
            "endpoint_path": "/vision/analyze",
            "custom_params": {
                "return_confidence": True,
                "language": "ru"
            },
            "response_field": "analysis.text",
            "headers": {
                "X-Client-Version": "1.0",
                "Accept": "application/json"
            }
        },
        "is_active": True
    }
]
