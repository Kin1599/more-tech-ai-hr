"""
API для тестирования динамического переключения между текстовыми и Vision моделями.

Демонстрирует работу Dynamic Model Switcher в различных режимах.
"""

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import logging
import asyncio

# Импорты из нашего проекта
from ...core.database import get_session
from .dynamic_model_switcher import (
    DynamicModelSwitcher, 
    ModelMode, 
    create_dynamic_model_switcher,
    ModelSwitchCallback
)
from .model_factory import ModelFactory
from .model_service import ModelConfigurationService
from .screen_analysis_tool import create_screen_analysis_tool
from ...models.ai_models import ModelTypeEnum

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Dynamic Model Switching API",
    description="API для тестирования динамического переключения между LLM и Vision моделями",
    version="1.0.0"
)

# Pydantic модели для API

class SwitcherCreateRequest(BaseModel):
    """Запрос на создание Dynamic Model Switcher."""
    vacancy_id: int = Field(..., description="ID вакансии для загрузки моделей")
    mode: str = Field("hybrid", description="Режим работы: text_only, multimodal, hybrid")
    enable_notifications: bool = Field(True, description="Включить уведомления о переключениях")

class SwitcherResponse(BaseModel):
    """Ответ с информацией о Dynamic Model Switcher."""
    switcher_id: str
    mode: str
    current_model_type: str
    screenshare_active: bool
    vision_available: bool
    statistics: Dict[str, Any]

class MessageRequest(BaseModel):
    """Запрос на обработку сообщения."""
    switcher_id: str = Field(..., description="ID переключателя")
    message: str = Field(..., description="Сообщение для обработки")
    force_vision: Optional[bool] = Field(None, description="Принудительно использовать Vision")

class MessageResponse(BaseModel):
    """Ответ на сообщение."""
    response: str
    model_used: str
    processing_time_ms: float
    vision_analysis_used: bool
    switch_occurred: bool

class ScreenshareRequest(BaseModel):
    """Запрос на изменение статуса демонстрации экрана."""
    switcher_id: str = Field(..., description="ID переключателя")
    active: bool = Field(..., description="Активна ли демонстрация экрана")

class SwitchModeRequest(BaseModel):
    """Запрос на смену режима работы."""
    switcher_id: str = Field(..., description="ID переключателя")
    mode: str = Field(..., description="Новый режим: text_only, multimodal, hybrid")

# Глобальное хранилище переключателей (в продакшене использовать Redis/DB)
active_switchers: Dict[str, DynamicModelSwitcher] = {}
switch_callbacks: Dict[str, ModelSwitchCallback] = {}

