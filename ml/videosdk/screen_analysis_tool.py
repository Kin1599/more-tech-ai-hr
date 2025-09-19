"""
Screen Analysis Tool для интеграции Vision моделей в LLM чатботы.

Предоставляет функциональность анализа экрана через Vision модели
как инструмент (tool) для Language Models.
"""

import logging
from typing import Optional, Dict, Any, Callable
from collections import deque
import asyncio
import json
from PIL import Image
import io
import base64

logger = logging.getLogger(__name__)

class ScreenAnalysisTool:
    """
    Инструмент для анализа экрана с использованием Vision моделей.
    
    Предоставляет унифицированный интерфейс для анализа скриншотов
    различными Vision провайдерами (Gemini, OpenAI, Anthropic, etc.).
    """
    
    def __init__(self, vision_model: Optional[Any] = None):
        """
        Инициализация Screen Analysis Tool.
        
        Args:
            vision_model: Экземпляр Vision модели для анализа
        """
        self.vision_model = vision_model
        self.latest_frame = None
        self.frame_queue = deque(maxlen=5)  # Храним последние 5 кадров
        self.analysis_cache = {}  # Кеш для повторных анализов
        self.is_screenshare_active = False
        
    def set_vision_model(self, vision_model: Any) -> None:
        """Установить Vision модель для анализа."""
        self.vision_model = vision_model
        logger.info("Vision model set for screen analysis")
    
    def update_frame(self, frame: Any) -> None:
        """
        Обновить текущий кадр экрана.
        
        Args:
            frame: Кадр от VideoSDK (VideoFrame объект)
        """
        self.latest_frame = frame
        self.frame_queue.append(frame)
        self.is_screenshare_active = True
        
        # Очищаем кеш при новом кадре
        self.analysis_cache.clear()
        
        logger.debug("Screen frame updated")
    
    def set_screenshare_status(self, active: bool) -> None:
        """Установить статус демонстрации экрана."""
        self.is_screenshare_active = active
        if not active:
            self.latest_frame = None
            self.frame_queue.clear()
            self.analysis_cache.clear()
        logger.info(f"Screenshare status: {'active' if active else 'inactive'}")
    
    def _frame_to_image(self, frame: Any) -> Optional[Image.Image]:
        """
        Конвертировать VideoFrame в PIL Image.
        
        Args:
            frame: VideoFrame объект от VideoSDK
            
        Returns:
            PIL Image или None при ошибке
        """
        try:
            if not frame:
                return None
            
            # Конвертируем frame в numpy array и затем в PIL Image
            image_data = frame.to_ndarray(format="rgb24")
            image = Image.fromarray(image_data)
            
            return image
        except Exception as e:
            logger.error(f"Error converting frame to image: {e}")
            return None
    
    async def analyze_screen(
        self, 
        prompt: str = "Проанализируй содержимое экрана и помоги пользователю",
        use_latest: bool = True
    ) -> str:
        """
        Анализировать текущий экран с помощью Vision модели.
        
        Args:
            prompt: Запрос для анализа экрана
            use_latest: Использовать последний кадр (True) или из очереди (False)
            
        Returns:
            Результат анализа экрана
        """
        try:
            # Проверяем доступность Vision модели
            if not self.vision_model:
                return "❌ Vision модель не настроена для анализа экрана"
            
            # Проверяем наличие активной демонстрации экрана
            if not self.is_screenshare_active:
                return "📺 Демонстрация экрана не активна. Попросите пользователя включить демонстрацию экрана для анализа."
            
            # Получаем кадр для анализа
            frame = self.latest_frame if use_latest else (
                self.frame_queue[-1] if self.frame_queue else None
            )
            
            if not frame:
                return "📷 Нет доступных кадров экрана для анализа"
            
            # Проверяем кеш
            cache_key = f"{prompt}_{id(frame)}"
            if cache_key in self.analysis_cache:
                logger.debug("Using cached analysis result")
                return self.analysis_cache[cache_key]
            
            # Конвертируем кадр в изображение
            image = self._frame_to_image(frame)
            if not image:
                return "🖼️ Ошибка обработки кадра экрана"
            
            # Анализируем с помощью Vision модели
            result = await self._analyze_with_vision_model(image, prompt)
            
            # Кешируем результат
            self.analysis_cache[cache_key] = result
            
            logger.info("Screen analysis completed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Ошибка анализа экрана: {str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}"
    
    async def _analyze_with_vision_model(self, image: Image.Image, prompt: str) -> str:
        """
        Анализ изображения с помощью конкретной Vision модели.
        
        Args:
            image: PIL изображение для анализа
            prompt: Текстовый запрос
            
        Returns:
            Результат анализа
        """
        try:
            # Определяем тип Vision модели и используем соответствующий метод
            
            # Google Gemini
            if hasattr(self.vision_model, 'generate_content'):
                logger.debug("Using Google Gemini Vision")
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.vision_model.generate_content([
                        f"🎯 Анализ экрана для интервью: {prompt}\n\n"
                        "Контекст: Ты помогаешь кандидату во время интервью, анализируя содержимое его экрана. "
                        "Фокусируйся на релевантных элементах UI, коде, документах или приложениях. "
                        "Давай конкретные и полезные советы.",
                        image
                    ])
                )
                return response.text
            
            # OpenAI Vision (через обертку)
            elif hasattr(self.vision_model, 'analyze_image'):
                logger.debug("Using wrapped Vision model (OpenAI/Anthropic/etc.)")
                return await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.vision_model.analyze_image,
                    image,
                    f"🎯 Анализ экрана для интервью: {prompt}\n\n"
                    "Контекст: Ты помогаешь кандидату во время интервью, анализируя содержимое его экрана. "
                    "Фокусируйся на релевантных элементах UI, коде, документах или приложениях. "
                    "Давай конкретные и полезные советы."
                )
            
            # Fallback для неизвестных моделей
            else:
                logger.warning("Unknown vision model type, attempting generic analysis")
                return "🤖 Vision модель настроена, но не удается определить тип для анализа экрана"
                
        except Exception as e:
            logger.error(f"Vision model analysis error: {e}")
            raise
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Получить определение инструмента для интеграции с LLM.
        
        Returns:
            Словарь с определением инструмента в формате OpenAI Function Calling
        """
        return {
            "type": "function",
            "function": {
                "name": "analyze_screen",
                "description": (
                    "Анализирует содержимое демонстрации экрана пользователя с помощью Vision модели. "
                    "Используй этот инструмент когда пользователь:\n"
                    "- Спрашивает о том, что видно на экране\n"
                    "- Просит помочь с интерфейсом приложения\n"
                    "- Нуждается в объяснении кода или документов\n"
                    "- Показывает ошибки или проблемы\n"
                    "- Демонстрирует свою работу"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": (
                                "Специфический запрос для анализа экрана. Например: "
                                "'Объясни этот код', 'Помоги с интерфейсом', "
                                "'Что означает эта ошибка', 'Проанализируй диаграмму'"
                            )
                        },
                        "focus_area": {
                            "type": "string",
                            "enum": ["code", "ui", "document", "error", "general"],
                            "description": "Область фокуса для анализа"
                        }
                    },
                    "required": ["prompt"]
                }
            }
        }
    
    async def handle_tool_call(self, tool_call: Dict[str, Any]) -> str:
        """
        Обработать вызов инструмента от LLM.
        
        Args:
            tool_call: Словарь с параметрами вызова инструмента
            
        Returns:
            Результат анализа экрана
        """
        try:
            # Извлекаем параметры
            if isinstance(tool_call.get("arguments"), str):
                arguments = json.loads(tool_call["arguments"])
            else:
                arguments = tool_call.get("arguments", {})
            
            prompt = arguments.get("prompt", "Проанализируй содержимое экрана")
            focus_area = arguments.get("focus_area", "general")
            
            # Адаптируем промпт под область фокуса
            focused_prompt = self._adapt_prompt_for_focus(prompt, focus_area)
            
            # Выполняем анализ
            result = await self.analyze_screen(focused_prompt)
            
            return result
            
        except Exception as e:
            error_msg = f"Ошибка обработки tool call: {str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}"
    
    def _adapt_prompt_for_focus(self, prompt: str, focus_area: str) -> str:
        """Адаптировать промпт под область фокуса."""
        focus_instructions = {
            "code": "Фокусируйся на анализе кода: синтаксис, логика, потенциальные ошибки, улучшения.",
            "ui": "Фокусируйся на элементах интерфейса: кнопки, меню, навигация, UX.",
            "document": "Фокусируйся на содержимом документа: текст, структура, ключевые моменты.",
            "error": "Фокусируйся на ошибках: диагностика, причины, решения.",
            "general": "Дай общий анализ содержимого экрана."
        }
        
        instruction = focus_instructions.get(focus_area, focus_instructions["general"])
        return f"{prompt}\n\nИнструкция: {instruction}"
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получить статус Screen Analysis Tool.
        
        Returns:
            Словарь со статусной информацией
        """
        return {
            "vision_model_available": self.vision_model is not None,
            "screenshare_active": self.is_screenshare_active,
            "latest_frame_available": self.latest_frame is not None,
            "frames_in_queue": len(self.frame_queue),
            "cached_analyses": len(self.analysis_cache)
        }


