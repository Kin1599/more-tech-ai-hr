from __future__ import annotations

import os
import asyncio
from typing import Any, AsyncIterator, List, Union
import json

import httpx
import openai
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

class GroqLLM(LLM):
    
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "qwen/qwen3-32b",
        base_url: str = "https://api.groq.com/openai/v1",
        temperature: float = 0.7,
        tool_choice: ToolChoice = "auto",
        max_completion_tokens: int | None = None,
        max_tokens: int | None = None,  # Для обратной совместимости
        frequency_penalty: float | None = None,
        presence_penalty: float | None = None,
        seed: int | None = None,
        stop: str | List[str] | None = None,
    ) -> None:
        """Initialize the Groq LLM plugin.

        Args:
            api_key (Optional[str], optional): Groq API key. Defaults to None.
            model (str): The model to use for the LLM plugin. Defaults to "qwen/qwen3-32b".
            base_url (str): The base URL for the Groq API. Defaults to "https://api.groq.com/openai/v1".
            temperature (float): The temperature to use for the LLM plugin. Defaults to 0.7.
            tool_choice (ToolChoice): The tool choice to use for the LLM plugin. Defaults to "auto".
            max_completion_tokens (Optional[int], optional): The maximum completion tokens to use for the LLM plugin. Defaults to None.
            max_tokens (Optional[int], optional): Deprecated in favor of max_completion_tokens. Defaults to None.
            frequency_penalty (Optional[float], optional): Frequency penalty parameter. Defaults to None.
            presence_penalty (Optional[float], optional): Presence penalty parameter. Defaults to None.
            seed (Optional[int], optional): Seed for deterministic sampling. Defaults to None.
            stop (Optional[Union[str, List[str]]], optional): Stop sequences. Defaults to None.
        """
        super().__init__()
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key must be provided either through api_key parameter or GROQ_API_KEY environment variable")
        
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.tool_choice = tool_choice
        self.max_completion_tokens = max_completion_tokens or max_tokens
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.seed = seed
        self.stop = stop
        self._cancelled = False
        
        self._client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url,
            max_retries=0,
            http_client=httpx.AsyncClient(
                timeout=httpx.Timeout(connect=15.0, read=10.0, write=10.0, pool=10.0),
                follow_redirects=True,
                limits=httpx.Limits(
                    max_connections=50,
                    max_keepalive_connections=50,
                    keepalive_expiry=120,
                ),
            ),
        )

    @staticmethod
    def create(
        *,
        api_key: str | None = None,
        model: str = "qwen/qwen3-32b",
        base_url: str = "https://api.groq.com/openai/v1",
        temperature: float = 0.7,
        tool_choice: ToolChoice = "auto",
        max_completion_tokens: int | None = None,
        **kwargs: Any
    ) -> "GroqLLM":
        """
        Create a new instance of Groq LLM.
        
        This method provides a clean factory method for creating GroqLLM instances.
        """
        return GroqLLM(
            api_key=api_key,
            model=model,
            base_url=base_url,
            temperature=temperature,
            tool_choice=tool_choice,
            max_completion_tokens=max_completion_tokens,
            **kwargs
        )

    def get_supported_models(self) -> list[str]:
        """Get list of supported Groq LLM models"""
        return [
            # Mixtral модели
            "mixtral-8x7b-32768",
            
            # Gemma модели 
            "gemma-7b-it",
            "gemma2-9b-it",
        ]

    def is_model_supported(self, model: str) -> bool:
        """Check if a model is supported by Groq"""
        return model in self.get_supported_models()

    async def chat(
        self,
        messages: ChatContext,
        tools: list[FunctionTool] | None = None,
        **kwargs: Any
    ) -> AsyncIterator[LLMResponse]:
        """
        Implement chat functionality using Groq's chat completion API
        
        Args:
            messages: ChatContext containing conversation history
            tools: Optional list of function tools available to the model
            **kwargs: Additional arguments passed to the Groq API
            
        Yields:
            LLMResponse objects containing the model's responses
        """
        self._cancelled = False
        
        def _format_content(content: Union[str, List[ChatContent]]):
            if isinstance(content, str):
                return content

            formatted_parts = []
            for part in content:
                if isinstance(part, str):
                    formatted_parts.append({"type": "text", "text": part})
                elif isinstance(part, ImageContent):
                    # Проверяем, поддерживает ли модель изображения
                    if "vision" in self.model.lower() or "llava" in self.model.lower():
                        image_url_data = {"url": part.to_data_url()}
                        if part.inference_detail != "auto":
                            image_url_data["detail"] = part.inference_detail
                        formatted_parts.append(
                            {
                                "type": "image_url",
                                "image_url": image_url_data,
                            }
                        )
                    else:
                        # Для моделей без поддержки изображений игнорируем изображения
                        print(f"Warning: Model {self.model} does not support images, skipping image content")
            return formatted_parts

        completion_params = {
            "model": self.model,
            "messages": [
                {
                    "role": msg.role.value,
                    "content": _format_content(msg.content),
                    **({"name": msg.name} if hasattr(msg, "name") and msg.name else {}),
                }
                if isinstance(msg, ChatMessage)
                else {
                    "role": "assistant",
                    "content": None,
                    "function_call": {"name": msg.name, "arguments": msg.arguments},
                }
                if isinstance(msg, FunctionCall)
                else {
                    "role": "function",
                    "name": msg.name,
                    "content": msg.output,
                }
                if isinstance(msg, FunctionCallOutput)
                else None
                for msg in messages.items
                if msg is not None
            ],
            "temperature": self.temperature,
            "stream": True,
        }
        
        # Добавляем дополнительные параметры если они заданы
        if self.max_completion_tokens is not None:
            completion_params["max_completion_tokens"] = self.max_completion_tokens
            
        if self.frequency_penalty is not None:
            completion_params["frequency_penalty"] = self.frequency_penalty
            
        if self.presence_penalty is not None:
            completion_params["presence_penalty"] = self.presence_penalty
            
        if self.seed is not None:
            completion_params["seed"] = self.seed
            
        if self.stop is not None:
            completion_params["stop"] = self.stop

        # Обработка инструментов/функций
        if tools:
            formatted_tools = []
            for tool in tools:
                if not is_function_tool(tool):
                    continue
                try:
                    tool_schema = build_openai_schema(tool)
                    formatted_tools.append(tool_schema)
                except Exception as e:
                    self.emit("error", f"Failed to format tool {tool}: {e}")
                    continue
            
            if formatted_tools:
                # Groq использует новый формат tools вместо functions
                completion_params["tools"] = [
                    {"type": "function", "function": tool["function"]}
                    for tool in formatted_tools
                ]
                completion_params["tool_choice"] = self.tool_choice

        # Добавляем дополнительные параметры из kwargs
        completion_params.update(kwargs)
        
        try:
            response_stream = await self._client.chat.completions.create(**completion_params)
            
            current_content = ""
            current_tool_calls = {}

            async for chunk in response_stream:
                if self._cancelled:
                    break
                
                if not chunk.choices:
                    continue
                    
                delta = chunk.choices[0].delta
                
                # Обработка tool calls (новый формат)
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        call_id = tool_call.id
                        if call_id not in current_tool_calls:
                            current_tool_calls[call_id] = {
                                "id": call_id,
                                "type": tool_call.type,
                                "function": {
                                    "name": tool_call.function.name or "",
                                    "arguments": tool_call.function.arguments or ""
                                }
                            }
                        else:
                            if tool_call.function.name:
                                current_tool_calls[call_id]["function"]["name"] += tool_call.function.name
                            if tool_call.function.arguments:
                                current_tool_calls[call_id]["function"]["arguments"] += tool_call.function.arguments
                
                # Обработка устаревшего формата function_call для совместимости
                elif delta.function_call:
                    call_id = "legacy_function_call"
                    if call_id not in current_tool_calls:
                        current_tool_calls[call_id] = {
                            "type": "function",
                            "function": {
                                "name": delta.function_call.name or "",
                                "arguments": delta.function_call.arguments or ""
                            }
                        }
                    else:
                        if delta.function_call.name:
                            current_tool_calls[call_id]["function"]["name"] += delta.function_call.name
                        if delta.function_call.arguments:
                            current_tool_calls[call_id]["function"]["arguments"] += delta.function_call.arguments
                
                # Обработка текстового контента
                elif delta.content is not None:
                    current_content = delta.content
                    yield LLMResponse(
                        content=current_content,
                        role=ChatRole.ASSISTANT,
                        metadata={"model": self.model, "provider": "groq"}
                    )
                
                # Проверяем завершение tool calls
                finish_reason = chunk.choices[0].finish_reason
                if finish_reason == "tool_calls" or finish_reason == "function_call":
                    for call_id, tool_call in current_tool_calls.items():
                        try:
                            args = json.loads(tool_call["function"]["arguments"])
                            tool_call["function"]["arguments"] = args
                        except json.JSONDecodeError:
                            self.emit("error", f"Failed to parse function arguments: {tool_call['function']['arguments']}")
                            tool_call["function"]["arguments"] = {}
                        
                        # Отправляем в старом формате для совместимости
                        yield LLMResponse(
                            content="",
                            role=ChatRole.ASSISTANT,
                            metadata={
                                "function_call": tool_call["function"],
                                "tool_call": tool_call,
                                "model": self.model,
                                "provider": "groq"
                            }
                        )
                    current_tool_calls = {}

        except asyncio.CancelledError:
            self._cancelled = True
            raise
        except Exception as e:
            if not self._cancelled:
                error_msg = f"Groq LLM error: {str(e)}"
                self.emit("error", error_msg)
            raise

    async def cancel_current_generation(self) -> None:
        self._cancelled = True

    async def aclose(self) -> None:
        """Cleanup resources by closing the HTTP client"""
        await self.cancel_current_generation()
        if self._client:
            await self._client.close()


