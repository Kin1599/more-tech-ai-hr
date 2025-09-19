"""
Dynamic Model Switcher для автоматического переключения между LLM и Vision моделями.

Автоматически переключается на Vision модель при включении демонстрации экрана
и обратно на обычную LLM модель при её отключении.
"""

import logging
from typing import Optional, Dict, Any, Callable
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)

class ModelMode(Enum):
    """Режимы работы модели."""
    TEXT_ONLY = "text_only"      # Только текстовая LLM
    MULTIMODAL = "multimodal"    # LLM + Vision для анализа экрана
    HYBRID = "hybrid"            # Автоматическое переключение

class DynamicModelSwitcher:
    """
    Динамическое переключение между текстовой LLM и мультимодальной Vision моделью.
    
    Автоматически переключается на Vision модель при включении демонстрации экрана
    и возвращается к обычной LLM при её отключении.
    """
    
    def __init__(
        self, 
        text_llm: Any,
        vision_llm: Optional[Any] = None,
        screen_analysis_tool: Optional[Any] = None,
        mode: ModelMode = ModelMode.HYBRID
    ):
        """
        Инициализация переключателя моделей.
        
        Args:
            text_llm: Обычная текстовая LLM модель
            vision_llm: Vision LLM модель (опционально)
            screen_analysis_tool: Screen Analysis Tool
            mode: Режим работы
        """
        self.text_llm = text_llm
        self.vision_llm = vision_llm
        self.screen_analysis_tool = screen_analysis_tool
        self.mode = mode
        
        # Состояние
        self.current_model = text_llm
        self.is_screenshare_active = False
        self.switch_callbacks = []
        
        # Статистика переключений
        self.switch_count = 0
        self.text_requests = 0
        self.vision_requests = 0
        
        logger.info(f"Dynamic Model Switcher инициализирован в режиме {mode.value}")
        
    def add_switch_callback(self, callback: Callable[[str, Any], None]) -> None:
        """
        Добавить callback для уведомления о переключении модели.
        
        Args:
            callback: Функция callback(mode_name, model)
        """
        self.switch_callbacks.append(callback)
    
    def set_screenshare_status(self, active: bool) -> None:
        """
        Установить статус демонстрации экрана и переключить модель при необходимости.
        
        Args:
            active: True если демонстрация экрана активна
        """
        old_status = self.is_screenshare_active
        self.is_screenshare_active = active
        
        if old_status != active:
            logger.info(f"Screenshare status changed: {old_status} -> {active}")
            self._switch_model_if_needed()
    
    def _switch_model_if_needed(self) -> None:
        """Переключить модель при необходимости на основе текущего состояния."""
        if self.mode != ModelMode.HYBRID:
            return  # Не переключаем в фиксированных режимах
        
        old_model = self.current_model
        
        if self.is_screenshare_active and self.vision_llm:
            # Переключаемся на Vision модель при активной демонстрации экрана
            self.current_model = self.vision_llm
            mode_name = "MULTIMODAL"
            logger.info("🔄 Переключение на Vision модель (демонстрация экрана активна)")
            
        else:
            # Переключаемся обратно на текстовую LLM
            self.current_model = self.text_llm
            mode_name = "TEXT_ONLY"
            logger.info("🔄 Переключение на текстовую LLM (демонстрация экрана неактивна)")
        
        if old_model != self.current_model:
            self.switch_count += 1
            
            # Уведомляем callbacks о переключении
            for callback in self.switch_callbacks:
                try:
                    callback(mode_name, self.current_model)
                except Exception as e:
                    logger.error(f"Error in switch callback: {e}")
    
    def get_current_model(self) -> Any:
        """
        Получить текущую активную модель.
        
        Returns:
            Текущая LLM модель (текстовая или Vision)
        """
        return self.current_model
    
    def is_vision_mode(self) -> bool:
        """Проверить, активен ли Vision режим."""
        return (
            self.current_model == self.vision_llm and 
            self.vision_llm is not None and
            self.is_screenshare_active
        )
    
    def is_text_mode(self) -> bool:
        """Проверить, активен ли текстовый режим."""
        return self.current_model == self.text_llm
    
    async def process_message(self, message: str, **kwargs) -> str:
        """
        Обработать сообщение с помощью текущей активной модели.
        
        Args:
            message: Текст сообщения
            **kwargs: Дополнительные параметры
            
        Returns:
            Ответ модели
        """
        # Определяем, нужен ли анализ экрана
        needs_screen_analysis = self._needs_screen_analysis(message)
        
        if needs_screen_analysis and self.is_screenshare_active and self.screen_analysis_tool:
            # Используем Vision анализ
            try:
                screen_analysis = await self.screen_analysis_tool.analyze_screen(
                    prompt=f"Контекст вопроса: {message}. Проанализируй экран и помоги пользователю."
                )
                
                # Добавляем результат анализа экрана к исходному сообщению
                enhanced_message = f"{message}\n\nАнализ экрана: {screen_analysis}"
                
                # Обрабатываем через текущую модель
                response = await self._call_model(enhanced_message, **kwargs)
                self.vision_requests += 1
                
                logger.info("✅ Использован Vision анализ для ответа")
                return response
                
            except Exception as e:
                logger.error(f"Error in vision analysis: {e}")
                # Fallback к обычной обработке
        
        # Обычная обработка без Vision анализа
        response = await self._call_model(message, **kwargs)
        self.text_requests += 1
        
        return response
    
    def _needs_screen_analysis(self, message: str) -> bool:
        """
        Определить, нужен ли анализ экрана для данного сообщения.
        
        Args:
            message: Текст сообщения
            
        Returns:
            True если нужен анализ экрана
        """
        screen_keywords = [
            # Прямые указания на экран
            "экран", "screen", "посмотри", "видишь", "смотри",
            "на экране", "показываю", "демонстрирую",
            
            # Код и программирование
            "код", "code", "программа", "скрипт", "функция", "класс",
            "ошибка", "error", "баг", "bug", "исправь", "исправить",
            "алгоритм", "логика", "реализация",
            
            # UI и дизайн
            "интерфейс", "ui", "дизайн", "кнопка", "меню", "форма",
            "layout", "макет", "элемент", "компонент",
            
            # Документы и диаграммы
            "документ", "диаграмма", "схема", "чертеж", "план",
            "архитектура", "структура", "модель",
            
            # Вопросительные слова с контекстом
            "что это", "как это", "почему это", "что делает",
            "как работает", "объясни это", "помоги с этим"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in screen_keywords)
    
    async def _call_model(self, message: str, **kwargs) -> str:
        """
        Вызвать текущую активную модель.
        
        Args:
            message: Сообщение для обработки
            **kwargs: Дополнительные параметры
            
        Returns:
            Ответ модели
        """
        model = self.get_current_model()
        
        # Различные способы вызова модели в зависимости от её типа
        if hasattr(model, 'ask'):
            # LangChainGroqChatbot использует метод ask()
            return model.ask(message)
        elif hasattr(model, 'process_message'):
            return await model.process_message(message, **kwargs)
        elif hasattr(model, 'generate_response'):
            return await model.generate_response(message, **kwargs)
        elif hasattr(model, '__call__'):
            return await model(message, **kwargs)
        else:
            # Fallback для стандартных LLM
            return f"Processed by {type(model).__name__}: {message}"
    
    def force_switch_to_vision(self) -> bool:
        """
        Принудительно переключиться на Vision модель.
        
        Returns:
            True если переключение успешно
        """
        if not self.vision_llm:
            logger.warning("Vision модель недоступна для принудительного переключения")
            return False
        
        old_model = self.current_model
        self.current_model = self.vision_llm
        
        if old_model != self.current_model:
            self.switch_count += 1
            logger.info("🔄 Принудительное переключение на Vision модель")
            
            for callback in self.switch_callbacks:
                try:
                    callback("MULTIMODAL_FORCED", self.current_model)
                except Exception as e:
                    logger.error(f"Error in switch callback: {e}")
        
        return True
    
    def force_switch_to_text(self) -> None:
        """Принудительно переключиться на текстовую модель."""
        old_model = self.current_model
        self.current_model = self.text_llm
        
        if old_model != self.current_model:
            self.switch_count += 1
            logger.info("🔄 Принудительное переключение на текстовую LLM")
            
            for callback in self.switch_callbacks:
                try:
                    callback("TEXT_ONLY_FORCED", self.current_model)
                except Exception as e:
                    logger.error(f"Error in switch callback: {e}")
    
    def set_mode(self, mode: ModelMode) -> None:
        """
        Установить режим работы переключателя.
        
        Args:
            mode: Новый режим работы
        """
        old_mode = self.mode
        self.mode = mode
        
        logger.info(f"Режим переключателя изменен: {old_mode.value} -> {mode.value}")
        
        # Применяем новый режим
        if mode == ModelMode.TEXT_ONLY:
            self.force_switch_to_text()
        elif mode == ModelMode.MULTIMODAL and self.vision_llm:
            self.force_switch_to_vision()
        elif mode == ModelMode.HYBRID:
            self._switch_model_if_needed()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику работы переключателя.
        
        Returns:
            Словарь со статистикой
        """
        return {
            "mode": self.mode.value,
            "current_model_type": "vision" if self.is_vision_mode() else "text",
            "is_screenshare_active": self.is_screenshare_active,
            "switch_count": self.switch_count,
            "text_requests": self.text_requests,
            "vision_requests": self.vision_requests,
            "vision_usage_percentage": (
                (self.vision_requests / (self.text_requests + self.vision_requests)) * 100
                if (self.text_requests + self.vision_requests) > 0 else 0
            ),
            "has_vision_model": self.vision_llm is not None,
            "has_screen_tool": self.screen_analysis_tool is not None
        }
    
    # Методы совместимости с LangChainGroqChatbot
    def ask(self, message: str) -> str:
        """Совместимость с LangChainGroqChatbot - синхронный ask."""
        import asyncio
        try:
            # Запускаем асинхронный метод в новом event loop или текущем
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Если уже в event loop, создаем задачу
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.process_message(message))
                    return future.result()
            else:
                return loop.run_until_complete(self.process_message(message))
        except Exception as e:
            logger.error(f"Error in ask method: {e}")
            # Fallback к прямому вызову текущей модели
            model = self.get_current_model()
            if hasattr(model, 'ask'):
                return model.ask(message)
            return f"Ошибка: {str(e)}"
    
    def is_finished(self) -> bool:
        """Проверить, завершена ли работа с текущей моделью."""
        model = self.get_current_model()
        if hasattr(model, 'is_finished'):
            return model.is_finished()
        return False
    
    def get_history(self) -> list:
        """Получить историю разговора от текущей модели."""
        model = self.get_current_model()
        if hasattr(model, 'get_history'):
            return model.get_history()
        elif hasattr(model, 'conversation_history'):
            return model.conversation_history
        return []
    
    def get_final_feedback(self) -> dict:
        """Получить финальную обратную связь от текущей модели."""
        model = self.get_current_model()
        if hasattr(model, 'get_final_feedback'):
            return model.get_final_feedback()
        return None
    
    def end_interview(self) -> dict:
        """Завершить интервью с текущей моделью."""
        model = self.get_current_model()
        if hasattr(model, 'end_interview'):
            return model.end_interview()
        return None
    
    def reset_statistics(self) -> None:
        """Сбросить статистику."""
        self.switch_count = 0
        self.text_requests = 0
        self.vision_requests = 0
        logger.info("Статистика переключателя сброшена")


def create_dynamic_model_switcher(
    text_llm: Any,
    vision_llm: Optional[Any] = None,
    screen_analysis_tool: Optional[Any] = None,
    mode: ModelMode = ModelMode.HYBRID
) -> DynamicModelSwitcher:
    """
    Создать экземпляр Dynamic Model Switcher.
    
    Args:
        text_llm: Обычная текстовая LLM модель
        vision_llm: Vision LLM модель (опционально)
        screen_analysis_tool: Screen Analysis Tool
        mode: Режим работы
        
    Returns:
        Настроенный DynamicModelSwitcher
    """
    switcher = DynamicModelSwitcher(
        text_llm=text_llm,
        vision_llm=vision_llm,
        screen_analysis_tool=screen_analysis_tool,
        mode=mode
    )
    
    logger.info("Dynamic Model Switcher создан")
    return switcher


class ModelSwitchCallback:
    """Callback класс для обработки переключений моделей."""
    
    def __init__(self, name: str):
        self.name = name
        self.switch_history = []
    
    def __call__(self, mode_name: str, model: Any) -> None:
        """
        Обработать переключение модели.
        
        Args:
            mode_name: Название режима
            model: Новая модель
        """
        import time
        
        switch_info = {
            "timestamp": time.time(),
            "mode": mode_name,
            "model_type": type(model).__name__,
            "callback_name": self.name
        }
        
        self.switch_history.append(switch_info)
        logger.info(f"[{self.name}] Model switched to {mode_name}: {type(model).__name__}")
    
    def get_history(self) -> list:
        """Получить историю переключений."""
        return self.switch_history.copy()
    
    def clear_history(self) -> None:
        """Очистить историю переключений."""
        self.switch_history.clear()


# Предустановленные конфигурации
SWITCHER_CONFIGS = {
    "conservative": {
        "mode": ModelMode.TEXT_ONLY,
        "description": "Всегда использует текстовую модель"
    },
    "aggressive": {
        "mode": ModelMode.MULTIMODAL,
        "description": "Всегда использует Vision модель (если доступна)"
    },
    "smart": {
        "mode": ModelMode.HYBRID,
        "description": "Автоматическое переключение на основе демонстрации экрана"
    }
}