def create_screen_analysis_tool(vision_model: Optional[Any] = None) -> ScreenAnalysisTool:
    """
    Создать экземпляр Screen Analysis Tool.
    
    Args:
        vision_model: Vision модель для анализа
        
    Returns:
        Настроенный ScreenAnalysisTool
    """
    tool = ScreenAnalysisTool(vision_model)
    logger.info("Screen Analysis Tool created")
    return tool


def integrate_with_langchain_tools(screen_tool: ScreenAnalysisTool) -> Callable:
    """
    Создать LangChain совместимую функцию для анализа экрана.
    
    Args:
        screen_tool: Экземпляр ScreenAnalysisTool
        
    Returns:
        Функция для использования в LangChain
    """
    async def analyze_screen_langchain(prompt: str, focus_area: str = "general") -> str:
        """LangChain совместимая функция анализа экрана."""
        return await screen_tool.analyze_screen(
            screen_tool._adapt_prompt_for_focus(prompt, focus_area)
        )
    
    # Добавляем метаданные для LangChain
    analyze_screen_langchain.__name__ = "analyze_screen"
    analyze_screen_langchain.__doc__ = screen_tool.get_tool_definition()["function"]["description"]
    
    return analyze_screen_langchain


# Предустановленные промпты для разных сценариев
SCREEN_ANALYSIS_PROMPTS = {
    "code_review": (
        "Проанализируй код на экране: проверь синтаксис, логику, "
        "потенциальные ошибки и предложи улучшения"
    ),
    "ui_help": (
        "Помоги пользователю разобраться с интерфейсом: "
        "объясни элементы UI, навигацию и возможные действия"
    ),
    "error_diagnosis": (
        "Проанализируй ошибку на экране: определи причину, "
        "предложи способы решения"
    ),
    "document_analysis": (
        "Проанализируй документ на экране: выдели ключевые моменты, "
        "структуру и важную информацию"
    ),
    "interview_help": (
        "Помоги кандидату с тем, что показано на экране в контексте интервью: "
        "дай советы, объяснения и рекомендации"
    ),
    "general_analysis": (
        "Проанализируй содержимое экрана и предоставь полезную информацию "
        "для пользователя"
    )
}
