"""
Сервис для работы с настройками AI моделей интервью.
Управляет конфигурацией и загрузкой моделей для каждого интервью.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

# Импорты моделей БД
try:
    from ...models.ai_models import (
        AIModelConfiguration, 
        InterviewModelConfiguration, 
        ModelUsageLog,
        ModelTypeEnum, 
        ModelProviderEnum,
        DEFAULT_MODEL_CONFIGS
    )
    from ...models.models import Vacancy
    from ...core.database import get_session
except ImportError as e:
    logging.warning(f"Cannot import AI model classes: {e}")
    # Fallback заглушки
    AIModelConfiguration = None
    InterviewModelConfiguration = None
    ModelUsageLog = None
    ModelTypeEnum = None
    ModelProviderEnum = None
    DEFAULT_MODEL_CONFIGS = []
    Vacancy = None
    get_session = None

logger = logging.getLogger(__name__)


class ModelConfigurationService:
    """Сервис для управления конфигурацией AI моделей."""
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Инициализация сервиса.
        
        Args:
            db_session: Сессия базы данных. Если не передана, будет создана новая.
        """
        self.db_session = db_session
        self._external_session = db_session is not None
    
    def _get_session(self) -> Session:
        """Получить сессию базы данных."""
        if self.db_session:
            return self.db_session
        elif get_session:
            return next(get_session())
        else:
            raise RuntimeError("Database session not available")
    
    def get_interview_models_config(self, vacancy_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить конфигурацию моделей для интервью по вакансии.
        
        Args:
            vacancy_id: ID вакансии
            
        Returns:
            Словарь с конфигурацией моделей или None
        """
        if not InterviewModelConfiguration:
            logger.warning("InterviewModelConfiguration model not available")
            return None
            
        try:
            db = self._get_session()
            
            # Загружаем конфигурацию с моделями
            config = (
                db.query(InterviewModelConfiguration)
                .options(
                    joinedload(InterviewModelConfiguration.llm_model),
                    joinedload(InterviewModelConfiguration.stt_model),
                    joinedload(InterviewModelConfiguration.tts_model),
                    joinedload(InterviewModelConfiguration.avatar_model),
                    joinedload(InterviewModelConfiguration.vision_model)
                )
                .filter_by(vacancy_id=vacancy_id, is_active=True)
                .first()
            )
            
            if not config:
                logger.info(f"No model configuration found for vacancy {vacancy_id}, using defaults")
                return self._get_default_models_config()
            
            return {
                "config_id": config.id,
                "vacancy_id": config.vacancy_id,
                "max_questions": config.max_questions,
                "interview_timeout": config.interview_timeout,
                "use_voice_activity_detection": config.use_voice_activity_detection,
                "use_turn_detection": config.use_turn_detection,
                "silence_threshold": config.silence_threshold,
                "llm_model": self._model_to_dict(config.llm_model) if config.llm_model else None,
                "stt_model": self._model_to_dict(config.stt_model) if config.stt_model else None,
                "tts_model": self._model_to_dict(config.tts_model) if config.tts_model else None,
                "avatar_model": self._model_to_dict(config.avatar_model) if config.avatar_model else None,
                "vision_model": self._model_to_dict(config.vision_model) if config.vision_model else None,
                "name": config.name,
                "description": config.description
            }
            
        except Exception as e:
            logger.error(f"Error fetching model configuration for vacancy {vacancy_id}: {e}")
            return self._get_default_models_config()
    
    def _get_default_models_config(self) -> Dict[str, Any]:
        """
        Получить конфигурацию моделей по умолчанию.
        
        Returns:
            Словарь с моделями по умолчанию
        """
        try:
            db = self._get_session()
            
            # Получаем модели по умолчанию для каждого типа
            llm_model = (
                db.query(AIModelConfiguration)
                .filter_by(model_type=ModelTypeEnum.LLM, is_default=True, is_active=True)
                .first()
            )
            
            stt_model = (
                db.query(AIModelConfiguration)
                .filter_by(model_type=ModelTypeEnum.STT, is_default=True, is_active=True)
                .first()
            )
            
            tts_model = (
                db.query(AIModelConfiguration)
                .filter_by(model_type=ModelTypeEnum.TTS, is_default=True, is_active=True)
                .first()
            )
            
            avatar_model = (
                db.query(AIModelConfiguration)
                .filter_by(model_type=ModelTypeEnum.AVATAR, is_default=True, is_active=True)
                .first()
            )
            
            vision_model = (
                db.query(AIModelConfiguration)
                .filter_by(model_type=ModelTypeEnum.VISION, is_default=True, is_active=True)
                .first()
            )
            
            return {
                "config_id": None,
                "vacancy_id": None,
                "max_questions": 12,
                "interview_timeout": 3600,
                "use_voice_activity_detection": True,
                "use_turn_detection": True,
                "silence_threshold": 0.5,
                "llm_model": self._model_to_dict(llm_model) if llm_model else self._get_fallback_llm(),
                "stt_model": self._model_to_dict(stt_model) if stt_model else self._get_fallback_stt(),
                "tts_model": self._model_to_dict(tts_model) if tts_model else self._get_fallback_tts(),
                "avatar_model": self._model_to_dict(avatar_model) if avatar_model else None,
                "vision_model": self._model_to_dict(vision_model) if vision_model else None,
                "name": "Default Configuration",
                "description": "Default models configuration"
            }
            
        except Exception as e:
            logger.error(f"Error getting default models: {e}")
            return self._get_fallback_config()
    
    def _model_to_dict(self, model: Any) -> Dict[str, Any]:
        """
        Конвертировать модель в словарь.
        
        Args:
            model: Объект AIModelConfiguration
            
        Returns:
            Словарь с параметрами модели
        """
        if not model:
            return {}
            
        extra_params = {}
        if model.extra_params:
            try:
                extra_params = json.loads(model.extra_params)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in extra_params for model {model.id}")
        
        return {
            "id": model.id,
            "name": model.name,
            "description": model.description,
            "model_type": model.model_type.value if model.model_type else None,
            "provider": model.provider.value if model.provider else None,
            "model_name": model.model_name,
            "endpoint_url": model.endpoint_url,
            "api_key_name": model.api_key_name,
            "model_path": model.model_path,
            "engine_path": model.engine_path,
            "context_length": model.context_length,
            "face_id": model.face_id,
            "max_session_length": model.max_session_length,
            "max_idle_time": model.max_idle_time,
            "temperature": model.temperature,
            "max_tokens": model.max_tokens,
            "timeout": model.timeout,
            "extra_params": extra_params
        }
    
    def _get_fallback_llm(self) -> Dict[str, Any]:
        """Fallback конфигурация для LLM."""
        return {
            "name": "Groq qwen3-32b (Fallback)",
            "model_type": "llm",
            "provider": "groq",
            "model_name": "qwen3-32b",
            "api_key_name": "GROQ_API_KEY",
            "temperature": 0.7,
            "max_tokens": 4000,
            "timeout": 30
        }
    
    def _get_fallback_stt(self) -> Dict[str, Any]:
        """Fallback конфигурация для STT."""
        return {
            "name": "Groq Whisper (Fallback)",
            "model_type": "stt",
            "provider": "groq",
            "model_name": "whisper-large-v3",
            "api_key_name": "GROQ_API_KEY",
            "timeout": 30
        }
    
    def _get_fallback_tts(self) -> Dict[str, Any]:
        """Fallback конфигурация для TTS."""
        return {
            "name": "Cartesia Sonic (Fallback)",
            "model_type": "tts",
            "provider": "cartesia",
            "model_name": "sonic-english",
            "api_key_name": "CARTESIA_API_KEY",
            "timeout": 30
        }
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Полная fallback конфигурация."""
        return {
            "config_id": None,
            "vacancy_id": None,
            "max_questions": 12,
            "interview_timeout": 3600,
            "use_voice_activity_detection": True,
            "use_turn_detection": True,
            "silence_threshold": 0.5,
            "llm_model": self._get_fallback_llm(),
            "stt_model": self._get_fallback_stt(),
            "tts_model": self._get_fallback_tts(),
            "avatar_model": None,
            "vision_model": None,
            "name": "Fallback Configuration",
            "description": "Emergency fallback configuration"
        }
    
    def create_interview_model_config(
        self,
        vacancy_id: int,
        llm_model_id: Optional[int] = None,
        stt_model_id: Optional[int] = None,
        tts_model_id: Optional[int] = None,
        avatar_model_id: Optional[int] = None,
        vision_model_id: Optional[int] = None,
        **kwargs
    ) -> Optional[int]:
        """
        Создать конфигурацию моделей для интервью.
        
        Args:
            vacancy_id: ID вакансии
            llm_model_id: ID модели LLM
            stt_model_id: ID модели STT
            tts_model_id: ID модели TTS
            avatar_model_id: ID модели Avatar
            vision_model_id: ID модели Vision
            **kwargs: Дополнительные параметры
            
        Returns:
            ID созданной конфигурации или None
        """
        if not InterviewModelConfiguration:
            logger.warning("Cannot create model configuration - model not available")
            return None
            
        try:
            db = self._get_session()
            
            # Проверяем, что вакансия существует
            vacancy = db.query(Vacancy).get(vacancy_id)
            if not vacancy:
                raise ValueError(f"Vacancy {vacancy_id} not found")
            
            # Создаем конфигурацию
            config = InterviewModelConfiguration(
                vacancy_id=vacancy_id,
                llm_model_id=llm_model_id,
                stt_model_id=stt_model_id,
                tts_model_id=tts_model_id,
                avatar_model_id=avatar_model_id,
                vision_model_id=vision_model_id,
                max_questions=kwargs.get('max_questions', 12),
                interview_timeout=kwargs.get('interview_timeout', 3600),
                use_voice_activity_detection=kwargs.get('use_voice_activity_detection', True),
                use_turn_detection=kwargs.get('use_turn_detection', True),
                silence_threshold=kwargs.get('silence_threshold', 0.5),
                name=kwargs.get('name'),
                description=kwargs.get('description')
            )
            
            db.add(config)
            db.commit()
            db.refresh(config)
            
            logger.info(f"Created model configuration {config.id} for vacancy {vacancy_id}")
            return config.id
            
        except Exception as e:
            logger.error(f"Error creating model configuration: {e}")
            return None
    
    def log_model_usage(
        self,
        vacancy_id: int,
        applicant_id: int,
        ai_model_id: int,
        tokens_used: Optional[int] = None,
        duration_seconds: Optional[float] = None,
        session_id: Optional[str] = None
    ):
        """
        Логировать использование модели.
        
        Args:
            vacancy_id: ID вакансии
            applicant_id: ID кандидата
            ai_model_id: ID использованной модели
            tokens_used: Количество использованных токенов
            duration_seconds: Длительность использования в секундах
            session_id: ID сессии VideoSDK
        """
        if not ModelUsageLog:
            logger.warning("Cannot log model usage - model not available")
            return
            
        try:
            db = self._get_session()
            
            # Получаем конфигурацию интервью
            interview_config = (
                db.query(InterviewModelConfiguration)
                .filter_by(vacancy_id=vacancy_id, is_active=True)
                .first()
            )
            
            log_entry = ModelUsageLog(
                interview_config_id=interview_config.id if interview_config else None,
                ai_model_id=ai_model_id,
                vacancy_id=vacancy_id,
                applicant_id=applicant_id,
                tokens_used=tokens_used,
                duration_seconds=duration_seconds,
                session_id=session_id
            )
            
            db.add(log_entry)
            db.commit()
            
            logger.debug(f"Logged model usage for vacancy {vacancy_id}, applicant {applicant_id}")
            
        except Exception as e:
            logger.error(f"Error logging model usage: {e}")
    
    def get_available_models(self, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Получить список доступных моделей.
        
        Args:
            model_type: Тип модели (llm, stt, tts) или None для всех
            
        Returns:
            Список доступных моделей
        """
        if not AIModelConfiguration:
            logger.warning("AIModelConfiguration model not available")
            return []
            
        try:
            db = self._get_session()
            
            query = db.query(AIModelConfiguration).filter_by(is_active=True)
            
            if model_type:
                query = query.filter_by(model_type=ModelTypeEnum(model_type))
            
            models = query.order_by(AIModelConfiguration.name).all()
            
            return [self._model_to_dict(model) for model in models]
            
        except Exception as e:
            logger.error(f"Error fetching available models: {e}")
            return []
    
    def initialize_default_models(self):
        """
        Инициализировать модели по умолчанию в базе данных.
        Вызывается при первом запуске приложения.
        """
        if not AIModelConfiguration or not DEFAULT_MODEL_CONFIGS:
            logger.warning("Cannot initialize default models - models not available")
            return
            
        try:
            db = self._get_session()
            
            # Проверяем, есть ли уже модели в БД
            existing_count = db.query(AIModelConfiguration).count()
            if existing_count > 0:
                logger.info(f"Models already exist in database ({existing_count} models)")
                return
            
            # Создаем модели по умолчанию
            for config in DEFAULT_MODEL_CONFIGS:
                model = AIModelConfiguration(
                    name=config["name"],
                    description=config["description"],
                    model_type=config["model_type"],
                    provider=config["provider"],
                    model_name=config["model_name"],
                    endpoint_url=config.get("endpoint_url"),
                    api_key_name=config.get("api_key_name"),
                    temperature=config.get("temperature"),
                    max_tokens=config.get("max_tokens"),
                    timeout=config.get("timeout", 30),
                    is_default=config.get("is_default", False)
                )
                db.add(model)
            
            db.commit()
            logger.info(f"Initialized {len(DEFAULT_MODEL_CONFIGS)} default models")
            
        except Exception as e:
            logger.error(f"Error initializing default models: {e}")
    
    def close(self):
        """Закрыть сессию базы данных, если она была создана внутри сервиса."""
        if self.db_session and not self._external_session:
            self.db_session.close()


def get_interview_models_config(vacancy_id: int, db_session: Optional[Session] = None) -> Dict[str, Any]:
    """
    Удобная функция для получения конфигурации моделей интервью.
    
    Args:
        vacancy_id: ID вакансии
        db_session: Опциональная сессия БД
        
    Returns:
        Конфигурация моделей
    """
    service = ModelConfigurationService(db_session)
    try:
        config = service.get_interview_models_config(vacancy_id)
        return config if config else service._get_fallback_config()
    finally:
        service.close()


def log_model_usage_simple(
    vacancy_id: int,
    applicant_id: int,
    model_config: Dict[str, Any],
    usage_data: Dict[str, Any],
    db_session: Optional[Session] = None
):
    """
    Упрощенная функция для логирования использования модели.
    
    Args:
        vacancy_id: ID вакансии
        applicant_id: ID кандидата
        model_config: Конфигурация модели
        usage_data: Данные об использовании
        db_session: Опциональная сессия БД
    """
    service = ModelConfigurationService(db_session)
    try:
        service.log_model_usage(
            vacancy_id=vacancy_id,
            applicant_id=applicant_id,
            ai_model_id=model_config.get("id"),
            tokens_used=usage_data.get("tokens_used"),
            duration_seconds=usage_data.get("duration_seconds"),
            session_id=usage_data.get("session_id")
        )
    finally:
        service.close()
