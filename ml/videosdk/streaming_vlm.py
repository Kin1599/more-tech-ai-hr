"""
Потоковые Vision Language Models для анализа экрана в реальном времени.

Поддерживает различные провайдеры VLM с возможностью потокового получения результатов.
"""

import asyncio
import logging
from typing import Optional, AsyncIterator, Any, Dict, List
from abc import ABC, abstractmethod
import base64
import io
from PIL import Image
import httpx
import json

logger = logging.getLogger(__name__)

class StreamingVLMBase(ABC):
    """Базовый класс для потоковых VLM"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._cancelled = False
        
    @abstractmethod
    async def analyze_image_streaming(
        self, 
        image: Image.Image, 
        prompt: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """Потоковый анализ изображения"""
        pass
    
    async def cancel_analysis(self) -> None:
        """Отменить текущий анализ"""
        self._cancelled = True

class StreamingGroqVLM(StreamingVLMBase):
    """Потоковый Groq VLM (если поддерживается)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.model = config.get("model_name", "llava-13b")
        self.base_url = config.get("endpoint_url", "https://api.groq.com/openai/v1")
        
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=15.0, read=30.0, write=10.0, pool=10.0),
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    async def analyze_image_streaming(
        self, 
        image: Image.Image, 
        prompt: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """Потоковый анализ изображения через Groq API"""
        if self._cancelled:
            return
            
        try:
            # Конвертируем изображение в base64
            image_b64 = self._image_to_base64(image)
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                "stream": True,
                "temperature": self.config.get("temperature", 0.7),
                "max_tokens": self.config.get("max_tokens", 2048)
            }
            
            async with self._client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if self._cancelled:
                        break
                        
                    if line.startswith("data: "):
                        data = line[6:]  # Убираем "data: "
                        if data.strip() == "[DONE]":
                            break
                            
                        try:
                            chunk_data = json.loads(data)
                            if "choices" in chunk_data and chunk_data["choices"]:
                                delta = chunk_data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Groq streaming VLM error: {e}")
            yield f"Ошибка анализа: {str(e)}"
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Конвертировать изображение в base64"""
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode()

class StreamingOpenAIVLM(StreamingVLMBase):
    """Потоковый OpenAI VLM"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.model = config.get("model_name", "gpt-4-vision-preview")
        self.base_url = config.get("endpoint_url", "https://api.openai.com/v1")
        
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=15.0, read=30.0, write=10.0, pool=10.0),
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    async def analyze_image_streaming(
        self, 
        image: Image.Image, 
        prompt: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """Потоковый анализ изображения через OpenAI API"""
        if self._cancelled:
            return
            
        try:
            # Конвертируем изображение в base64
            image_b64 = self._image_to_base64(image)
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                "stream": True,
                "temperature": self.config.get("temperature", 0.7),
                "max_tokens": self.config.get("max_tokens", 2048)
            }
            
            async with self._client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if self._cancelled:
                        break
                        
                    if line.startswith("data: "):
                        data = line[6:]  # Убираем "data: "
                        if data.strip() == "[DONE]":
                            break
                            
                        try:
                            chunk_data = json.loads(data)
                            if "choices" in chunk_data and chunk_data["choices"]:
                                delta = chunk_data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"OpenAI streaming VLM error: {e}")
            yield f"Ошибка анализа: {str(e)}"
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Конвертировать изображение в base64"""
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode()

class StreamingCustomVLM(StreamingVLMBase):
    """Потоковый кастомный VLM endpoint"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.endpoint_url = config.get("endpoint_url")
        self.model = config.get("model_name")
        self.api_key = config.get("api_key")
        self.request_format = config.get("request_format", "openai")
        self.auth_type = config.get("auth_type", "bearer")
        
        # Настраиваем клиент
        headers = {}
        if self.api_key:
            if self.auth_type == "bearer":
                headers["Authorization"] = f"Bearer {self.api_key}"
            elif self.auth_type == "api_key":
                headers["X-API-Key"] = self.api_key
        
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=15.0, read=30.0, write=10.0, pool=10.0),
            headers=headers
        )
    
    async def analyze_image_streaming(
        self, 
        image: Image.Image, 
        prompt: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """Потоковый анализ изображения через кастомный endpoint"""
        if self._cancelled:
            return
            
        try:
            # Конвертируем изображение в base64
            image_b64 = self._image_to_base64(image)
            
            # Формируем payload в зависимости от формата
            if self.request_format == "openai":
                payload = self._create_openai_payload(image_b64, prompt)
                endpoint = f"{self.endpoint_url}/chat/completions"
            elif self.request_format == "anthropic":
                payload = self._create_anthropic_payload(image_b64, prompt)
                endpoint = f"{self.endpoint_url}/messages"
            else:
                # Кастомный формат
                payload = self._create_custom_payload(image_b64, prompt)
                endpoint = self.endpoint_url
            
            async with self._client.stream(
                "POST",
                endpoint,
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if self._cancelled:
                        break
                        
                    if line.startswith("data: "):
                        data = line[6:]  # Убираем "data: "
                        if data.strip() == "[DONE]":
                            break
                            
                        try:
                            chunk_data = json.loads(data)
                            content = self._extract_content_from_chunk(chunk_data)
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Custom streaming VLM error: {e}")
            yield f"Ошибка анализа: {str(e)}"
    
    def _create_openai_payload(self, image_b64: str, prompt: str) -> Dict[str, Any]:
        """Создать payload в формате OpenAI"""
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            "stream": True,
            "temperature": self.config.get("temperature", 0.7),
            "max_tokens": self.config.get("max_tokens", 2048)
        }
    
    def _create_anthropic_payload(self, image_b64: str, prompt: str) -> Dict[str, Any]:
        """Создать payload в формате Anthropic"""
        return {
            "model": self.model,
            "max_tokens": self.config.get("max_tokens", 2048),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_b64
                            }
                        }
                    ]
                }
            ],
            "stream": True
        }
    
    def _create_custom_payload(self, image_b64: str, prompt: str) -> Dict[str, Any]:
        """Создать кастомный payload"""
        return {
            "model": self.model,
            "prompt": prompt,
            "image": image_b64,
            "stream": True,
            "temperature": self.config.get("temperature", 0.7),
            "max_tokens": self.config.get("max_tokens", 2048)
        }
    
    def _extract_content_from_chunk(self, chunk_data: Dict[str, Any]) -> str:
        """Извлечь контент из chunk данных"""
        # Пытаемся найти контент в различных форматах
        if "choices" in chunk_data and chunk_data["choices"]:
            delta = chunk_data["choices"][0].get("delta", {})
            return delta.get("content", "")
        elif "content" in chunk_data:
            return chunk_data["content"]
        elif "text" in chunk_data:
            return chunk_data["text"]
        return ""
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Конвертировать изображение в base64"""
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode()

class StreamingVLMFactory:
    """Фабрика для создания потоковых VLM"""
    
    @staticmethod
    def create_streaming_vlm(config: Dict[str, Any]) -> StreamingVLMBase:
        """Создать потоковый VLM на основе конфигурации"""
        provider = config.get("provider", "groq")
        
        if provider == "groq":
            return StreamingGroqVLM(config)
        elif provider == "openai":
            return StreamingOpenAIVLM(config)
        elif provider == "custom_endpoint":
            return StreamingCustomVLM(config)
        else:
            # Fallback к обычному VLM
            logger.warning(f"Streaming not supported for provider {provider}, using regular VLM")
            return None

# Утилиты для интеграции с существующими VLM
class StreamingVLMAdapter:
    """Адаптер для интеграции потоковых VLM с существующими компонентами"""
    
    def __init__(self, streaming_vlm: StreamingVLMBase):
        self.streaming_vlm = streaming_vlm
        self._current_analysis = None
    
    async def analyze_image_streaming(
        self, 
        image: Image.Image, 
        prompt: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """Потоковый анализ изображения"""
        self._current_analysis = asyncio.create_task(
            self._run_streaming_analysis(image, prompt, **kwargs)
        )
        
        try:
            async for chunk in self.streaming_vlm.analyze_image_streaming(image, prompt, **kwargs):
                yield chunk
        finally:
            if self._current_analysis:
                self._current_analysis.cancel()
                self._current_analysis = None
    
    async def _run_streaming_analysis(self, image: Image.Image, prompt: str, **kwargs):
        """Запустить потоковый анализ"""
        try:
            async for chunk in self.streaming_vlm.analyze_image_streaming(image, prompt, **kwargs):
                # Здесь можно добавить дополнительную обработку
                pass
        except asyncio.CancelledError:
            pass
    
    async def cancel_current_analysis(self) -> None:
        """Отменить текущий анализ"""
        if self._current_analysis:
            self._current_analysis.cancel()
            self._current_analysis = None
        await self.streaming_vlm.cancel_analysis()
