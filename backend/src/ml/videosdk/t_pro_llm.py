"""
Интеграция с моделью T-pro-it-1.0 от T-Tech для русскоязычных интервью.

T-pro-it-1.0 - это модель на базе Qwen 2.5, специально обученная для работы с русским языком.
Показывает отличные результаты на русских бенчмарках: MERA (0.629), MaMuRaMu (0.841), ruMMLU-PRO (0.665).

Источник: https://huggingface.co/t-tech/T-pro-it-1.0
"""

from __future__ import annotations

import os
import asyncio
from typing import Any, AsyncIterator, List, Union, Optional
import json
import logging

import httpx
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from videosdk.agents import (
    LLM,
    LLMResponse,
    ChatContext,
    ChatRole,
    ChatMessage,
    FunctionCall,
    FunctionCallOutput,
    ToolChoice,
    FunctionTool,
    is_function_tool,
    build_openai_schema,
)
from videosdk.agents.llm.chat_context import ChatContent, ImageContent

logger = logging.getLogger(__name__)

class TProLLM(LLM):
    """LLM на базе модели T-pro-it-1.0 от T-Tech для русскоязычных интервью"""
    
    def __init__(
        self,
        *,
        model_name: str = "t-tech/T-pro-it-1.0",
        device: str = "auto",
        torch_dtype: str = "auto",
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.8,
        top_k: int = 70,
        repetition_penalty: float = 1.05,
        do_sample: bool = True,
        cache_dir: Optional[str] = None,
        trust_remote_code: bool = True,
        **kwargs
    ) -> None:
        """Initialize the T-pro LLM plugin.

        Args:
            model_name (str): Название модели T-pro. Defaults to "t-tech/T-pro-it-1.0".
            device (str): Устройство для загрузки модели. Defaults to "auto".
            torch_dtype (str): Тип данных PyTorch. Defaults to "auto".
            max_new_tokens (int): Максимальное количество новых токенов. Defaults to 512.
            temperature (float): Температура для генерации. Defaults to 0.7.
            top_p (float): Top-p параметр. Defaults to 0.8.
            top_k (int): Top-k параметр. Defaults to 70.
            repetition_penalty (float): Штраф за повторения. Defaults to 1.05.
            do_sample (bool): Использовать сэмплирование. Defaults to True.
            cache_dir (Optional[str]): Директория для кэша модели.
            trust_remote_code (bool): Доверять удаленному коду. Defaults to True.
        """
        super().__init__()
        
        self.model_name = model_name
        self.device = device
        self.torch_dtype = torch_dtype
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.repetition_penalty = repetition_penalty
        self.do_sample = do_sample
        self.cache_dir = cache_dir
        self.trust_remote_code = trust_remote_code
        self._cancelled = False
        
        # Инициализация модели и токенизатора
        self._model = None
        self._tokenizer = None
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
        
        # Системный промпт для T-pro
        self.system_prompt = (
            "Ты T-pro, виртуальный ассистент в Т-Технологии. "
            "Твоя задача - быть полезным диалоговым ассистентом. "
            "Отвечай на русском языке, будь вежливым и профессиональным."
        )
        
        logger.info(f"Инициализирован T-pro LLM: {model_name}")
    
    async def _ensure_initialized(self) -> None:
        """Инициализация модели с блокировкой"""
        if self._initialized:
            return
            
        async with self._initialization_lock:
            if self._initialized:
                return
                
            try:
                logger.info(f"Загружаем модель T-pro: {self.model_name}")
                
                # Загружаем токенизатор
                self._tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    cache_dir=self.cache_dir,
                    trust_remote_code=self.trust_remote_code
                )
                
                # Загружаем модель
                self._model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=self.torch_dtype,
                    device_map=self.device,
                    cache_dir=self.cache_dir,
                    trust_remote_code=self.trust_remote_code,
                    low_cpu_mem_usage=True
                )
                
                # Устанавливаем seed для воспроизводимости
                torch.manual_seed(42)
                
                self._initialized = True
                logger.info("Модель T-pro успешно загружена")
                
            except Exception as e:
                logger.error(f"Ошибка загрузки модели T-pro: {e}")
                raise
    
    @staticmethod
    def create(
        *,
        model_name: str = "t-tech/T-pro-it-1.0",
        device: str = "auto",
        torch_dtype: str = "auto",
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs: Any
    ) -> "TProLLM":
        """
        Create a new instance of T-pro LLM.
        
        This method provides a clean factory method for creating TProLLM instances.
        """
        return TProLLM(
            model_name=model_name,
            device=device,
            torch_dtype=torch_dtype,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            **kwargs
        )

    def get_supported_models(self) -> list[str]:
        """Get list of supported T-pro models"""
        return [
            "t-tech/T-pro-it-1.0",
            "t-tech/T-pro-it-1.0-instruct",  # Если будет доступна
        ]

    def is_model_supported(self, model: str) -> bool:
        """Check if a model is supported by T-pro"""
        return model in self.get_supported_models()

    async def chat(
        self,
        messages: ChatContext,
        tools: list[FunctionTool] | None = None,
        **kwargs: Any
    ) -> AsyncIterator[LLMResponse]:
        """
        Implement chat functionality using T-pro model
        
        Args:
            messages: ChatContext containing conversation history
            tools: Optional list of function tools available to the model
            **kwargs: Additional arguments passed to the model
            
        Yields:
            LLMResponse objects containing the model's responses
        """
        self._cancelled = False
        
        try:
            await self._ensure_initialized()
            
            # Формируем сообщения для T-pro
            formatted_messages = self._format_messages_for_tpro(messages)
            
            # Применяем chat template
            text = self._tokenizer.apply_chat_template(
                formatted_messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # Токенизируем входной текст
            model_inputs = self._tokenizer([text], return_tensors="pt").to(self._model.device)
            
            # Параметры генерации
            generation_params = {
                "max_new_tokens": self.max_new_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "repetition_penalty": self.repetition_penalty,
                "do_sample": self.do_sample,
                "pad_token_id": self._tokenizer.eos_token_id,
            }
            
            # Добавляем параметры из kwargs
            generation_params.update(kwargs)
            
            # Генерируем ответ потоково
            async for chunk in self._generate_streaming(model_inputs, generation_params):
                if self._cancelled:
                    break
                    
                if chunk:
                    yield LLMResponse(
                        content=chunk,
                        role=ChatRole.ASSISTANT,
                        metadata={
                            "model": self.model_name,
                            "provider": "t-tech",
                            "language": "ru"
                        }
                    )

        except asyncio.CancelledError:
            self._cancelled = True
            raise
        except Exception as e:
            if not self._cancelled:
                error_msg = f"T-pro LLM error: {str(e)}"
                logger.error(error_msg)
                self.emit("error", error_msg)
            raise

    def _format_messages_for_tpro(self, messages: ChatContext) -> List[dict]:
        """Форматировать сообщения для T-pro модели"""
        formatted_messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        for msg in messages.items:
            if isinstance(msg, ChatMessage):
                if msg.role == ChatRole.USER:
                    formatted_messages.append({
                        "role": "user",
                        "content": self._format_content(msg.content)
                    })
                elif msg.role == ChatRole.ASSISTANT:
                    formatted_messages.append({
                        "role": "assistant", 
                        "content": self._format_content(msg.content)
                    })
            elif isinstance(msg, FunctionCall):
                formatted_messages.append({
                    "role": "assistant",
                    "content": f"Вызываю функцию {msg.name} с параметрами: {msg.arguments}"
                })
            elif isinstance(msg, FunctionCallOutput):
                formatted_messages.append({
                    "role": "function",
                    "name": msg.name,
                    "content": msg.output
                })
        
        return formatted_messages

    def _format_content(self, content: Union[str, List[ChatContent]]) -> str:
        """Форматировать контент сообщения"""
        if isinstance(content, str):
            return content
        
        formatted_parts = []
        for part in content:
            if isinstance(part, str):
                formatted_parts.append(part)
            elif isinstance(part, ImageContent):
                # T-pro не поддерживает изображения напрямую
                formatted_parts.append("[Изображение]")
        
        return " ".join(formatted_parts)

    async def _generate_streaming(
        self, 
        model_inputs: dict, 
        generation_params: dict
    ) -> AsyncIterator[str]:
        """Потоковая генерация ответа"""
        try:
            # Для потоковой генерации используем generate с yield
            with torch.no_grad():
                generated_ids = self._model.generate(
                    **model_inputs,
                    **generation_params,
                    return_dict_in_generate=True,
                    output_scores=True
                )
            
            # Извлекаем только новые токены
            input_length = model_inputs.input_ids.shape[1]
            new_tokens = generated_ids.sequences[0][input_length:]
            
            # Декодируем токены потоково
            for i in range(len(new_tokens)):
                if self._cancelled:
                    break
                    
                # Декодируем токен
                token_text = self._tokenizer.decode([new_tokens[i]], skip_special_tokens=True)
                
                if token_text:
                    yield token_text
                    
                # Небольшая задержка для имитации потокового получения
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Ошибка потоковой генерации: {e}")
            yield f"Ошибка генерации: {str(e)}"

    async def cancel_current_generation(self) -> None:
        """Отменить текущую генерацию"""
        self._cancelled = True

    async def aclose(self) -> None:
        """Cleanup resources"""
        await self.cancel_current_generation()
        
        # Очищаем модель из памяти
        if self._model is not None:
            del self._model
            self._model = None
            
        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None
            
        # Очищаем кэш CUDA если доступен
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        self._initialized = False
        logger.info("T-pro LLM ресурсы очищены")

    def get_model_info(self) -> dict:
        """Получить информацию о модели"""
        return {
            "name": self.model_name,
            "provider": "t-tech",
            "language": "ru",
            "base_model": "Qwen 2.5",
            "parameters": "32.8B",
            "benchmarks": {
                "MERA": 0.629,
                "MaMuRaMu": 0.841,
                "ruMMLU-PRO": 0.665,
                "ruGSM8K": 0.941,
                "ruMATH": 0.776,
                "ruMBPP": 0.805,
                "Arena-Hard-Ru": 90.17,
                "MT Bench Ru": 8.7,
                "Alpaca Eval Ru": 47.61
            },
            "initialized": self._initialized
        }

    def set_system_prompt(self, prompt: str) -> None:
        """Установить системный промпт"""
        self.system_prompt = prompt
        logger.info(f"Системный промпт T-pro обновлен: {prompt[:100]}...")

    def get_system_prompt(self) -> str:
        """Получить текущий системный промпт"""
        return self.system_prompt


class TProLLMWithVLLM(LLM):
    """T-pro LLM с использованием VLLM для оптимизации производительности"""
    
    def __init__(
        self,
        *,
        model_name: str = "t-tech/T-pro-it-1.0",
        max_model_len: int = 8192,
        temperature: float = 0.7,
        top_p: float = 0.8,
        top_k: int = 70,
        repetition_penalty: float = 1.05,
        **kwargs
    ) -> None:
        """Initialize T-pro LLM with VLLM backend"""
        super().__init__()
        
        self.model_name = model_name
        self.max_model_len = max_model_len
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.repetition_penalty = repetition_penalty
        self._cancelled = False
        
        # VLLM компоненты
        self._llm = None
        self._tokenizer = None
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
        
        # Системный промпт
        self.system_prompt = (
            "Ты T-pro, виртуальный ассистент в Т-Технологии. "
            "Твоя задача - быть полезным диалоговым ассистентом. "
            "Отвечай на русском языке, будь вежливым и профессиональным."
        )
        
        logger.info(f"Инициализирован T-pro LLM с VLLM: {model_name}")
    
    async def _ensure_initialized(self) -> None:
        """Инициализация VLLM модели"""
        if self._initialized:
            return
            
        async with self._initialization_lock:
            if self._initialized:
                return
                
            try:
                from vllm import LLM, SamplingParams
                from transformers import AutoTokenizer
                
                logger.info(f"Загружаем T-pro модель с VLLM: {self.model_name}")
                
                # Загружаем токенизатор
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                
                # Загружаем VLLM модель
                self._llm = LLM(
                    model=self.model_name,
                    max_model_len=self.max_model_len,
                    trust_remote_code=True
                )
                
                self._initialized = True
                logger.info("T-pro модель с VLLM успешно загружена")
                
            except ImportError:
                raise ImportError("VLLM не установлен. Установите: pip install vllm")
            except Exception as e:
                logger.error(f"Ошибка загрузки T-pro с VLLM: {e}")
                raise
    
    async def chat(
        self,
        messages: ChatContext,
        tools: list[FunctionTool] | None = None,
        **kwargs: Any
    ) -> AsyncIterator[LLMResponse]:
        """Chat с использованием VLLM"""
        self._cancelled = False
        
        try:
            await self._ensure_initialized()
            
            # Формируем сообщения
            formatted_messages = self._format_messages_for_tpro(messages)
            
            # Применяем chat template
            prompt_token_ids = self._tokenizer.apply_chat_template(
                formatted_messages, 
                add_generation_prompt=True
            )
            
            # Параметры сэмплирования
            sampling_params = {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "repetition_penalty": self.repetition_penalty,
                "max_tokens": kwargs.get("max_tokens", 512)
            }
            
            # Генерируем ответ
            outputs = self._llm.generate(
                prompt_token_ids=prompt_token_ids,
                sampling_params=sampling_params
            )
            
            generated_text = outputs[0].outputs[0].text
            
            # Возвращаем как единый чанк (VLLM не поддерживает потоковую генерацию)
            yield LLMResponse(
                content=generated_text,
                role=ChatRole.ASSISTANT,
                metadata={
                    "model": self.model_name,
                    "provider": "t-tech-vllm",
                    "language": "ru"
                }
            )
            
        except Exception as e:
            if not self._cancelled:
                error_msg = f"T-pro VLLM error: {str(e)}"
                logger.error(error_msg)
                self.emit("error", error_msg)
            raise
    
    def _format_messages_for_tpro(self, messages: ChatContext) -> List[dict]:
        """Форматировать сообщения для T-pro модели"""
        formatted_messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        for msg in messages.items:
            if isinstance(msg, ChatMessage):
                if msg.role == ChatRole.USER:
                    formatted_messages.append({
                        "role": "user",
                        "content": str(msg.content)
                    })
                elif msg.role == ChatRole.ASSISTANT:
                    formatted_messages.append({
                        "role": "assistant", 
                        "content": str(msg.content)
                    })
        
        return formatted_messages
    
    async def cancel_current_generation(self) -> None:
        """Отменить текущую генерацию"""
        self._cancelled = True
    
    async def aclose(self) -> None:
        """Cleanup resources"""
        await self.cancel_current_generation()
        
        if self._llm is not None:
            del self._llm
            self._llm = None
            
        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None
            
        self._initialized = False
        logger.info("T-pro VLLM ресурсы очищены")


# Утилиты для интеграции
def create_tpro_llm(
    use_vllm: bool = False,
    model_name: str = "t-tech/T-pro-it-1.0",
    **kwargs
) -> Union[TProLLM, TProLLMWithVLLM]:
    """Создать экземпляр T-pro LLM"""
    if use_vllm:
        return TProLLMWithVLLM(model_name=model_name, **kwargs)
    else:
        return TProLLM(model_name=model_name, **kwargs)

def get_tpro_benchmarks() -> dict:
    """Получить результаты бенчмарков T-pro"""
    return {
        "proprietary_models": {
            "MERA": {"T-pro-it-1.0": 0.629, "GPT-4o": 0.642, "GigaChat Max": 0.588},
            "MaMuRaMu": {"T-pro-it-1.0": 0.841, "GPT-4o": 0.874, "GigaChat Max": 0.824},
            "ruMMLU-PRO": {"T-pro-it-1.0": 0.665, "GPT-4o": 0.713, "GigaChat Max": 0.535},
            "ruGSM8K": {"T-pro-it-1.0": 0.941, "GPT-4o": 0.931, "GigaChat Max": 0.892},
            "ruMATH": {"T-pro-it-1.0": 0.776, "GPT-4o": 0.771, "GigaChat Max": 0.589},
            "ruMBPP": {"T-pro-it-1.0": 0.805, "GPT-4o": 0.802, "GigaChat Max": 0.626},
            "Arena-Hard-Ru": {"T-pro-it-1.0": 90.17, "GPT-4o": 84.87},
            "MT Bench Ru": {"T-pro-it-1.0": 8.7, "GPT-4o": 8.706, "GigaChat Max": 8.53},
            "Alpaca Eval Ru": {"T-pro-it-1.0": 47.61, "GPT-4o": 50, "GigaChat Max": 38.13}
        },
        "open_source_models": {
            "MERA": {"T-pro-it-1.0": 0.629, "Qwen-2.5-32B": 0.578, "RuAdapt-Qwen-32B": 0.615},
            "MaMuRaMu": {"T-pro-it-1.0": 0.841, "Qwen-2.5-32B": 0.824, "RuAdapt-Qwen-32B": 0.812},
            "ruMMLU-PRO": {"T-pro-it-1.0": 0.665, "Qwen-2.5-32B": 0.637, "RuAdapt-Qwen-32B": 0.631},
            "ruGSM8K": {"T-pro-it-1.0": 0.941, "Qwen-2.5-32B": 0.926, "RuAdapt-Qwen-32B": 0.923},
            "ruMATH": {"T-pro-it-1.0": 0.776, "Qwen-2.5-32B": 0.727, "RuAdapt-Qwen-32B": 0.742},
            "ruMBPP": {"T-pro-it-1.0": 0.805, "Qwen-2.5-32B": 0.825, "RuAdapt-Qwen-32B": 0.813},
            "Arena-Hard-Ru": {"T-pro-it-1.0": 90.17, "Qwen-2.5-32B": 74.54, "RuAdapt-Qwen-32B": 80.23},
            "MT Bench Ru": {"T-pro-it-1.0": 8.7, "Qwen-2.5-32B": 8.15, "RuAdapt-Qwen-32B": 8.39},
            "Alpaca Eval Ru": {"T-pro-it-1.0": 47.61, "Qwen-2.5-32B": 35.01, "RuAdapt-Qwen-32B": 43.15}
        }
    }
