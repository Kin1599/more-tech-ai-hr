"""
Конфигурация потокового режима для агентных компонентов.

Позволяет включать/выключать потоковое получение для различных компонентов.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class StreamingMode(Enum):
    """Режимы потокового получения"""
    DISABLED = "disabled"  # Потоковое получение отключено
    ENABLED = "enabled"    # Потоковое получение включено
    AUTO = "auto"         # Автоматический выбор на основе контекста

@dataclass
class StreamingConfig:
    """Конфигурация потокового режима"""
    
    # LLM настройки
    llm_streaming: StreamingMode = StreamingMode.ENABLED
    llm_chunk_size: int = 50  # Размер чанка для LLM
    
    # TTS настройки
    tts_streaming: StreamingMode = StreamingMode.ENABLED
    tts_sentence_threshold: int = 100  # Минимальная длина для потокового TTS
    tts_chunk_delay: float = 0.1  # Задержка между чанками (секунды)
    
    # STT настройки
    stt_streaming: StreamingMode = StreamingMode.ENABLED
    stt_partial_results: bool = True  # Промежуточные результаты
    stt_buffer_size: int = 3  # Размер буфера в секундах для промежуточных результатов
    
    # VLM настройки
    vlm_streaming: StreamingMode = StreamingMode.AUTO
    vlm_streaming_threshold: int = 2000  # Минимальная длина ответа для потокового режима
    
    # Общие настройки
    enable_adaptive_streaming: bool = True  # Адаптивное потоковое получение
    streaming_timeout: float = 30.0  # Таймаут для потоковых операций
    max_concurrent_streams: int = 3  # Максимальное количество одновременных потоков
    
    @classmethod
    def from_env(cls) -> "StreamingConfig":
        """Создать конфигурацию из переменных окружения"""
        return cls(
            llm_streaming=StreamingMode(os.getenv("LLM_STREAMING", "enabled")),
            llm_chunk_size=int(os.getenv("LLM_CHUNK_SIZE", "50")),
            
            tts_streaming=StreamingMode(os.getenv("TTS_STREAMING", "enabled")),
            tts_sentence_threshold=int(os.getenv("TTS_SENTENCE_THRESHOLD", "100")),
            tts_chunk_delay=float(os.getenv("TTS_CHUNK_DELAY", "0.1")),
            
            stt_streaming=StreamingMode(os.getenv("STT_STREAMING", "enabled")),
            stt_partial_results=os.getenv("STT_PARTIAL_RESULTS", "true").lower() == "true",
            stt_buffer_size=int(os.getenv("STT_BUFFER_SIZE", "3")),
            
            vlm_streaming=StreamingMode(os.getenv("VLM_STREAMING", "auto")),
            vlm_streaming_threshold=int(os.getenv("VLM_STREAMING_THRESHOLD", "2000")),
            
            enable_adaptive_streaming=os.getenv("ENABLE_ADAPTIVE_STREAMING", "true").lower() == "true",
            streaming_timeout=float(os.getenv("STREAMING_TIMEOUT", "30.0")),
            max_concurrent_streams=int(os.getenv("MAX_CONCURRENT_STREAMS", "3"))
        )
    
    def should_enable_streaming(self, component: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Определить, нужно ли включать потоковое получение для компонента"""
        if not self.enable_adaptive_streaming:
            return self._get_component_mode(component) == StreamingMode.ENABLED
        
        # Адаптивная логика
        if component == "llm":
            return self._should_enable_llm_streaming(context)
        elif component == "tts":
            return self._should_enable_tts_streaming(context)
        elif component == "stt":
            return self._should_enable_stt_streaming(context)
        elif component == "vlm":
            return self._should_enable_vlm_streaming(context)
        
        return False
    
    def _get_component_mode(self, component: str) -> StreamingMode:
        """Получить режим для компонента"""
        if component == "llm":
            return self.llm_streaming
        elif component == "tts":
            return self.tts_streaming
        elif component == "stt":
            return self.stt_streaming
        elif component == "vlm":
            return self.vlm_streaming
        return StreamingMode.DISABLED
    
    def _should_enable_llm_streaming(self, context: Optional[Dict[str, Any]]) -> bool:
        """Определить потоковое получение для LLM"""
        mode = self.llm_streaming
        
        if mode == StreamingMode.DISABLED:
            return False
        elif mode == StreamingMode.ENABLED:
            return True
        else:  # AUTO
            # Включаем потоковое получение для длинных ответов
            if context and "expected_length" in context:
                return context["expected_length"] > 200
            return True
    
    def _should_enable_tts_streaming(self, context: Optional[Dict[str, Any]]) -> bool:
        """Определить потоковое получение для TTS"""
        mode = self.tts_streaming
        
        if mode == StreamingMode.DISABLED:
            return False
        elif mode == StreamingMode.ENABLED:
            return True
        else:  # AUTO
            # Включаем для длинных текстов
            if context and "text_length" in context:
                return context["text_length"] > self.tts_sentence_threshold
            return True
    
    def _should_enable_stt_streaming(self, context: Optional[Dict[str, Any]]) -> bool:
        """Определить потоковое получение для STT"""
        mode = self.stt_streaming
        
        if mode == StreamingMode.DISABLED:
            return False
        elif mode == StreamingMode.ENABLED:
            return True
        else:  # AUTO
            # Всегда включаем для длинных аудио сессий
            return True
    
    def _should_enable_vlm_streaming(self, context: Optional[Dict[str, Any]]) -> bool:
        """Определить потоковое получение для VLM"""
        mode = self.vlm_streaming
        
        if mode == StreamingMode.DISABLED:
            return False
        elif mode == StreamingMode.ENABLED:
            return True
        else:  # AUTO
            # Включаем для сложных изображений или длинных промптов
            if context:
                prompt_length = context.get("prompt_length", 0)
                image_complexity = context.get("image_complexity", "medium")
                return prompt_length > 100 or image_complexity == "high"
            return False
    
    def get_component_config(self, component: str) -> Dict[str, Any]:
        """Получить конфигурацию для компонента"""
        config = {
            "streaming_enabled": self.should_enable_streaming(component),
            "timeout": self.streaming_timeout,
            "max_concurrent_streams": self.max_concurrent_streams
        }
        
        if component == "llm":
            config.update({
                "chunk_size": self.llm_chunk_size
            })
        elif component == "tts":
            config.update({
                "sentence_threshold": self.tts_sentence_threshold,
                "chunk_delay": self.tts_chunk_delay
            })
        elif component == "stt":
            config.update({
                "partial_results": self.stt_partial_results,
                "buffer_size": self.stt_buffer_size
            })
        elif component == "vlm":
            config.update({
                "streaming_threshold": self.vlm_streaming_threshold
            })
        
        return config