@app.post("/switchers/", response_model=SwitcherResponse)
async def create_switcher(
    request: SwitcherCreateRequest,
    db: Session = Depends(get_session)
):
    """
    Создать новый Dynamic Model Switcher для тестирования.
    
    Загружает модели из конфигурации вакансии и создает переключатель.
    """
    try:
        import uuid
        switcher_id = str(uuid.uuid4())
        
        # Загружаем модели из конфигурации вакансии
        service = ModelConfigurationService(db)
        models_config = service.get_interview_models_config(request.vacancy_id)
        
        if not models_config:
            raise HTTPException(
                status_code=404, 
                detail=f"Interview configuration not found for vacancy {request.vacancy_id}"
            )
        
        # Создаем текстовую модель (заглушка для демо)
        text_llm = MockLLMModel("Text LLM")
        
        # Создаем Vision модель если есть в конфигурации
        vision_llm = None
        screen_tool = None
        
        vision_config = models_config.get("vision_model")
        if vision_config:
            try:
                # Создаем Vision модель
                vision_model = ModelFactory.create_vision_model(vision_config)
                screen_tool = create_screen_analysis_tool(vision_model)
                vision_llm = MockLLMModel("Vision LLM", has_vision=True)
                
                logger.info("Vision модель создана для переключателя")
            except Exception as e:
                logger.warning(f"Failed to create Vision model: {e}")
        
        # Определяем режим
        mode_map = {
            "text_only": ModelMode.TEXT_ONLY,
            "multimodal": ModelMode.MULTIMODAL,
            "hybrid": ModelMode.HYBRID
        }
        mode = mode_map.get(request.mode, ModelMode.HYBRID)
        
        # Создаем переключатель
        switcher = create_dynamic_model_switcher(
            text_llm=text_llm,
            vision_llm=vision_llm,
            screen_analysis_tool=screen_tool,
            mode=mode
        )
        
        # Добавляем callback для уведомлений
        if request.enable_notifications:
            callback = ModelSwitchCallback(f"switcher_{switcher_id}")
            switcher.add_switch_callback(callback)
            switch_callbacks[switcher_id] = callback
        
        # Сохраняем переключатель
        active_switchers[switcher_id] = switcher
        
        logger.info(f"Dynamic Model Switcher создан: {switcher_id}")
        
        return SwitcherResponse(
            switcher_id=switcher_id,
            mode=mode.value,
            current_model_type="vision" if switcher.is_vision_mode() else "text",
            screenshare_active=switcher.is_screenshare_active,
            vision_available=vision_llm is not None,
            statistics=switcher.get_statistics()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating switcher: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/switchers/{switcher_id}/message", response_model=MessageResponse)
async def process_message(
    switcher_id: str,
    request: MessageRequest
):
    """
    Обработать сообщение через Dynamic Model Switcher.
    
    Автоматически определяет, нужен ли Vision анализ, и переключает модели.
    """
    import time
    start_time = time.time()
    
    try:
        switcher = active_switchers.get(switcher_id)
        if not switcher:
            raise HTTPException(status_code=404, detail="Switcher not found")
        
        # Запоминаем текущую модель для отслеживания переключений
        old_model = switcher.get_current_model()
        
        # Принудительное переключение если запрошено
        if request.force_vision is True:
            if not switcher.force_switch_to_vision():
                raise HTTPException(status_code=400, detail="Vision model not available")
        elif request.force_vision is False:
            switcher.force_switch_to_text()
        
        # Обрабатываем сообщение
        response = await switcher.process_message(request.message)
        
        # Определяем, какая модель использовалась
        current_model = switcher.get_current_model()
        model_used = "vision" if switcher.is_vision_mode() else "text"
        switch_occurred = old_model != current_model
        
        processing_time = (time.time() - start_time) * 1000
        
        return MessageResponse(
            response=response,
            model_used=model_used,
            processing_time_ms=processing_time,
            vision_analysis_used=switcher.is_vision_mode() and switcher.is_screenshare_active,
            switch_occurred=switch_occurred
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/switchers/{switcher_id}/screenshare")
async def set_screenshare_status(
    switcher_id: str,
    request: ScreenshareRequest
):
    """
    Изменить статус демонстрации экрана.
    
    Автоматически переключает между текстовой и Vision моделью.
    """
    try:
        switcher = active_switchers.get(switcher_id)
        if not switcher:
            raise HTTPException(status_code=404, detail="Switcher not found")
        
        old_status = switcher.is_screenshare_active
        switcher.set_screenshare_status(request.active)
        
        return {
            "message": f"Screenshare {'activated' if request.active else 'deactivated'}",
            "old_status": old_status,
            "new_status": request.active,
            "current_model": "vision" if switcher.is_vision_mode() else "text",
            "switch_occurred": old_status != request.active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting screenshare status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/switchers/{switcher_id}/mode")
async def switch_mode(
    switcher_id: str,
    request: SwitchModeRequest
):
    """Изменить режим работы переключателя."""
    try:
        switcher = active_switchers.get(switcher_id)
        if not switcher:
            raise HTTPException(status_code=404, detail="Switcher not found")
        
        mode_map = {
            "text_only": ModelMode.TEXT_ONLY,
            "multimodal": ModelMode.MULTIMODAL,
            "hybrid": ModelMode.HYBRID
        }
        
        new_mode = mode_map.get(request.mode)
        if not new_mode:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid mode: {request.mode}. Use: text_only, multimodal, hybrid"
            )
        
        old_mode = switcher.mode
        switcher.set_mode(new_mode)
        
        return {
            "message": f"Mode switched from {old_mode.value} to {new_mode.value}",
            "old_mode": old_mode.value,
            "new_mode": new_mode.value,
            "current_model": "vision" if switcher.is_vision_mode() else "text"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/switchers/{switcher_id}", response_model=SwitcherResponse)
async def get_switcher_status(switcher_id: str):
    """Получить статус переключателя."""
    try:
        switcher = active_switchers.get(switcher_id)
        if not switcher:
            raise HTTPException(status_code=404, detail="Switcher not found")
        
        return SwitcherResponse(
            switcher_id=switcher_id,
            mode=switcher.mode.value,
            current_model_type="vision" if switcher.is_vision_mode() else "text",
            screenshare_active=switcher.is_screenshare_active,
            vision_available=switcher.vision_llm is not None,
            statistics=switcher.get_statistics()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting switcher status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/switchers/{switcher_id}/history")
async def get_switch_history(switcher_id: str):
    """Получить историю переключений модели."""
    try:
        callback = switch_callbacks.get(switcher_id)
        if not callback:
            raise HTTPException(status_code=404, detail="Switch history not found")
        
        return {
            "switcher_id": switcher_id,
            "switch_history": callback.get_history(),
            "total_switches": len(callback.get_history())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting switch history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/switchers/")
async def list_active_switchers():
    """Получить список активных переключателей."""
    return {
        "active_switchers": [
            {
                "switcher_id": switcher_id,
                "mode": switcher.mode.value,
                "current_model": "vision" if switcher.is_vision_mode() else "text",
                "screenshare_active": switcher.is_screenshare_active,
                "statistics": switcher.get_statistics()
            }
            for switcher_id, switcher in active_switchers.items()
        ],
        "total_count": len(active_switchers)
    }

@app.delete("/switchers/{switcher_id}")
async def delete_switcher(switcher_id: str):
    """Удалить переключатель."""
    try:
        if switcher_id in active_switchers:
            del active_switchers[switcher_id]
        
        if switcher_id in switch_callbacks:
            del switch_callbacks[switcher_id]
        
        return {"message": f"Switcher {switcher_id} deleted"}
        
    except Exception as e:
        logger.error(f"Error deleting switcher: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/demo/scenarios/")
async def get_demo_scenarios():
    """Получить демонстрационные сценарии для тестирования."""
    return {
        "scenarios": [
            {
                "name": "Basic Text Interview",
                "description": "Обычное интервью без демонстрации экрана",
                "steps": [
                    {"action": "create_switcher", "mode": "hybrid"},
                    {"action": "send_message", "message": "Расскажите о своем опыте работы"},
                    {"action": "send_message", "message": "Какие технологии вы используете?"}
                ]
            },
            {
                "name": "Code Review Session",
                "description": "Интервью с демонстрацией кода",
                "steps": [
                    {"action": "create_switcher", "mode": "hybrid"},
                    {"action": "enable_screenshare"},
                    {"action": "send_message", "message": "Покажите свой код"},
                    {"action": "send_message", "message": "Объясните эту функцию"},
                    {"action": "disable_screenshare"}
                ]
            },
            {
                "name": "Vision Only Mode",
                "description": "Принудительное использование Vision модели",
                "steps": [
                    {"action": "create_switcher", "mode": "multimodal"},
                    {"action": "send_message", "message": "Анализируйте все визуально", "force_vision": True}
                ]
            },
            {
                "name": "Dynamic Switching",
                "description": "Автоматическое переключение между режимами",
                "steps": [
                    {"action": "create_switcher", "mode": "hybrid"},
                    {"action": "send_message", "message": "Привет, как дела?"},
                    {"action": "enable_screenshare"},
                    {"action": "send_message", "message": "Посмотрите на этот код"},
                    {"action": "disable_screenshare"},
                    {"action": "send_message", "message": "Спасибо за интервью"}
                ]
            }
        ]
    }

# Заглушка для демонстрации
class MockLLMModel:
    """Заглушка LLM модели для демонстрации."""
    
    def __init__(self, name: str, has_vision: bool = False):
        self.name = name
        self.has_vision = has_vision
        self.conversation_history = []
        self.finished = False
    
    def ask(self, message: str) -> str:
        """Имитация ответа модели."""
        self.conversation_history.append({"user": message})
        
        if self.has_vision:
            response = f"[{self.name}] 👁️ Я вижу ваш экран и анализирую: {message}"
        else:
            response = f"[{self.name}] 💬 Текстовый ответ на: {message}"
        
        self.conversation_history.append({"assistant": response})
        
        # Имитация завершения интервью
        if "спасибо" in message.lower() or "пока" in message.lower():
            self.finished = True
        
        return response
    
    def is_finished(self) -> bool:
        return self.finished
    
    def get_history(self) -> list:
        return self.conversation_history
    
    def get_final_feedback(self) -> dict:
        if self.finished:
            return {"verdict": "positive", "score": 85, "model": self.name}
        return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
