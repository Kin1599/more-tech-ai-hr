"""
Фабрика для создания AI моделей разных типов и провайдеров.
Поддерживает как API модели (OpenAI, Groq, Anthropic), так и локальные модели.
"""

import os
import logging
from typing import Any, Dict, Optional, Union
from abc import ABC, abstractmethod

# Импорты для различных моделей
try:
    # LLM модели
    from langchain_groq import ChatGroq
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    
    # VideoSDK компоненты
    from videosdk.plugins.openai import OpenAITTS
    from videosdk.plugins.cartesia import CartesiaTTS, CartesiaSTT
    
    # Локальные компоненты из проекта
    from groq_stt import GroqSTT
    from groq_llm import GroqLLM
    from groq_tts_fixed import GroqTTSFixed
    from cartesia_safe_wrapper import SafeCartesiaTTSWrapper, SafeCartesiaSTTWrapper
    
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Some model dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False

logger = logging.getLogger(__name__)


class ModelCreationError(Exception):
    """Ошибка создания модели."""
    pass


class BaseModelAdapter(ABC):
    """Базовый класс для адаптеров моделей."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get("model_name")
        self.provider = config.get("provider")
        self.api_key = self._get_api_key()
    
    def _get_api_key(self) -> Optional[str]:
        """Получить API ключ из переменных окружения."""
        api_key_name = self.config.get("api_key_name")
        if api_key_name:
            return os.getenv(api_key_name)
        return None
    
    @abstractmethod
    def create_model(self) -> Any:
        """Создать модель."""
        pass


class LLMModelAdapter(BaseModelAdapter):
    """Адаптер для LLM моделей."""
    
    def create_model(self) -> Any:
        """Создать LLM модель."""
        provider = self.config.get("provider")
        
        # API провайдеры
        if provider == "groq":
            return self._create_groq_llm()
        elif provider == "openai":
            return self._create_openai_llm()
        elif provider == "anthropic":
            return self._create_anthropic_llm()
        elif provider == "huggingface":
            return self._create_huggingface_llm()
        elif provider == "replicate":
            return self._create_replicate_llm()
        elif provider == "cohere":
            return self._create_cohere_llm()
        
        # Локальные провайдеры
        elif provider == "local_oollama":
            return self._create_oollama_llm()
        elif provider == "local_vllm":
            return self._create_vllm_llm()
        elif provider == "local_ollamacpp":
            return self._create_ollamacpp_llm()
        elif provider == "local_transformers":
            return self._create_transformers_llm()
        elif provider == "local_onnx":
            return self._create_onnx_llm()
        elif provider == "local_tensorrt":
            return self._create_tensorrt_llm()
        
        # Кастомные и универсальные
        elif provider == "custom_endpoint":
            return self._create_custom_endpoint_llm()
        elif provider == "custom_local":
            return self._create_custom_local_llm()
        elif provider == "openai_compatible":
            return self._create_openai_compatible_llm()
        
        else:
            raise ModelCreationError(f"Unsupported LLM provider: {provider}")
    
    def _create_groq_llm(self) -> Any:
        """Создать Groq LLM."""
        if not DEPENDENCIES_AVAILABLE:
            raise ModelCreationError("Groq dependencies not available")
        
        if not self.api_key:
            raise ModelCreationError("GROQ_API_KEY not found in environment")
        
        return ChatGroq(
            groq_api_key=self.api_key,
            model_name=self.model_name,
            temperature=self.config.get("temperature", 0.7),
            max_tokens=self.config.get("max_tokens"),
            timeout=self.config.get("timeout", 30)
        )
    
    def _create_openai_llm(self) -> Any:
        """Создать OpenAI LLM."""
        if not DEPENDENCIES_AVAILABLE:
            raise ModelCreationError("OpenAI dependencies not available")
        
        if not self.api_key:
            raise ModelCreationError("OPENAI_API_KEY not found in environment")
        
        return ChatOpenAI(
            openai_api_key=self.api_key,
            model_name=self.model_name,
            temperature=self.config.get("temperature", 0.7),
            max_tokens=self.config.get("max_tokens"),
            timeout=self.config.get("timeout", 30)
        )
    
    def _create_anthropic_llm(self) -> Any:
        """Создать Anthropic LLM."""
        if not DEPENDENCIES_AVAILABLE:
            raise ModelCreationError("Anthropic dependencies not available")
        
        if not self.api_key:
            raise ModelCreationError("ANTHROPIC_API_KEY not found in environment")
        
        return ChatAnthropic(
            anthropic_api_key=self.api_key,
            model=self.model_name,
            temperature=self.config.get("temperature", 0.7),
            max_tokens=self.config.get("max_tokens"),
            timeout=self.config.get("timeout", 30)
        )
    
    def _create_oollama_llm(self) -> Any:
        """Создать локальную Oollama LLM."""
        try:
            from langchain_community.llms import Oollama
            
            endpoint_url = self.config.get("endpoint_url", "http://localhost:11434")
            
            return Oollama(
                base_url=endpoint_url,
                model=self.model_name,
                temperature=self.config.get("temperature", 0.7),
                timeout=self.config.get("timeout", 60)
            )
        except ImportError:
            raise ModelCreationError("Oollama dependencies not available")
    
    def _create_custom_endpoint_llm(self) -> Any:
        """Создать LLM через кастомный endpoint."""
        try:
            from langchain_openai import ChatOpenAI
            
            endpoint_url = self.config.get("endpoint_url")
            if not endpoint_url:
                raise ModelCreationError("endpoint_url required for custom endpoint")
            
            return ChatOpenAI(
                openai_api_base=endpoint_url,
                openai_api_key=self.api_key or "dummy-key",
                model_name=self.model_name,
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens"),
                timeout=self.config.get("timeout", 30)
            )
        except ImportError:
            raise ModelCreationError("Custom endpoint dependencies not available")
    
    def _create_huggingface_llm(self) -> Any:
        """Создать HuggingFace LLM."""
        try:
            from langchain_huggingface import HuggingFaceEndpoint
            
            if not self.api_key:
                raise ModelCreationError("HUGGINGFACE_API_TOKEN not found in environment")
            
            return HuggingFaceEndpoint(
                repo_id=self.model_name,
                huggingfacehub_api_token=self.api_key,
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens"),
                timeout=self.config.get("timeout", 30)
            )
        except ImportError:
            raise ModelCreationError("HuggingFace dependencies not available")
    
    def _create_replicate_llm(self) -> Any:
        """Создать Replicate LLM."""
        try:
            from langchain_community.llms import Replicate
            
            if not self.api_key:
                raise ModelCreationError("REPLICATE_API_TOKEN not found in environment")
            
            return Replicate(
                model=self.model_name,
                replicate_api_token=self.api_key,
                model_kwargs={
                    "temperature": self.config.get("temperature", 0.7),
                    "max_tokens": self.config.get("max_tokens"),
                }
            )
        except ImportError:
            raise ModelCreationError("Replicate dependencies not available")
    
    def _create_cohere_llm(self) -> Any:
        """Создать Cohere LLM."""
        try:
            from langchain_cohere import ChatCohere
            
            if not self.api_key:
                raise ModelCreationError("COHERE_API_KEY not found in environment")
            
            return ChatCohere(
                cohere_api_key=self.api_key,
                model=self.model_name,
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens"),
                timeout=self.config.get("timeout", 30)
            )
        except ImportError:
            raise ModelCreationError("Cohere dependencies not available")
    
    def _create_vllm_llm(self) -> Any:
        """Создать vLLM локальную модель."""
        try:
            from langchain_community.llms import VLLM
            
            endpoint_url = self.config.get("endpoint_url", "http://localhost:8000")
            
            return VLLM(
                openai_api_key="EMPTY",
                openai_api_base=endpoint_url,
                model_name=self.model_name,
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens"),
                timeout=self.config.get("timeout", 60)
            )
        except ImportError:
            raise ModelCreationError("vLLM dependencies not available")
    
    def _create_ollamacpp_llm(self) -> Any:
        """Создать ollama.cpp локальную модель."""
        try:
            from langchain_community.llms import ollamaCpp
            
            model_path = self.config.get("model_path") or self.model_name
            if not model_path:
                raise ModelCreationError("model_path required for ollama.cpp")
            
            return ollamaCpp(
                model_path=model_path,
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens", 512),
                n_ctx=self.config.get("context_length", 2048),
                verbose=False
            )
        except ImportError:
            raise ModelCreationError("ollama.cpp dependencies not available")
    
    def _create_transformers_llm(self) -> Any:
        """Создать HuggingFace Transformers локальную модель."""
        try:
            from langchain_community.llms import HuggingFacePipeline
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            
            # Загружаем модель и токенизатор
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForCausalLM.from_pretrained(self.model_name)
            
            # Создаем pipeline
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                temperature=self.config.get("temperature", 0.7),
                max_new_tokens=self.config.get("max_tokens", 512),
                device_map="auto"
            )
            
            return HuggingFacePipeline(pipeline=pipe)
        except ImportError:
            raise ModelCreationError("Transformers dependencies not available")
    
    def _create_onnx_llm(self) -> Any:
        """Создать ONNX локальную модель."""
        try:
            from custom_onnx_llm import ONNXLanguageModel  # Предполагаемый класс
            
            model_path = self.config.get("model_path") or self.model_name
            
            return ONNXLanguageModel(
                model_path=model_path,
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens", 512)
            )
        except ImportError:
            raise ModelCreationError("ONNX dependencies not available")
    
    def _create_tensorrt_llm(self) -> Any:
        """Создать TensorRT локальную модель."""
        try:
            from custom_tensorrt_llm import TensorRTLanguageModel  # Предполагаемый класс
            
            engine_path = self.config.get("engine_path") or self.model_name
            
            return TensorRTLanguageModel(
                engine_path=engine_path,
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens", 512)
            )
        except ImportError:
            raise ModelCreationError("TensorRT dependencies not available")
    
    def _create_openai_compatible_llm(self) -> Any:
        """Создать OpenAI-совместимую модель."""
        try:
            from langchain_openai import ChatOpenAI
            
            endpoint_url = self.config.get("endpoint_url")
            if not endpoint_url:
                raise ModelCreationError("endpoint_url required for OpenAI compatible API")
            
            return ChatOpenAI(
                openai_api_base=endpoint_url,
                openai_api_key=self.api_key or "not-needed",
                model_name=self.model_name,
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens"),
                timeout=self.config.get("timeout", 30)
            )
        except ImportError:
            raise ModelCreationError("OpenAI compatible dependencies not available")
    
    def _create_custom_local_llm(self) -> Any:
        """Создать полностью кастомную локальную модель."""
        try:
            from custom_local_llm import CustomLocalLLM  # Предполагаемый класс
            
            # Получаем все параметры из extra_params
            extra_params = self.config.get("extra_params", {})
            if isinstance(extra_params, str):
                import json
                extra_params = json.loads(extra_params)
            
            return CustomLocalLLM(
                model_name=self.model_name,
                model_path=self.config.get("model_path"),
                endpoint_url=self.config.get("endpoint_url"),
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens"),
                **extra_params
            )
        except ImportError:
            raise ModelCreationError("Custom local LLM dependencies not available")


class STTModelAdapter(BaseModelAdapter):
    """Адаптер для STT моделей."""
    
    def create_model(self) -> Any:
        """Создать STT модель."""
        provider = self.config.get("provider")
        
        if provider == "groq":
            return self._create_groq_stt()
        elif provider == "openai":
            return self._create_openai_stt()
        elif provider == "cartesia":
            return self._create_cartesia_stt()
        elif provider == "local_whisper":
            return self._create_local_whisper()
        elif provider == "custom_endpoint":
            return self._create_custom_stt()
        else:
            raise ModelCreationError(f"Unsupported STT provider: {provider}")
    
    def _create_groq_stt(self) -> Any:
        """Создать Groq STT."""
        if not DEPENDENCIES_AVAILABLE:
            raise ModelCreationError("Groq STT dependencies not available")
        
        if not self.api_key:
            raise ModelCreationError("GROQ_API_KEY not found in environment")
        
        return GroqSTT(
            api_key=self.api_key,
            model=self.model_name,
            timeout=self.config.get("timeout", 30)
        )
    
    def _create_openai_stt(self) -> Any:
        """Создать OpenAI Whisper STT."""
        try:
            from videosdk.plugins.openai import OpenAISTT
            
            if not self.api_key:
                raise ModelCreationError("OPENAI_API_KEY not found in environment")
            
            return OpenAISTT(
                api_key=self.api_key,
                model=self.model_name,
                timeout=self.config.get("timeout", 30)
            )
        except ImportError:
            raise ModelCreationError("OpenAI STT dependencies not available")
    
    def _create_cartesia_stt(self) -> Any:
        """Создать Cartesia STT."""
        if not DEPENDENCIES_AVAILABLE:
            raise ModelCreationError("Cartesia STT dependencies not available")
        
        if not self.api_key:
            raise ModelCreationError("CARTESIA_API_KEY not found in environment")
        
        return SafeCartesiaSTTWrapper(
            api_key=self.api_key,
            model=self.model_name,
            timeout=self.config.get("timeout", 30)
        )
    
    def _create_local_whisper(self) -> Any:
        """Создать локальную Whisper STT."""
        try:
            from whisper_stt_local import LocalWhisperSTT  # Предполагаемый локальный класс
            
            endpoint_url = self.config.get("endpoint_url", "http://localhost:8000")
            
            return LocalWhisperSTT(
                endpoint_url=endpoint_url,
                model=self.model_name,
                timeout=self.config.get("timeout", 60)
            )
        except ImportError:
            raise ModelCreationError("Local Whisper dependencies not available")
    
    def _create_custom_stt(self) -> Any:
        """Создать STT через кастомный endpoint."""
        try:
            from custom_stt import CustomSTT  # Предполагаемый класс для кастомных STT
            
            endpoint_url = self.config.get("endpoint_url")
            if not endpoint_url:
                raise ModelCreationError("endpoint_url required for custom STT")
            
            return CustomSTT(
                endpoint_url=endpoint_url,
                api_key=self.api_key,
                model=self.model_name,
                timeout=self.config.get("timeout", 30)
            )
        except ImportError:
            raise ModelCreationError("Custom STT dependencies not available")


class TTSModelAdapter(BaseModelAdapter):
    """Адаптер для TTS моделей."""
    
    def create_model(self) -> Any:
        """Создать TTS модель."""
        provider = self.config.get("provider")
        
        if provider == "cartesia":
            return self._create_cartesia_tts()
        elif provider == "openai":
            return self._create_openai_tts()
        elif provider == "groq":
            return self._create_groq_tts()
        elif provider == "local_coqui":
            return self._create_coqui_tts()
        elif provider == "local_bark":
            return self._create_bark_tts()
        elif provider == "custom_endpoint":
            return self._create_custom_tts()
        else:
            raise ModelCreationError(f"Unsupported TTS provider: {provider}")
    
    def _create_cartesia_tts(self) -> Any:
        """Создать Cartesia TTS."""
        if not DEPENDENCIES_AVAILABLE:
            raise ModelCreationError("Cartesia TTS dependencies not available")
        
        if not self.api_key:
            raise ModelCreationError("CARTESIA_API_KEY not found in environment")
        
        return SafeCartesiaTTSWrapper(
            api_key=self.api_key,
            model=self.model_name,
            timeout=self.config.get("timeout", 30)
        )
    
    def _create_openai_tts(self) -> Any:
        """Создать OpenAI TTS."""
        if not DEPENDENCIES_AVAILABLE:
            raise ModelCreationError("OpenAI TTS dependencies not available")
        
        if not self.api_key:
            raise ModelCreationError("OPENAI_API_KEY not found in environment")
        
        return OpenAITTS(
            api_key=self.api_key,
            model=self.model_name,
            timeout=self.config.get("timeout", 30)
        )
    
    def _create_groq_tts(self) -> Any:
        """Создать Groq TTS."""
        if not DEPENDENCIES_AVAILABLE:
            raise ModelCreationError("Groq TTS dependencies not available")
        
        return GroqTTSFixed(
            api_key=self.api_key,
            model=self.model_name,
            timeout=self.config.get("timeout", 30)
        )
    
    def _create_coqui_tts(self) -> Any:
        """Создать локальную Coqui TTS."""
        try:
            from coqui_tts_local import LocalCoquiTTS  # Предполагаемый локальный класс
            
            endpoint_url = self.config.get("endpoint_url", "http://localhost:5002")
            
            return LocalCoquiTTS(
                endpoint_url=endpoint_url,
                model=self.model_name,
                timeout=self.config.get("timeout", 60)
            )
        except ImportError:
            raise ModelCreationError("Local Coqui TTS dependencies not available")
    
    def _create_bark_tts(self) -> Any:
        """Создать локальную Bark TTS."""
        try:
            from bark_tts_local import LocalBarkTTS  # Предполагаемый локальный класс
            
            endpoint_url = self.config.get("endpoint_url", "http://localhost:5003")
            
            return LocalBarkTTS(
                endpoint_url=endpoint_url,
                model=self.model_name,
                timeout=self.config.get("timeout", 60)
            )
        except ImportError:
            raise ModelCreationError("Local Bark TTS dependencies not available")
    
    def _create_custom_tts(self) -> Any:
        """Создать TTS через кастомный endpoint."""
        try:
            from custom_tts import CustomTTS  # Предполагаемый класс для кастомных TTS
            
            endpoint_url = self.config.get("endpoint_url")
            if not endpoint_url:
                raise ModelCreationError("endpoint_url required for custom TTS")
            
            return CustomTTS(
                endpoint_url=endpoint_url,
                api_key=self.api_key,
                model=self.model_name,
                timeout=self.config.get("timeout", 30)
            )
        except ImportError:
            raise ModelCreationError("Custom TTS dependencies not available")


class AvatarModelAdapter(BaseModelAdapter):
    """Адаптер для Avatar моделей."""
    
    def create_model(self) -> Any:
        """Создать Avatar модель."""
        provider = self.config.get("provider")
        
        if provider == "simli":
            return self._create_simli_avatar()
        elif provider == "custom_endpoint":
            return self._create_custom_avatar()
        elif provider == "custom_local":
            return self._create_custom_local_avatar()
        else:
            raise ModelCreationError(f"Unsupported Avatar provider: {provider}")
    
    def _create_simli_avatar(self) -> Any:
        """Создать Simli Avatar."""
        try:
            from videosdk.plugins.simli import SimliAvatar, SimliConfig
            
            if not self.api_key:
                raise ModelCreationError("SIMLI_API_KEY not found in environment")
            
            # Получаем параметры из конфигурации
            face_id = self.config.get("face_id", "0c2b8b04-5274-41f1-a21c-d5c98322efa9")
            max_session_length = self.config.get("max_session_length", 1800)
            max_idle_time = self.config.get("max_idle_time", 300)
            
            # Создаем конфигурацию Simli
            simli_config = SimliConfig(
                apiKey=self.api_key,
                faceId=face_id,
                maxSessionLength=max_session_length,
                maxIdleTime=max_idle_time
            )
            
            return SimliAvatar(config=simli_config)
        except ImportError:
            raise ModelCreationError("Simli dependencies not available. Install with: pip install 'videosdk-plugins-simli'")
    
    def _create_custom_avatar(self) -> Any:
        """Создать кастомный Avatar через API."""
        try:
            from custom_avatar_api import CustomAvatarAPI  # Предполагаемый класс
            
            endpoint_url = self.config.get("endpoint_url")
            if not endpoint_url:
                raise ModelCreationError("endpoint_url required for custom avatar")
            
            return CustomAvatarAPI(
                endpoint_url=endpoint_url,
                api_key=self.api_key,
                face_id=self.config.get("face_id"),
                timeout=self.config.get("timeout", 30)
            )
        except ImportError:
            raise ModelCreationError("Custom Avatar API dependencies not available")
    
    def _create_custom_local_avatar(self) -> Any:
        """Создать полностью кастомный локальный Avatar."""
        try:
            from custom_local_avatar import CustomLocalAvatar  # Предполагаемый класс
            
            # Получаем все параметры из extra_params
            extra_params = self.config.get("extra_params", {})
            if isinstance(extra_params, str):
                import json
                extra_params = json.loads(extra_params)
            
            return CustomLocalAvatar(
                model_name=self.model_name,
                model_path=self.config.get("model_path"),
                endpoint_url=self.config.get("endpoint_url"),
                face_id=self.config.get("face_id"),
                max_session_length=self.config.get("max_session_length", 1800),
                max_idle_time=self.config.get("max_idle_time", 300),
                **extra_params
            )
        except ImportError:
            raise ModelCreationError("Custom local Avatar dependencies not available")


class VisionModelAdapter(BaseModelAdapter):
    """Адаптер для Vision моделей."""
    
    def create_model(self) -> Any:
        """Создать Vision модель."""
        provider = self.config.get("provider")
        
        if provider == "google_gemini":
            return self._create_gemini_vision()
        elif provider == "openai_vision":
            return self._create_openai_vision()
        elif provider == "anthropic_vision":
            return self._create_anthropic_vision()
        elif provider == "azure_vision":
            return self._create_azure_vision()
        elif provider == "local_llava":
            return self._create_llava_vision()
        elif provider == "local_cogvlm":
            return self._create_cogvlm_vision()
        elif provider == "local_blip2":
            return self._create_blip2_vision()
        elif provider == "local_instructblip":
            return self._create_instructblip_vision()
        elif provider == "local_minigpt4":
            return self._create_minigpt4_vision()
        elif provider == "local_qwen_vl":
            return self._create_qwen_vl_vision()
        elif provider == "local_internvl":
            return self._create_internvl_vision()
        elif provider == "local_moondream":
            return self._create_moondream_vision()
        elif provider == "local_bakllava":
            return self._create_bakllava_vision()
        elif provider == "custom_endpoint":
            return self._create_custom_vision()
        else:
            raise ModelCreationError(f"Unsupported Vision provider: {provider}")
    
    def _create_gemini_vision(self) -> Any:
        """Создать Google Gemini Vision модель."""
        try:
            import google.generativeai as genai
            
            if not self.api_key:
                raise ModelCreationError("GEMINI_API_KEY not found in environment")
            
            # Настраиваем Gemini API
            genai.configure(api_key=self.api_key)
            
            # Получаем параметры из конфигурации
            model_name = self.model_name or "gemini-1.5-flash"
            
            # Настройки безопасности и генерации
            extra_params = self.config.get("extra_params", {})
            if isinstance(extra_params, str):
                import json
                extra_params = json.loads(extra_params)
            
            generation_config = genai.GenerationConfig(
                max_output_tokens=extra_params.get("max_output_tokens", 2048),
                temperature=extra_params.get("temperature", 0.4),
                top_p=extra_params.get("top_p", 0.8),
                top_k=extra_params.get("top_k", 40)
            )
            
            # Настройки безопасности
            safety_settings = None
            if extra_params.get("safety_settings") == "block_none":
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            
            # Создаем модель
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            return model
        except ImportError:
            raise ModelCreationError("Google Generative AI not available. Install with: pip install google-generativeai")
    
    def _create_openai_vision(self) -> Any:
        """Создать OpenAI Vision модель."""
        try:
            from openai import OpenAI
            
            if not self.api_key:
                raise ModelCreationError("OPENAI_API_KEY not found in environment")
            
            client = OpenAI(api_key=self.api_key)
            
            # Создаем обертку для унифицированного интерфейса
            class OpenAIVisionWrapper:
                def __init__(self, client, model_name, config):
                    self.client = client
                    self.model_name = model_name or "gpt-4-vision-preview"
                    self.config = config
                
                def analyze_image(self, image, prompt="Проанализируй это изображение"):
                    """Анализ изображения через OpenAI Vision."""
                    import base64
                    import io
                    
                    # Конвертируем изображение в base64
                    if hasattr(image, 'save'):  # PIL Image
                        buffer = io.BytesIO()
                        image.save(buffer, format='PNG')
                        image_data = base64.b64encode(buffer.getvalue()).decode()
                    else:
                        raise ValueError("Unsupported image format")
                    
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{image_data}",
                                            "detail": self.config.get("extra_params", {}).get("detail", "high")
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=self.config.get("max_tokens", 4096),
                        temperature=self.config.get("temperature", 0.7)
                    )
                    
                    return response.choices[0].message.content
            
            return OpenAIVisionWrapper(client, self.model_name, self.config)
        except ImportError:
            raise ModelCreationError("OpenAI not available. Install with: pip install openai")
    
    def _create_anthropic_vision(self) -> Any:
        """Создать Anthropic Vision модель."""
        try:
            import anthropic
            
            if not self.api_key:
                raise ModelCreationError("ANTHROPIC_API_KEY not found in environment")
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            # Создаем обертку для унифицированного интерфейса
            class AnthropicVisionWrapper:
                def __init__(self, client, model_name, config):
                    self.client = client
                    self.model_name = model_name or "claude-3-sonnet-20240229"
                    self.config = config
                
                def analyze_image(self, image, prompt="Проанализируй это изображение"):
                    """Анализ изображения через Anthropic Vision."""
                    import base64
                    import io
                    
                    # Конвертируем изображение в base64
                    if hasattr(image, 'save'):  # PIL Image
                        buffer = io.BytesIO()
                        image.save(buffer, format='PNG')
                        image_data = base64.b64encode(buffer.getvalue()).decode()
                    else:
                        raise ValueError("Unsupported image format")
                    
                    response = self.client.messages.create(
                        model=self.model_name,
                        max_tokens=self.config.get("max_tokens", 4096),
                        temperature=self.config.get("temperature", 0.7),
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "image/png",
                                            "data": image_data
                                        }
                                    },
                                    {"type": "text", "text": prompt}
                                ]
                            }
                        ]
                    )
                    
                    return response.content[0].text
            
            return AnthropicVisionWrapper(client, self.model_name, self.config)
        except ImportError:
            raise ModelCreationError("Anthropic not available. Install with: pip install anthropic")
    
    def _create_azure_vision(self) -> Any:
        """Создать Azure Vision модель."""
        try:
            from azure.cognitiveservices.vision.computervision import ComputerVisionClient
            from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
            from msrest.authentication import CognitiveServicesCredentials
            
            endpoint = self.config.get("endpoint_url")
            if not endpoint or not self.api_key:
                raise ModelCreationError("Azure endpoint and API key required")
            
            credentials = CognitiveServicesCredentials(self.api_key)
            client = ComputerVisionClient(endpoint, credentials)
            
            # Создаем обертку для унифицированного интерфейса
            class AzureVisionWrapper:
                def __init__(self, client, config):
                    self.client = client
                    self.config = config
                
                def analyze_image(self, image, prompt="Проанализируй это изображение"):
                    """Анализ изображения через Azure Vision."""
                    import io
                    
                    # Конвертируем изображение в stream
                    if hasattr(image, 'save'):  # PIL Image
                        buffer = io.BytesIO()
                        image.save(buffer, format='PNG')
                        buffer.seek(0)
                    else:
                        raise ValueError("Unsupported image format")
                    
                    # Анализируем изображение
                    analysis = self.client.analyze_image_in_stream(
                        buffer,
                        visual_features=['Description', 'Objects', 'Tags', 'Categories']
                    )
                    
                    # Формируем описание
                    description = analysis.description.captions[0].text if analysis.description.captions else "No description"
                    objects = [obj.object_property for obj in analysis.objects] if analysis.objects else []
                    tags = [tag.name for tag in analysis.tags] if analysis.tags else []
                    
                    result = f"Описание: {description}\n"
                    if objects:
                        result += f"Объекты: {', '.join(objects)}\n"
                    if tags:
                        result += f"Теги: {', '.join(tags)}"
                    
                    return result
            
            return AzureVisionWrapper(client, self.config)
        except ImportError:
            raise ModelCreationError("Azure Cognitive Services not available")
    
    def _create_custom_vision(self) -> Any:
        """Создать кастомную Vision модель через custom endpoint."""
        try:
            import requests
            import json
            
            endpoint_url = self.config.get("endpoint_url")
            if not endpoint_url:
                raise ModelCreationError("endpoint_url required for custom vision")
            
            # Создаем универсальную обертку для любого VLM API
            class CustomVisionWrapper:
                def __init__(self, endpoint_url, api_key, config):
                    self.endpoint_url = endpoint_url.rstrip('/')
                    self.api_key = api_key
                    self.config = config
                    self.timeout = config.get("timeout", 30)
                    self.headers = self._build_headers()
                
                def _build_headers(self):
                    """Построить заголовки для запроса."""
                    headers = {
                        "Content-Type": "application/json",
                        "User-Agent": "MoreTech-AI-HR-VLM/1.0"
                    }
                    
                    # Различные способы передачи API ключа
                    auth_type = self.config.get("extra_params", {}).get("auth_type", "bearer")
                    
                    if self.api_key:
                        if auth_type == "bearer":
                            headers["Authorization"] = f"Bearer {self.api_key}"
                        elif auth_type == "api_key":
                            headers["X-API-Key"] = self.api_key
                        elif auth_type == "openai":
                            headers["Authorization"] = f"Bearer {self.api_key}"
                        elif auth_type == "anthropic":
                            headers["x-api-key"] = self.api_key
                        elif auth_type == "custom_header":
                            custom_header = self.config.get("extra_params", {}).get("auth_header", "Authorization")
                            headers[custom_header] = self.api_key
                    
                    # Дополнительные заголовки
                    extra_headers = self.config.get("extra_params", {}).get("headers", {})
                    headers.update(extra_headers)
                    
                    return headers
                
                def analyze_image(self, image, prompt="Проанализируй это изображение"):
                    """Анализ изображения через custom endpoint."""
                    # Конвертируем изображение в base64
                    import io
                    import base64
                    
                    if hasattr(image, 'save'):  # PIL Image
                        buffer = io.BytesIO()
                        image.save(buffer, format='PNG')
                        image_data = base64.b64encode(buffer.getvalue()).decode()
                    else:
                        raise ValueError("Unsupported image format")
                    
                    # Определяем формат запроса
                    request_format = self.config.get("extra_params", {}).get("request_format", "openai")
                    
                    if request_format == "openai":
                        payload = self._build_openai_payload(image_data, prompt)
                        endpoint = f"{self.endpoint_url}/v1/chat/completions"
                    elif request_format == "anthropic":
                        payload = self._build_anthropic_payload(image_data, prompt)
                        endpoint = f"{self.endpoint_url}/v1/messages"
                    elif request_format == "gemini":
                        payload = self._build_gemini_payload(image_data, prompt)
                        endpoint = f"{self.endpoint_url}/v1/models/{self.config.get('model_name', 'gemini-pro-vision')}:generateContent"
                    elif request_format == "custom":
                        payload = self._build_custom_payload(image_data, prompt)
                        endpoint = f"{self.endpoint_url}{self.config.get('extra_params', {}).get('endpoint_path', '/analyze')}"
                    else:
                        raise ValueError(f"Unsupported request format: {request_format}")
                    
                    # Выполняем запрос
                    response = requests.post(
                        endpoint,
                        headers=self.headers,
                        json=payload,
                        timeout=self.timeout
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"API request failed: {response.status_code} - {response.text}")
                    
                    # Парсим ответ в зависимости от формата
                    return self._parse_response(response.json(), request_format)
                
                def _build_openai_payload(self, image_data, prompt):
                    """Построить payload в формате OpenAI."""
                    return {
                        "model": self.config.get("model_name", "gpt-4-vision-preview"),
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{image_data}",
                                            "detail": self.config.get("extra_params", {}).get("detail", "high")
                                        }
                                    }
                                ]
                            }
                        ],
                        "max_tokens": self.config.get("max_tokens", 4096),
                        "temperature": self.config.get("temperature", 0.7)
                    }
                
                def _build_anthropic_payload(self, image_data, prompt):
                    """Построить payload в формате Anthropic."""
                    return {
                        "model": self.config.get("model_name", "claude-3-sonnet-20240229"),
                        "max_tokens": self.config.get("max_tokens", 4096),
                        "temperature": self.config.get("temperature", 0.7),
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "image/png",
                                            "data": image_data
                                        }
                                    },
                                    {"type": "text", "text": prompt}
                                ]
                            }
                        ]
                    }
                
                def _build_gemini_payload(self, image_data, prompt):
                    """Построить payload в формате Gemini."""
                    return {
                        "contents": [
                            {
                                "parts": [
                                    {"text": prompt},
                                    {
                                        "inline_data": {
                                            "mime_type": "image/png",
                                            "data": image_data
                                        }
                                    }
                                ]
                            }
                        ],
                        "generationConfig": {
                            "maxOutputTokens": self.config.get("max_tokens", 2048),
                            "temperature": self.config.get("temperature", 0.4)
                        }
                    }
                
                def _build_custom_payload(self, image_data, prompt):
                    """Построить кастомный payload."""
                    # Базовый шаблон
                    payload = {
                        "image": image_data,
                        "prompt": prompt,
                        "model": self.config.get("model_name", "custom-vlm"),
                        "max_tokens": self.config.get("max_tokens", 2048),
                        "temperature": self.config.get("temperature", 0.4)
                    }
                    
                    # Дополнительные параметры из конфигурации
                    custom_params = self.config.get("extra_params", {}).get("custom_params", {})
                    payload.update(custom_params)
                    
                    return payload
                
                def _parse_response(self, response_data, request_format):
                    """Парсинг ответа в зависимости от формата."""
                    try:
                        if request_format == "openai":
                            return response_data["choices"][0]["message"]["content"]
                        elif request_format == "anthropic":
                            return response_data["content"][0]["text"]
                        elif request_format == "gemini":
                            return response_data["candidates"][0]["content"]["parts"][0]["text"]
                        elif request_format == "custom":
                            # Пытаемся извлечь текст из различных возможных полей
                            response_field = self.config.get("extra_params", {}).get("response_field", "text")
                            if "." in response_field:
                                # Поддержка вложенных полей типа "result.text"
                                fields = response_field.split(".")
                                result = response_data
                                for field in fields:
                                    result = result[field]
                                return result
                            else:
                                return response_data[response_field]
                        else:
                            # Fallback - пытаемся найти текст в стандартных полях
                            for field in ["text", "content", "result", "response", "output"]:
                                if field in response_data:
                                    return response_data[field]
                            return str(response_data)
                    except (KeyError, IndexError, TypeError) as e:
                        raise Exception(f"Failed to parse response: {e}. Response: {response_data}")
            
            return CustomVisionWrapper(endpoint_url, self.api_key, self.config)
        except ImportError:
            raise ModelCreationError("requests library not available for custom vision endpoint")
    
    def _create_llava_vision(self) -> Any:
        """Создать LLaVA Vision модель."""
        try:
            from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration
            import torch
            
            model_path = self.config.get("model_path") or self.model_name
            if not model_path:
                raise ModelCreationError("model_path required for local LLaVA")
            
            # Загружаем модель и процессор
            processor = LlavaNextProcessor.from_pretrained(model_path)
            model = LlavaNextForConditionalGeneration.from_pretrained(
                model_path,
                torch_dtype=torch.float16 if self.config.get("extra_params", {}).get("dtype") == "float16" else torch.bfloat16,
                low_cpu_mem_usage=True,
                load_in_4bit=self.config.get("extra_params", {}).get("load_in_4bit", False),
                device_map="auto"
            )
            
            # Создаем обертку для унифицированного интерфейса
            class LLaVAVisionWrapper:
                def __init__(self, model, processor, config):
                    self.model = model
                    self.processor = processor
                    self.config = config
                    self.device = config.get("extra_params", {}).get("device", "cuda")
                
                def analyze_image(self, image, prompt="Проанализируй это изображение"):
                    """Анализ изображения через LLaVA."""
                    conversation = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image"},
                            ],
                        },
                    ]
                    
                    prompt_text = self.processor.apply_chat_template(conversation, add_generation_prompt=True)
                    inputs = self.processor(prompt_text, image, return_tensors="pt").to(self.device)
                    
                    # Генерируем ответ
                    with torch.no_grad():
                        output = self.model.generate(
                            **inputs,
                            max_new_tokens=self.config.get("max_tokens", 1024),
                            temperature=self.config.get("temperature", 0.4),
                            do_sample=self.config.get("extra_params", {}).get("do_sample", True),
                            top_p=self.config.get("extra_params", {}).get("top_p", 0.9),
                            pad_token_id=self.processor.tokenizer.eos_token_id
                        )
                    
                    # Декодируем результат
                    generated_text = self.processor.decode(output[0], skip_special_tokens=True)
                    
                    # Извлекаем только сгенерированную часть
                    if "ASSISTANT:" in generated_text:
                        response = generated_text.split("ASSISTANT:")[-1].strip()
                    else:
                        response = generated_text.strip()
                    
                    return response
            
            return LLaVAVisionWrapper(model, processor, self.config)
        except ImportError:
            raise ModelCreationError("LLaVA dependencies not available. Install with: pip install transformers torch accelerate")
    
    def _create_cogvlm_vision(self) -> Any:
        """Создать CogVLM Vision модель."""
        try:
            from transformers import AutoModelForCausalLM, ollamaTokenizer
            import torch
            from PIL import Image
            
            model_path = self.config.get("model_path") or self.model_name
            if not model_path:
                raise ModelCreationError("model_path required for local CogVLM")
            
            # Загружаем токенизатор и модель
            tokenizer = ollamaTokenizer.from_pretrained("lmsys/vicuna-7b-v1.5")
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.bfloat16,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                device_map="auto"
            )
            
            class CogVLMWrapper:
                def __init__(self, model, tokenizer, config):
                    self.model = model
                    self.tokenizer = tokenizer
                    self.config = config
                    self.device = config.get("extra_params", {}).get("device", "cuda")
                
                def analyze_image(self, image, prompt="Проанализируй это изображение"):
                    """Анализ изображения через CogVLM."""
                    # Подготавливаем входные данные
                    inputs = self.model.build_conversation_input_ids(
                        self.tokenizer, 
                        query=prompt, 
                        history=[], 
                        images=[image]
                    )
                    
                    inputs = {
                        'input_ids': inputs['input_ids'].unsqueeze(0).to(self.device),
                        'token_type_ids': inputs['token_type_ids'].unsqueeze(0).to(self.device),
                        'attention_mask': inputs['attention_mask'].unsqueeze(0).to(self.device),
                        'images': [[inputs['images'][0].to(self.device).to(torch.bfloat16)]],
                    }
                    
                    # Генерируем ответ
                    with torch.no_grad():
                        outputs = self.model.generate(
                            **inputs,
                            max_new_tokens=self.config.get("max_tokens", 1024),
                            temperature=self.config.get("temperature", 0.3),
                            do_sample=True,
                            top_p=0.9,
                            pad_token_id=128002,
                        )
                    
                    response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                    return response.split("Assistant:")[-1].strip() if "Assistant:" in response else response.strip()
            
            return CogVLMWrapper(model, tokenizer, self.config)
        except ImportError:
            raise ModelCreationError("CogVLM dependencies not available")
    
    def _create_qwen_vl_vision(self) -> Any:
        """Создать Qwen-VL Vision модель."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            model_path = self.config.get("model_path") or self.model_name
            if not model_path:
                raise ModelCreationError("model_path required for local Qwen-VL")
            
            # Загружаем модель и токенизатор
            tokenizer = AutoTokenizer.from_pretrained(
                model_path, 
                trust_remote_code=self.config.get("extra_params", {}).get("trust_remote_code", True)
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                device_map="auto",
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.config.get("extra_params", {}).get("dtype") == "float16" else torch.bfloat16
            )
            
            class QwenVLWrapper:
                def __init__(self, model, tokenizer, config):
                    self.model = model
                    self.tokenizer = tokenizer
                    self.config = config
                
                def analyze_image(self, image, prompt="Проанализируй это изображение"):
                    """Анализ изображения через Qwen-VL."""
                    import tempfile
                    import os
                    
                    # Сохраняем изображение во временный файл
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                        image.save(tmp_file.name)
                        image_path = tmp_file.name
                    
                    try:
                        # Формируем запрос с изображением
                        query = self.tokenizer.from_list_format([
                            {'image': image_path},
                            {'text': prompt},
                        ])
                        
                        # Генерируем ответ
                        response, _ = self.model.chat(
                            self.tokenizer, 
                            query=query, 
                            history=None,
                            max_new_tokens=self.config.get("max_tokens", 2048),
                            temperature=self.config.get("temperature", 0.4)
                        )
                        
                        return response
                    finally:
                        # Удаляем временный файл
                        if os.path.exists(image_path):
                            os.unlink(image_path)
            
            return QwenVLWrapper(model, tokenizer, self.config)
        except ImportError:
            raise ModelCreationError("Qwen-VL dependencies not available")
    
    def _create_moondream_vision(self) -> Any:
        """Создать MoonDream Vision модель."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            model_path = self.config.get("model_path") or self.model_name
            if not model_path:
                raise ModelCreationError("model_path required for local MoonDream")
            
            # Загружаем модель
            model = AutoModelForCausalLM.from_pretrained(
                model_path, 
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.config.get("extra_params", {}).get("dtype") == "float16" else torch.bfloat16,
                device_map="auto"
            )
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            
            class MoonDreamWrapper:
                def __init__(self, model, tokenizer, config):
                    self.model = model
                    self.tokenizer = tokenizer
                    self.config = config
                
                def analyze_image(self, image, prompt="Проанализируй это изображение"):
                    """Анализ изображения через MoonDream."""
                    # MoonDream имеет простой интерфейс
                    enc_image = self.model.encode_image(image)
                    response = self.model.answer_question(enc_image, prompt, self.tokenizer)
                    return response
            
            return MoonDreamWrapper(model, tokenizer, self.config)
        except ImportError:
            raise ModelCreationError("MoonDream dependencies not available")
    
    def _create_internvl_vision(self) -> Any:
        """Создать InternVL Vision модель."""
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch
            
            model_path = self.config.get("model_path") or self.model_name
            if not model_path:
                raise ModelCreationError("model_path required for local InternVL")
            
            # Загружаем модель и токенизатор
            tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            model = AutoModel.from_pretrained(
                model_path,
                torch_dtype=torch.bfloat16,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                device_map="auto"
            )
            
            class InternVLWrapper:
                def __init__(self, model, tokenizer, config):
                    self.model = model
                    self.tokenizer = tokenizer
                    self.config = config
                
                def analyze_image(self, image, prompt="Проанализируй это изображение"):
                    """Анализ изображения через InternVL."""
                    pixel_values = self.model.preprocess_image(image).unsqueeze(0).cuda()
                    
                    # Генерируем ответ
                    response = self.model.chat(
                        self.tokenizer,
                        pixel_values,
                        prompt,
                        generation_config=dict(
                            num_beams=1,
                            max_new_tokens=self.config.get("max_tokens", 2048),
                            do_sample=False,
                            temperature=self.config.get("temperature", 0.3)
                        )
                    )
                    
                    return response
            
            return InternVLWrapper(model, tokenizer, self.config)
        except ImportError:
            raise ModelCreationError("InternVL dependencies not available")
    
    def _create_blip2_vision(self) -> Any:
        """Создать BLIP2 Vision модель."""
        try:
            from transformers import Blip2Processor, Blip2ForConditionalGeneration
            import torch
            
            model_path = self.config.get("model_path") or "Salesforce/blip2-opt-2.7b"
            
            processor = Blip2Processor.from_pretrained(model_path)
            model = Blip2ForConditionalGeneration.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            class BLIP2Wrapper:
                def __init__(self, model, processor, config):
                    self.model = model
                    self.processor = processor
                    self.config = config
                
                def analyze_image(self, image, prompt="Проанализируй это изображение"):
                    """Анализ изображения через BLIP2."""
                    inputs = self.processor(image, prompt, return_tensors="pt").to("cuda")
                    
                    with torch.no_grad():
                        generated_ids = self.model.generate(
                            **inputs,
                            max_new_tokens=self.config.get("max_tokens", 1024),
                            temperature=self.config.get("temperature", 0.4)
                        )
                    
                    response = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
                    return response
            
            return BLIP2Wrapper(model, processor, self.config)
        except ImportError:
            raise ModelCreationError("BLIP2 dependencies not available")
    
    def _create_instructblip_vision(self) -> Any:
        """Создать InstructBLIP Vision модель."""
        try:
            from transformers import InstructBlipProcessor, InstructBlipForConditionalGeneration
            import torch
            
            model_path = self.config.get("model_path") or "Salesforce/instructblip-vicuna-7b"
            
            processor = InstructBlipProcessor.from_pretrained(model_path)
            model = InstructBlipForConditionalGeneration.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            class InstructBLIPWrapper:
                def __init__(self, model, processor, config):
                    self.model = model
                    self.processor = processor
                    self.config = config
                
                def analyze_image(self, image, prompt="Проанализируй это изображение"):
                    """Анализ изображения через InstructBLIP."""
                    inputs = self.processor(images=image, text=prompt, return_tensors="pt").to("cuda")
                    
                    with torch.no_grad():
                        outputs = self.model.generate(
                            **inputs,
                            max_new_tokens=self.config.get("max_tokens", 1024),
                            temperature=self.config.get("temperature", 0.4),
                            do_sample=True
                        )
                    
                    response = self.processor.batch_decode(outputs, skip_special_tokens=True)[0].strip()
                    return response
            
            return InstructBLIPWrapper(model, processor, self.config)
        except ImportError:
            raise ModelCreationError("InstructBLIP dependencies not available")
    
    def _create_minigpt4_vision(self) -> Any:
        """Создать MiniGPT4 Vision модель."""
        try:
            # MiniGPT4 требует специальной установки
            from minigpt4.common.config import Config
            from minigpt4.common.registry import registry
            from minigpt4.conversation.conversation import Chat, CONV_VISION_Vicuna0
            
            model_path = self.config.get("model_path")
            if not model_path:
                raise ModelCreationError("model_path required for local MiniGPT4")
            
            # Инициализируем модель через конфигурацию MiniGPT4
            cfg = Config(args=None, config_path=f"{model_path}/config.yaml")
            model_cls = registry.get_model_class(cfg.model_cfg.arch)
            model = model_cls.from_config(cfg.model_cfg).cuda()
            
            class MiniGPT4Wrapper:
                def __init__(self, model, config):
                    self.model = model
                    self.config = config
                    self.chat = Chat(model, vis_processor, device='cuda')
                
                def analyze_image(self, image, prompt="Проанализируй это изображение"):
                    """Анализ изображения через MiniGPT4."""
                    chat_state = CONV_VISION_Vicuna0.copy()
                    img_list = []
                    
                    self.chat.upload_img(image, chat_state, img_list)
                    self.chat.ask(prompt, chat_state)
                    
                    response = self.chat.answer(
                        conv=chat_state,
                        img_list=img_list,
                        max_new_tokens=self.config.get("max_tokens", 1024),
                        temperature=self.config.get("temperature", 0.4)
                    )[0]
                    
                    return response
            
            return MiniGPT4Wrapper(model, self.config)
        except ImportError:
            raise ModelCreationError("MiniGPT4 dependencies not available")
    
    def _create_bakllava_vision(self) -> Any:
        """Создать BakLLaVA Vision модель."""
        try:
            from transformers import AutoProcessor, LlavaForConditionalGeneration
            import torch
            
            model_path = self.config.get("model_path") or "SkunkworksAI/BakLLaVA-1"
            
            processor = AutoProcessor.from_pretrained(model_path)
            model = LlavaForConditionalGeneration.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            class BakLLaVAWrapper:
                def __init__(self, model, processor, config):
                    self.model = model
                    self.processor = processor
                    self.config = config
                
                def analyze_image(self, image, prompt="Проанализируй это изображение"):
                    """Анализ изображения через BakLLaVA."""
                    inputs = self.processor(
                        text=f"USER: {prompt} ASSISTANT:",
                        images=image,
                        return_tensors="pt"
                    ).to("cuda")
                    
                    with torch.no_grad():
                        outputs = self.model.generate(
                            **inputs,
                            max_new_tokens=self.config.get("max_tokens", 1024),
                            temperature=self.config.get("temperature", 0.4),
                            do_sample=True
                        )
                    
                    response = self.processor.decode(outputs[0], skip_special_tokens=True)
                    
                    # Извлекаем только ответ ассистента
                    if "ASSISTANT:" in response:
                        response = response.split("ASSISTANT:")[-1].strip()
                    
                    return response
            
            return BakLLaVAWrapper(model, processor, self.config)
        except ImportError:
            raise ModelCreationError("BakLLaVA dependencies not available")


class ModelFactory:
    """
    Фабрика для создания различных типов AI моделей.
    
    Поддерживает создание LLM, STT, TTS и Avatar моделей на основе конфигурации.
    """
    
    @staticmethod
    def create_llm_model(config: Dict[str, Any]) -> Any:
        """
        Создать LLM модель.
        
        Args:
            config: Конфигурация модели
            
        Returns:
            Экземпляр LLM модели
            
        Raises:
            ModelCreationError: Если не удалось создать модель
        """
        try:
            adapter = LLMModelAdapter(config)
            model = adapter.create_model()
            logger.info(f"Created LLM model: {config.get('name')} ({config.get('provider')})")
            return model
        except Exception as e:
            error_msg = f"Failed to create LLM model {config.get('name')}: {e}"
            logger.error(error_msg)
            raise ModelCreationError(error_msg) from e
    
    @staticmethod
    def create_stt_model(config: Dict[str, Any]) -> Any:
        """
        Создать STT модель.
        
        Args:
            config: Конфигурация модели
            
        Returns:
            Экземпляр STT модели
            
        Raises:
            ModelCreationError: Если не удалось создать модель
        """
        try:
            adapter = STTModelAdapter(config)
            model = adapter.create_model()
            logger.info(f"Created STT model: {config.get('name')} ({config.get('provider')})")
            return model
        except Exception as e:
            error_msg = f"Failed to create STT model {config.get('name')}: {e}"
            logger.error(error_msg)
            raise ModelCreationError(error_msg) from e
    
    @staticmethod
    def create_tts_model(config: Dict[str, Any]) -> Any:
        """
        Создать TTS модель.
        
        Args:
            config: Конфигурация модели
            
        Returns:
            Экземпляр TTS модели
            
        Raises:
            ModelCreationError: Если не удалось создать модель
        """
        try:
            adapter = TTSModelAdapter(config)
            model = adapter.create_model()
            logger.info(f"Created TTS model: {config.get('name')} ({config.get('provider')})")
            return model
        except Exception as e:
            error_msg = f"Failed to create TTS model {config.get('name')}: {e}"
            logger.error(error_msg)
            raise ModelCreationError(error_msg) from e
    
    @staticmethod
    def create_avatar_model(config: Dict[str, Any]) -> Any:
        """
        Создать Avatar модель.
        
        Args:
            config: Конфигурация модели
            
        Returns:
            Экземпляр Avatar модели
            
        Raises:
            ModelCreationError: Если не удалось создать модель
        """
        try:
            adapter = AvatarModelAdapter(config)
            model = adapter.create_model()
            logger.info(f"Created Avatar model: {config.get('name')} ({config.get('provider')})")
            return model
        except Exception as e:
            error_msg = f"Failed to create Avatar model {config.get('name')}: {e}"
            logger.error(error_msg)
            raise ModelCreationError(error_msg) from e
    
    @staticmethod
    def create_vision_model(config: Dict[str, Any]) -> Any:
        """
        Создать Vision модель.
        
        Args:
            config: Конфигурация модели
            
        Returns:
            Экземпляр Vision модели
            
        Raises:
            ModelCreationError: Если не удалось создать модель
        """
        try:
            adapter = VisionModelAdapter(config)
            model = adapter.create_model()
            logger.info(f"Created Vision model: {config.get('name')} ({config.get('provider')})")
            return model
        except Exception as e:
            error_msg = f"Failed to create Vision model {config.get('name')}: {e}"
            logger.error(error_msg)
            raise ModelCreationError(error_msg) from e
    
    @staticmethod
    def create_models_from_config(models_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создать все модели из конфигурации интервью.
        
        Args:
            models_config: Конфигурация моделей интервью
            
        Returns:
            Словарь с созданными моделями
        """
        models = {}
        
        # Создаем LLM модель
        llm_config = models_config.get("llm_model")
        if llm_config:
            try:
                models["llm"] = ModelFactory.create_llm_model(llm_config)
            except ModelCreationError as e:
                logger.warning(f"Failed to create LLM model, using fallback: {e}")
                models["llm"] = None
        
        # Создаем STT модель
        stt_config = models_config.get("stt_model")
        if stt_config:
            try:
                models["stt"] = ModelFactory.create_stt_model(stt_config)
            except ModelCreationError as e:
                logger.warning(f"Failed to create STT model, using fallback: {e}")
                models["stt"] = None
        
        # Создаем TTS модель
        tts_config = models_config.get("tts_model")
        if tts_config:
            try:
                models["tts"] = ModelFactory.create_tts_model(tts_config)
            except ModelCreationError as e:
                logger.warning(f"Failed to create TTS model, using fallback: {e}")
                models["tts"] = None
        
        # Создаем Avatar модель
        avatar_config = models_config.get("avatar_model")
        if avatar_config:
            try:
                models["avatar"] = ModelFactory.create_avatar_model(avatar_config)
            except ModelCreationError as e:
                logger.warning(f"Failed to create Avatar model, using fallback: {e}")
                models["avatar"] = None
        
        # Создаем Vision модель
        vision_config = models_config.get("vision_model")
        if vision_config:
            try:
                models["vision"] = ModelFactory.create_vision_model(vision_config)
            except ModelCreationError as e:
                logger.warning(f"Failed to create Vision model, using fallback: {e}")
                models["vision"] = None
        
        logger.info(f"Created {len([m for m in models.values() if m is not None])} models from configuration")
        return models
    
    @staticmethod
    def validate_model_config(config: Dict[str, Any]) -> bool:
        """
        Валидировать конфигурацию модели.
        
        Args:
            config: Конфигурация модели
            
        Returns:
            True если конфигурация валидна
        """
        required_fields = ["name", "model_type", "provider", "model_name"]
        
        for field in required_fields:
            if field not in config or not config[field]:
                logger.error(f"Missing required field in model config: {field}")
                return False
        
        # Проверяем API ключ для API провайдеров
        api_providers = [
            "openai", "groq", "anthropic", "cartesia", 
            "huggingface", "replicate", "cohere"
        ]
        if config.get("provider") in api_providers:
            api_key_name = config.get("api_key_name")
            if not api_key_name:
                logger.error("api_key_name required for API providers")
                return False
            
            api_key = os.getenv(api_key_name)
            if not api_key:
                logger.warning(f"API key {api_key_name} not found in environment")
                # Не возвращаем False, так как ключ может быть установлен позже
        
        # Проверяем endpoint для локальных и кастомных провайдеров
        endpoint_providers = [
            "local_oollama", "local_whisper", "local_coqui", "local_bark",
            "local_vllm", "custom_endpoint", "custom_local", "openai_compatible"
        ]
        if config.get("provider") in endpoint_providers:
            endpoint_url = config.get("endpoint_url")
            if not endpoint_url:
                logger.error("endpoint_url required for local/custom providers")
                return False
        
        # Проверяем model_path для провайдеров, которые работают с локальными файлами
        file_providers = ["local_ollamacpp", "local_onnx", "local_tensorrt"]
        if config.get("provider") in file_providers:
            model_path = config.get("model_path") or config.get("engine_path")
            if not model_path:
                logger.error("model_path or engine_path required for file-based providers")
                return False
        
        # Для transformers проверяем, что model_name это валидное HF repo
        if config.get("provider") == "local_transformers":
            if not config.get("model_name"):
                logger.error("model_name (HuggingFace repo) required for transformers provider")
                return False
        
        # Для Simli Avatar проверяем специфичные параметры
        if config.get("provider") == "simli":
            api_key_name = config.get("api_key_name")
            if not api_key_name:
                logger.error("api_key_name required for Simli provider")
                return False
            
            # Проверяем face_id (опционально, есть дефолтное значение)
            face_id = config.get("face_id")
            if face_id and not isinstance(face_id, str):
                logger.error("face_id must be a string")
                return False
        
        # Для Vision провайдеров проверяем специфичные параметры
        api_vision_providers = ["google_gemini", "openai_vision", "anthropic_vision", "azure_vision"]
        local_vision_providers = [
            "local_llava", "local_cogvlm", "local_blip2", "local_instructblip", 
            "local_minigpt4", "local_qwen_vl", "local_internvl", "local_moondream", "local_bakllava"
        ]
        
        if config.get("provider") in api_vision_providers:
            api_key_name = config.get("api_key_name")
            if not api_key_name:
                logger.error("api_key_name required for API Vision providers")
                return False
            
            # Для Azure дополнительно проверяем endpoint
            if config.get("provider") == "azure_vision":
                endpoint_url = config.get("endpoint_url")
                if not endpoint_url:
                    logger.error("endpoint_url required for Azure Vision")
                    return False
        
        elif config.get("provider") in local_vision_providers:
            model_path = config.get("model_path")
            if not model_path:
                logger.error("model_path required for local Vision providers")
                return False
            
            # Проверяем дополнительные параметры для некоторых моделей
            if config.get("provider") in ["local_qwen_vl", "local_cogvlm"]:
                trust_remote_code = config.get("extra_params", {}).get("trust_remote_code")
                if trust_remote_code is None:
                    logger.warning("trust_remote_code parameter recommended for some local Vision models")
        
        # Для Custom Endpoint провайдеров проверяем специфичные параметры
        elif config.get("provider") == "custom_endpoint":
            endpoint_url = config.get("endpoint_url")
            if not endpoint_url:
                logger.error("endpoint_url required for custom_endpoint provider")
                return False
            
            request_format = config.get("extra_params", {}).get("request_format", "openai")
            if request_format not in ["openai", "anthropic", "gemini", "custom"]:
                logger.error(f"Invalid request_format: {request_format}")
                return False
            
            auth_type = config.get("extra_params", {}).get("auth_type", "bearer")
            valid_auth_types = ["bearer", "api_key", "anthropic", "openai", "none", "custom_header"]
            if auth_type not in valid_auth_types:
                logger.error(f"Invalid auth_type: {auth_type}")
                return False
            
            # Проверяем кастомные параметры для специфичных auth_type
            if auth_type == "custom_header":
                auth_header = config.get("extra_params", {}).get("auth_header")
                if not auth_header:
                    logger.error("auth_header required when auth_type is custom_header")
                    return False
            
            # Проверяем параметры для кастомного формата
            if request_format == "custom":
                response_field = config.get("extra_params", {}).get("response_field")
                if not response_field:
                    logger.warning("response_field recommended for custom request format")
        
        return True


# Удобные функции для создания моделей
def create_interview_models(vacancy_id: int, db_session=None) -> Dict[str, Any]:
    """
    Создать все модели для интервью по ID вакансии.
    
    Args:
        vacancy_id: ID вакансии
        db_session: Сессия базы данных
        
    Returns:
        Словарь с созданными моделями
    """
    from .model_service import get_interview_models_config
    
    # Получаем конфигурацию моделей
    models_config = get_interview_models_config(vacancy_id, db_session)
    
    # Создаем модели
    return ModelFactory.create_models_from_config(models_config)


def test_model_availability(config: Dict[str, Any]) -> bool:
    """
    Протестировать доступность модели.
    
    Args:
        config: Конфигурация модели
        
    Returns:
        True если модель доступна
    """
    try:
        model_type = config.get("model_type")
        
        if model_type == "llm":
            ModelFactory.create_llm_model(config)
        elif model_type == "stt":
            ModelFactory.create_stt_model(config)
        elif model_type == "tts":
            ModelFactory.create_tts_model(config)
        else:
            return False
        
        return True
    except Exception as e:
        logger.debug(f"Model availability test failed: {e}")
        return False