# Обратная совместимость - создаем алиас для существующего кода
class OpenAILLM(GroqLLM):
    """
    Backward compatibility alias for GroqLLM.
    Allows existing OpenAILLM code to work with Groq API by simply changing the base_url.
    """
    
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "qwen/qwen3-32b",
        base_url: str | None = None,
        temperature: float = 0.7,
        tool_choice: ToolChoice = "auto",
        max_completion_tokens: int | None = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize OpenAILLM with Groq support.
        
        When base_url points to Groq API, this will use Groq's chat completion service.
        """
        
        # Определяем, используется ли Groq API
        is_groq = base_url and "groq.com" in base_url
        
        if is_groq:
            # Для Groq используем GROQ_API_KEY если не указан api_key
            if not api_key:
                api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("Groq API key must be provided either through api_key parameter or GROQ_API_KEY environment variable")
                
            # Устанавливаем правильный base_url для Groq
            if not base_url.endswith("/v1"):
                base_url = base_url.rstrip("/") + "/v1"
        else:
            # Для OpenAI используем OPENAI_API_KEY если не указан api_key
            if not api_key:
                api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key must be provided either through api_key parameter or OPENAI_API_KEY environment variable")
            
            # Устанавливаем правильный base_url для OpenAI
            if not base_url:
                base_url = "https://api.openai.com/v1"
        
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url,
            temperature=temperature,
            tool_choice=tool_choice,
            max_completion_tokens=max_completion_tokens,
            **kwargs
        )
        
        # Сохраняем информацию о том, используется ли Groq
        self._is_groq = is_groq
        
    @staticmethod
    def azure(*args, **kwargs):
        """Azure OpenAI не поддерживается в Groq версии"""
        raise NotImplementedError("Azure OpenAI is not supported when using Groq API")