# Глобальная конфигурация
_streaming_config: Optional[StreamingConfig] = None

def get_streaming_config() -> StreamingConfig:
    """Получить глобальную конфигурацию потокового режима"""
    global _streaming_config
    if _streaming_config is None:
        _streaming_config = StreamingConfig.from_env()
    return _streaming_config

def set_streaming_config(config: StreamingConfig) -> None:
    """Установить глобальную конфигурацию потокового режима"""
    global _streaming_config
    _streaming_config = config

def reset_streaming_config() -> None:
    """Сбросить глобальную конфигурацию потокового режима"""
    global _streaming_config
    _streaming_config = None

# Предустановленные конфигурации
PRESET_CONFIGS = {
    "performance": StreamingConfig(
        llm_streaming=StreamingMode.ENABLED,
        tts_streaming=StreamingMode.ENABLED,
        stt_streaming=StreamingMode.ENABLED,
        vlm_streaming=StreamingMode.ENABLED,
        enable_adaptive_streaming=True,
        streaming_timeout=15.0,
        max_concurrent_streams=5
    ),
    
    "balanced": StreamingConfig(
        llm_streaming=StreamingMode.AUTO,
        tts_streaming=StreamingMode.AUTO,
        stt_streaming=StreamingMode.ENABLED,
        vlm_streaming=StreamingMode.AUTO,
        enable_adaptive_streaming=True,
        streaming_timeout=30.0,
        max_concurrent_streams=3
    ),
    
    "quality": StreamingConfig(
        llm_streaming=StreamingMode.DISABLED,
        tts_streaming=StreamingMode.DISABLED,
        stt_streaming=StreamingMode.DISABLED,
        vlm_streaming=StreamingMode.DISABLED,
        enable_adaptive_streaming=False,
        streaming_timeout=60.0,
        max_concurrent_streams=1
    ),
    
    "realtime": StreamingConfig(
        llm_streaming=StreamingMode.ENABLED,
        tts_streaming=StreamingMode.ENABLED,
        stt_streaming=StreamingMode.ENABLED,
        vlm_streaming=StreamingMode.ENABLED,
        enable_adaptive_streaming=True,
        streaming_timeout=10.0,
        max_concurrent_streams=10,
        tts_chunk_delay=0.05,
        stt_buffer_size=1
    )
}

def load_preset_config(preset_name: str) -> StreamingConfig:
    """Загрузить предустановленную конфигурацию"""
    if preset_name not in PRESET_CONFIGS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(PRESET_CONFIGS.keys())}")
    
    config = PRESET_CONFIGS[preset_name]
    set_streaming_config(config)
    return config
