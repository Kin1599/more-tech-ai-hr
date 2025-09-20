"""
API для управления Avatar Video Stream.

Демонстрирует возможности управления видеопотоком AI аватара,
включая генерацию talking/idle кадров и проекцию на фронтенд.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import logging
import asyncio
import time
import json
import base64
import io
from datetime import datetime

# Импорты из нашего проекта
from .avatar_video_generator import (
    create_avatar_generator, 
    AvatarVideoGenerator,
    AvatarConfig,
    AvatarState
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Avatar Video API",
    description="API для управления видеопотоком AI аватара",
    version="1.0.0"
)

# Pydantic модели для API

class AvatarConfigRequest(BaseModel):
    """Запрос на создание конфигурации аватара."""
    avatar_type: str = Field("simli", description="Тип аватара: simli, custom, placeholder")
    face_id: Optional[str] = Field(None, description="ID лица для Simli аватара")
    resolution: List[int] = Field([640, 480], description="Разрешение видео [ширина, высота]")
    fps: int = Field(30, description="Частота кадров")
    talking_sensitivity: float = Field(0.3, description="Чувствительность детекции речи")
    emotion_detection: bool = Field(True, description="Включить детекцию эмоций")
    head_movement_enabled: bool = Field(True, description="Включить движение головы")
    eye_blink_enabled: bool = Field(True, description="Включить моргание")
    background_color: List[int] = Field([50, 50, 50], description="Цвет фона [R, G, B]")
    avatar_scale: float = Field(0.8, description="Масштаб аватара")

class SpeechDataRequest(BaseModel):
    """Запрос на обновление данных речи."""
    is_speaking: bool = Field(..., description="Говорит ли аватар")
    intensity: float = Field(0.0, description="Интенсивность речи (0.0-1.0)")
    audio_data: Optional[str] = Field(None, description="Base64 аудиоданные")

class FaceTrackingDataRequest(BaseModel):
    """Запрос на обновление данных face tracking."""
    face_detected: bool = Field(..., description="Обнаружено ли лицо")
    face_confidence: float = Field(0.0, description="Уверенность детекции лица")
    gaze_direction: Dict[str, float] = Field(..., description="Направление взгляда {x, y}")
    head_pose: Dict[str, float] = Field(..., description="Поза головы {yaw, pitch, roll}")
    eye_blink: bool = Field(False, description="Моргает ли")

class AvatarStateResponse(BaseModel):
    """Ответ с состоянием аватара."""
    timestamp: float
    is_talking: bool
    emotion: str
    mouth_openness: float
    eye_blink: bool
    head_movement: List[float]  # [yaw, pitch, roll]
    speech_intensity: float

class AvatarStatusResponse(BaseModel):
    """Ответ со статусом аватара."""
    available: bool
    avatar_type: Optional[str] = None
    is_active: bool = False
    current_state: Optional[AvatarStateResponse] = None
    config: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class AvatarFrameResponse(BaseModel):
    """Ответ с кадром аватара."""
    success: bool
    frame_data: Optional[str] = None  # Base64 изображение
    timestamp: float
    state: Optional[AvatarStateResponse] = None
    error: Optional[str] = None

# Глобальные переменные для управления аватаром
avatar_generator: Optional[AvatarVideoGenerator] = None
active_connections: Dict[str, WebSocket] = {}
avatar_stream_active = False

@app.post("/avatar/initialize", response_model=AvatarStatusResponse)
async def initialize_avatar(config: AvatarConfigRequest):
    """Инициализация аватара с конфигурацией."""
    global avatar_generator
    
    try:
        # Создаем генератор аватара
        config_dict = {
            "avatar_type": config.avatar_type,
            "face_id": config.face_id,
            "resolution": config.resolution,
            "fps": config.fps,
            "talking_sensitivity": config.talking_sensitivity,
            "emotion_detection": config.emotion_detection,
            "head_movement_enabled": config.head_movement_enabled,
            "eye_blink_enabled": config.eye_blink_enabled,
            "background_color": config.background_color,
            "avatar_scale": config.avatar_scale
        }
        
        avatar_generator = create_avatar_generator(config_dict)
        
        logger.info(f"Avatar инициализирован: {config.avatar_type}")
        
        return AvatarStatusResponse(
            available=True,
            avatar_type=config.avatar_type,
            is_active=False,
            current_state=AvatarStateResponse(
                timestamp=time.time(),
                is_talking=False,
                emotion="neutral",
                mouth_openness=0.0,
                eye_blink=False,
                head_movement=[0.0, 0.0, 0.0],
                speech_intensity=0.0
            ),
            config=config_dict
        )
        
    except Exception as e:
        logger.error(f"Ошибка инициализации аватара: {e}")
        return AvatarStatusResponse(
            available=False,
            error=str(e)
        )

@app.post("/avatar/start-stream")
async def start_avatar_stream():
    """Запуск видеопотока аватара."""
    global avatar_stream_active
    
    if not avatar_generator:
        raise HTTPException(status_code=400, detail="Avatar не инициализирован")
    
    try:
        avatar_stream_active = True
        logger.info("Avatar stream запущен")
        
        return {
            "success": True,
            "message": "Avatar stream запущен",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Ошибка запуска avatar stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/avatar/stop-stream")
async def stop_avatar_stream():
    """Остановка видеопотока аватара."""
    global avatar_stream_active
    
    try:
        avatar_stream_active = False
        
        # Закрываем все активные соединения
        for connection_id, websocket in active_connections.items():
            try:
                await websocket.close()
            except:
                pass
        active_connections.clear()
        
        logger.info("Avatar stream остановлен")
        
        return {
            "success": True,
            "message": "Avatar stream остановлен",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Ошибка остановки avatar stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/avatar/update-speech")
async def update_avatar_speech(speech_data: SpeechDataRequest):
    """Обновление данных речи для анимации аватара."""
    if not avatar_generator:
        raise HTTPException(status_code=400, detail="Avatar не инициализирован")
    
    try:
        # Декодируем аудиоданные если есть
        audio_bytes = None
        if speech_data.audio_data:
            audio_bytes = base64.b64decode(speech_data.audio_data)
        
        # Обновляем данные речи
        avatar_generator.update_speech_data(
            is_speaking=speech_data.is_speaking,
            speech_intensity=speech_data.intensity,
            audio_data=audio_bytes
        )
        
        logger.debug(f"Speech updated: speaking={speech_data.is_speaking}, intensity={speech_data.intensity}")
        
        return {
            "success": True,
            "message": "Данные речи обновлены",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Ошибка обновления данных речи: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/avatar/update-face-tracking")
async def update_avatar_face_tracking(face_data: FaceTrackingDataRequest):
    """Обновление данных face tracking для движения аватара."""
    if not avatar_generator:
        raise HTTPException(status_code=400, detail="Avatar не инициализирован")
    
    try:
        # Формируем данные face tracking
        face_tracking_data = {
            "face_detected": face_data.face_detected,
            "face_confidence": face_data.face_confidence,
            "gaze_direction": face_data.gaze_direction,
            "head_pose": face_data.head_pose,
            "eye_blink": face_data.eye_blink
        }
        
        # Обновляем данные face tracking
        avatar_generator.update_face_tracking_data(face_tracking_data)
        
        logger.debug("Face tracking данные обновлены")
        
        return {
            "success": True,
            "message": "Face tracking данные обновлены",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Ошибка обновления face tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/avatar/status", response_model=AvatarStatusResponse)
async def get_avatar_status():
    """Получение текущего статуса аватара."""
    if not avatar_generator:
        return AvatarStatusResponse(
            available=False,
            error="Avatar не инициализирован"
        )
    
    try:
        current_state = avatar_generator.current_state
        
        return AvatarStatusResponse(
            available=True,
            avatar_type=avatar_generator.config.avatar_type,
            is_active=avatar_stream_active,
            current_state=AvatarStateResponse(
                timestamp=current_state.timestamp,
                is_talking=current_state.is_talking,
                emotion=current_state.emotion,
                mouth_openness=current_state.mouth_openness,
                eye_blink=current_state.eye_blink,
                head_movement=list(current_state.head_movement),
                speech_intensity=current_state.speech_intensity
            ),
            config={
                "resolution": avatar_generator.config.resolution,
                "fps": avatar_generator.config.fps,
                "face_id": avatar_generator.config.face_id,
                "talking_sensitivity": avatar_generator.config.talking_sensitivity,
                "emotion_detection": avatar_generator.config.emotion_detection,
                "head_movement_enabled": avatar_generator.config.head_movement_enabled,
                "eye_blink_enabled": avatar_generator.config.eye_blink_enabled,
                "background_color": avatar_generator.config.background_color,
                "avatar_scale": avatar_generator.config.avatar_scale
            }
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса аватара: {e}")
        return AvatarStatusResponse(
            available=False,
            error=str(e)
        )

@app.get("/avatar/generate-frame", response_model=AvatarFrameResponse)
async def generate_avatar_frame():
    """Генерация одного кадра аватара."""
    if not avatar_generator:
        raise HTTPException(status_code=400, detail="Avatar не инициализирован")
    
    try:
        # Генерируем кадр
        frame = avatar_generator.generate_frame()
        
        # Конвертируем кадр в base64
        frame_array = frame.to_ndarray(format="rgb24")
        
        # Конвертируем в изображение
        from PIL import Image
        img = Image.fromarray(frame_array)
        
        # Конвертируем в base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        frame_data = base64.b64encode(buffer.getvalue()).decode()
        
        # Получаем текущее состояние
        current_state = avatar_generator.current_state
        
        return AvatarFrameResponse(
            success=True,
            frame_data=frame_data,
            timestamp=time.time(),
            state=AvatarStateResponse(
                timestamp=current_state.timestamp,
                is_talking=current_state.is_talking,
                emotion=current_state.emotion,
                mouth_openness=current_state.mouth_openness,
                eye_blink=current_state.eye_blink,
                head_movement=list(current_state.head_movement),
                speech_intensity=current_state.speech_intensity
            )
        )
        
    except Exception as e:
        logger.error(f"Ошибка генерации кадра аватара: {e}")
        return AvatarFrameResponse(
            success=False,
            error=str(e),
            timestamp=time.time()
        )

@app.websocket("/avatar/stream/{connection_id}")
async def avatar_stream_websocket(websocket: WebSocket, connection_id: str):
    """WebSocket для потоковой передачи кадров аватара."""
    global avatar_stream_active
    
    if not avatar_generator:
        await websocket.close(code=1000, reason="Avatar не инициализирован")
        return
    
    try:
        await websocket.accept()
        active_connections[connection_id] = websocket
        
        logger.info(f"WebSocket соединение установлено: {connection_id}")
        
        # Настройки потока
        target_fps = avatar_generator.config.fps
        frame_interval = 1.0 / target_fps
        
        last_frame_time = time.time()
        
        while avatar_stream_active and connection_id in active_connections:
            try:
                current_time = time.time()
                
                # Контроль FPS
                if current_time - last_frame_time >= frame_interval:
                    # Генерируем кадр
                    frame = avatar_generator.generate_frame()
                    
                    # Конвертируем в base64
                    frame_array = frame.to_ndarray(format="rgb24")
                    
                    from PIL import Image
                    img = Image.fromarray(frame_array)
                    
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=85)
                    frame_data = base64.b64encode(buffer.getvalue()).decode()
                    
                    # Получаем состояние
                    current_state = avatar_generator.current_state
                    
                    # Отправляем кадр
                    message = {
                        "type": "frame",
                        "frame_data": frame_data,
                        "timestamp": current_time,
                        "state": {
                            "is_talking": current_state.is_talking,
                            "emotion": current_state.emotion,
                            "mouth_openness": current_state.mouth_openness,
                            "eye_blink": current_state.eye_blink,
                            "head_movement": list(current_state.head_movement),
                            "speech_intensity": current_state.speech_intensity
                        }
                    }
                    
                    await websocket.send_text(json.dumps(message))
                    last_frame_time = current_time
                
                # Небольшая задержка для контроля нагрузки
                await asyncio.sleep(0.001)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Ошибка в WebSocket потоке: {e}")
                break
        
    except Exception as e:
        logger.error(f"Ошибка WebSocket соединения: {e}")
    finally:
        if connection_id in active_connections:
            del active_connections[connection_id]
        logger.info(f"WebSocket соединение закрыто: {connection_id}")

@app.post("/avatar/configure")
async def configure_avatar(config: Dict[str, Any]):
    """Настройка параметров аватара."""
    if not avatar_generator:
        raise HTTPException(status_code=400, detail="Avatar не инициализирован")
    
    try:
        # Обновляем конфигурацию
        if "talking_sensitivity" in config:
            avatar_generator.config.talking_sensitivity = config["talking_sensitivity"]
        
        if "emotion_detection" in config:
            avatar_generator.config.emotion_detection = config["emotion_detection"]
        
        if "head_movement_enabled" in config:
            avatar_generator.config.head_movement_enabled = config["head_movement_enabled"]
        
        if "eye_blink_enabled" in config:
            avatar_generator.config.eye_blink_enabled = config["eye_blink_enabled"]
        
        if "avatar_scale" in config:
            avatar_generator.config.avatar_scale = config["avatar_scale"]
        
        logger.info("Конфигурация аватара обновлена")
        
        return {
            "success": True,
            "message": "Конфигурация обновлена",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Ошибка настройки аватара: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/avatar/demo")
async def get_demo_info():
    """Получить информацию о демо возможностях."""
    return {
        "title": "Avatar Video Stream Demo API",
        "description": "Управление видеопотоком AI аватара с talking/idle кадрами",
        "features": [
            "Генерация talking кадров с анимацией рта",
            "Генерация idle кадров с естественными движениями",
            "Синхронизация с речью и face tracking",
            "WebSocket потоковая передача кадров",
            "Настраиваемые параметры анимации",
            "Поддержка различных типов аватаров"
        ],
        "endpoints": {
            "initialize": "POST /avatar/initialize - Инициализация аватара",
            "start_stream": "POST /avatar/start-stream - Запуск видеопотока",
            "stop_stream": "POST /avatar/stop-stream - Остановка видеопотока",
            "update_speech": "POST /avatar/update-speech - Обновление данных речи",
            "update_face_tracking": "POST /avatar/update-face-tracking - Обновление face tracking",
            "status": "GET /avatar/status - Статус аватара",
            "generate_frame": "GET /avatar/generate-frame - Генерация кадра",
            "stream_websocket": "WS /avatar/stream/{id} - Потоковая передача",
            "configure": "POST /avatar/configure - Настройка параметров"
        },
        "usage_example": {
            "step1": "POST /avatar/initialize - Инициализировать аватар",
            "step2": "POST /avatar/start-stream - Запустить видеопоток",
            "step3": "WS /avatar/stream/demo - Подключиться к потоку",
            "step4": "POST /avatar/update-speech - Обновить данные речи",
            "step5": "POST /avatar/stop-stream - Остановить поток"
        },
        "avatar_types": {
            "simli": "Simli AI Avatar с lip-sync",
            "custom": "Кастомный аватар",
            "placeholder": "Простой placeholder аватар"
        },
        "animation_features": {
            "mouth_animation": "Анимация рта на основе речи",
            "eye_blink": "Естественное моргание",
            "head_movement": "Движение головы на основе face tracking",
            "emotion_detection": "Детекция и отображение эмоций",
            "speech_sync": "Синхронизация с речью"
        }
    }

@app.get("/health/avatar")
async def check_avatar_health():
    """Проверка состояния avatar системы."""
    try:
        health_status = {
            "status": "healthy",
            "checks": []
        }
        
        # Проверка генератора аватара
        if avatar_generator:
            health_status["checks"].append({
                "name": "Avatar Generator",
                "status": "pass",
                "details": f"Type: {avatar_generator.config.avatar_type}, Active: {avatar_stream_active}"
            })
        else:
            health_status["checks"].append({
                "name": "Avatar Generator",
                "status": "fail",
                "details": "Not initialized"
            })
            health_status["status"] = "unhealthy"
        
        # Проверка активных соединений
        health_status["checks"].append({
            "name": "WebSocket Connections",
            "status": "pass",
            "details": f"Active connections: {len(active_connections)}"
        })
        
        # Проверка PIL
        try:
            from PIL import Image
            health_status["checks"].append({
                "name": "PIL",
                "status": "pass",
                "details": "Available"
            })
        except ImportError:
            health_status["checks"].append({
                "name": "PIL",
                "status": "fail",
                "details": "PIL not installed"
            })
            health_status["status"] = "unhealthy"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Avatar health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "checks": []
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
