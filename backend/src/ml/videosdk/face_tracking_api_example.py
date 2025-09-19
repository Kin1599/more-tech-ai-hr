"""
API для тестирования и управления Face Tracking системой.

Демонстрирует возможности отслеживания лица, направления взгляда,
и анализа поведенческих паттернов во время интервью.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import logging
import base64
import io
import time
import cv2
import numpy as np
from PIL import Image
from av import VideoFrame

# Импорты из нашего проекта
from .face_tracking import (
    create_face_tracker, 
    FaceTracker, 
    FaceMetrics, 
    AttentionStats
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Face Tracking API",
    description="API для тестирования и анализа face tracking системы",
    version="1.0.0"
)

# Pydantic модели для API

class FaceTrackingConfigRequest(BaseModel):
    """Запрос на создание конфигурации face tracking."""
    face_detection_confidence: float = Field(0.5, description="Порог уверенности детекции лица")
    face_tracking_confidence: float = Field(0.5, description="Порог уверенности трекинга лица")
    max_num_faces: int = Field(1, description="Максимальное количество лиц для отслеживания")
    gaze_threshold: float = Field(30.0, description="Порог угла взгляда (градусы) для определения отвлечения")
    blink_threshold: float = Field(0.25, description="Порог EAR для определения моргания")
    distraction_min_duration: float = Field(2.0, description="Минимальная длительность отвлечения (секунды)")

class FaceTrackingTestRequest(BaseModel):
    """Запрос на тестирование face tracking."""
    image_data: str = Field(..., description="Base64 изображение для анализа")
    config: Optional[FaceTrackingConfigRequest] = Field(None, description="Конфигурация face tracking")

class FaceMetricsResponse(BaseModel):
    """Ответ с метриками лица."""
    timestamp: float
    face_detected: bool
    face_confidence: float
    face_bbox: Optional[List[int]] = None  # [x, y, width, height]
    
    # Eye tracking метрики
    eye_aspect_ratio_left: Optional[float] = None
    eye_aspect_ratio_right: Optional[float] = None
    
    # Направление взгляда
    gaze_direction_x: Optional[float] = None
    gaze_direction_y: Optional[float] = None
    
    # Head pose
    head_pose_yaw: Optional[float] = None
    head_pose_pitch: Optional[float] = None
    head_pose_roll: Optional[float] = None
    
    # Анализ
    is_looking_away: bool = False
    is_blinking: bool = False
    attention_level: str = "unknown"  # high, medium, low, absent

class AttentionStatsResponse(BaseModel):
    """Ответ со статистикой внимательности."""
    total_duration: float
    face_present_duration: float
    looking_away_duration: float
    blink_count: int
    face_presence_ratio: float
    attention_ratio: float
    distraction_frequency: float
    distraction_events_count: int

class BehavioralInsightsResponse(BaseModel):
    """Ответ с поведенческими инсайтами."""
    overall_engagement: str  # high, medium, low
    presence_quality: str    # good, acceptable, poor
    distraction_level: str   # low, medium, high
    insights: List[Dict[str, Any]]
    recommendations: List[str]

class FaceTrackingTestResponse(BaseModel):
    """Ответ тестирования face tracking."""
    success: bool
    metrics: Optional[FaceMetricsResponse] = None
    error: Optional[str] = None
    processing_time_ms: float
    analysis_summary: Dict[str, Any]

# Глобальный face tracker для тестирования
test_face_tracker: Optional[FaceTracker] = None

@app.post("/face-tracking/test", response_model=FaceTrackingTestResponse)
async def test_face_tracking(request: FaceTrackingTestRequest):
    """Протестировать face tracking на изображении."""
    global test_face_tracker
    start_time = time.time()
    
    try:
        # Создаем или обновляем face tracker
        config_dict = {}
        if request.config:
            config_dict = {
                "face_detection_confidence": request.config.face_detection_confidence,
                "face_tracking_confidence": request.config.face_tracking_confidence,
                "max_num_faces": request.config.max_num_faces,
                "gaze_threshold": request.config.gaze_threshold,
                "blink_threshold": request.config.blink_threshold,
                "distraction_min_duration": request.config.distraction_min_duration
            }
        
        test_face_tracker = create_face_tracker(config_dict)
        
        # Декодируем изображение
        try:
            image_bytes = base64.b64decode(request.image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Конвертируем в OpenCV формат
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Создаем VideoFrame для совместимости с face tracker
            video_frame = VideoFrame.from_ndarray(opencv_image, format="bgr24")
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Ошибка обработки изображения: {str(e)}")
        
        # Обработка кадра
        metrics = test_face_tracker.process_frame(video_frame)
        processing_time = (time.time() - start_time) * 1000
        
        # Анализ результатов
        attention_level = "high"
        is_looking_away = False
        
        if not metrics.face_detected:
            attention_level = "absent"
        elif (metrics.gaze_direction_x is not None and 
              abs(metrics.gaze_direction_x) > test_face_tracker.gaze_threshold):
            attention_level = "distracted"
            is_looking_away = True
        elif (metrics.gaze_direction_y is not None and 
              abs(metrics.gaze_direction_y) > test_face_tracker.gaze_threshold):
            attention_level = "distracted"
            is_looking_away = True
        
        # Детекция моргания
        is_blinking = False
        if (metrics.eye_aspect_ratio_left is not None and 
            metrics.eye_aspect_ratio_right is not None):
            avg_ear = (metrics.eye_aspect_ratio_left + metrics.eye_aspect_ratio_right) / 2
            is_blinking = avg_ear < test_face_tracker.blink_threshold
        
        # Формируем ответ
        metrics_response = FaceMetricsResponse(
            timestamp=metrics.timestamp,
            face_detected=metrics.face_detected,
            face_confidence=metrics.face_confidence,
            face_bbox=list(metrics.face_bbox) if metrics.face_bbox else None,
            eye_aspect_ratio_left=metrics.eye_aspect_ratio_left,
            eye_aspect_ratio_right=metrics.eye_aspect_ratio_right,
            gaze_direction_x=metrics.gaze_direction_x,
            gaze_direction_y=metrics.gaze_direction_y,
            head_pose_yaw=metrics.head_pose_yaw,
            head_pose_pitch=metrics.head_pose_pitch,
            head_pose_roll=metrics.head_pose_roll,
            is_looking_away=is_looking_away,
            is_blinking=is_blinking,
            attention_level=attention_level
        )
        
        # Анализ
        analysis_summary = {
            "face_detected": metrics.face_detected,
            "confidence_level": "high" if metrics.face_confidence > 0.8 else "medium" if metrics.face_confidence > 0.5 else "low",
            "attention_assessment": attention_level,
            "gaze_analysis": {
                "horizontal_deviation": abs(metrics.gaze_direction_x) if metrics.gaze_direction_x else 0,
                "vertical_deviation": abs(metrics.gaze_direction_y) if metrics.gaze_direction_y else 0,
                "looking_away": is_looking_away
            },
            "eye_analysis": {
                "left_ear": metrics.eye_aspect_ratio_left,
                "right_ear": metrics.eye_aspect_ratio_right,
                "blinking": is_blinking
            },
            "head_pose_analysis": {
                "yaw": metrics.head_pose_yaw,
                "pitch": metrics.head_pose_pitch,
                "roll": metrics.head_pose_roll
            }
        }
        
        return FaceTrackingTestResponse(
            success=True,
            metrics=metrics_response,
            processing_time_ms=processing_time,
            analysis_summary=analysis_summary
        )
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Ошибка в face tracking тесте: {e}")
        
        return FaceTrackingTestResponse(
            success=False,
            error=str(e),
            processing_time_ms=processing_time,
            analysis_summary={"error": "processing_failed"}
        )

@app.post("/face-tracking/test/upload")
async def test_face_tracking_upload(
    file: UploadFile = File(...),
    face_detection_confidence: float = Form(0.5),
    gaze_threshold: float = Form(30.0),
    blink_threshold: float = Form(0.25)
):
    """Протестировать face tracking с загруженным изображением."""
    try:
        # Проверяем тип файла
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Файл должен быть изображением")
        
        # Читаем и конвертируем изображение
        image_bytes = await file.read()
        image_b64 = base64.b64encode(image_bytes).decode()
        
        # Создаем конфигурацию
        config = FaceTrackingConfigRequest(
            face_detection_confidence=face_detection_confidence,
            gaze_threshold=gaze_threshold,
            blink_threshold=blink_threshold
        )
        
        # Используем основной endpoint
        request = FaceTrackingTestRequest(
            image_data=image_b64,
            config=config
        )
        
        return await test_face_tracking(request)
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании с загруженным файлом: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/face-tracking/stats", response_model=AttentionStatsResponse)
async def get_attention_stats(
    start_time: Optional[float] = None,
    end_time: Optional[float] = None
):
    """Получить статистику внимательности."""
    global test_face_tracker
    
    if not test_face_tracker:
        raise HTTPException(status_code=400, detail="Face tracker не инициализирован. Выполните тест сначала.")
    
    try:
        stats = test_face_tracker.get_attention_stats(start_time, end_time)
        
        return AttentionStatsResponse(
            total_duration=stats.total_duration,
            face_present_duration=stats.face_present_duration,
            looking_away_duration=stats.looking_away_duration,
            blink_count=stats.blink_count,
            face_presence_ratio=stats.face_presence_ratio,
            attention_ratio=stats.attention_ratio,
            distraction_frequency=stats.distraction_frequency,
            distraction_events_count=len(stats.distraction_events)
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/face-tracking/insights", response_model=BehavioralInsightsResponse)
async def get_behavioral_insights():
    """Получить поведенческие инсайты."""
    global test_face_tracker
    
    if not test_face_tracker:
        raise HTTPException(status_code=400, detail="Face tracker не инициализирован. Выполните тест сначала.")
    
    try:
        stats = test_face_tracker.get_attention_stats()
        current_status = test_face_tracker.get_current_status()
        
        insights = []
        recommendations = []
        
        # Анализ присутствия в кадре
        if stats.face_presence_ratio < 0.8:
            insights.append({
                "type": "presence",
                "level": "warning",
                "message": f"Низкое присутствие в кадре: {stats.face_presence_ratio*100:.1f}%",
                "value": stats.face_presence_ratio
            })
            recommendations.append("Улучшите позиционирование камеры и освещение")
        
        # Анализ внимательности
        if stats.attention_ratio < 0.7:
            insights.append({
                "type": "attention",
                "level": "warning",
                "message": f"Низкий уровень внимательности: {stats.attention_ratio*100:.1f}%",
                "value": stats.attention_ratio
            })
            recommendations.append("Кандидат часто отвлекался - обратите внимание на концентрацию")
        elif stats.attention_ratio > 0.9:
            insights.append({
                "type": "attention",
                "level": "positive",
                "message": f"Отличная концентрация: {stats.attention_ratio*100:.1f}%",
                "value": stats.attention_ratio
            })
            recommendations.append("Кандидат демонстрирует высокую вовлеченность")
        
        # Анализ частоты отвлечений
        if stats.distraction_frequency > 2:
            insights.append({
                "type": "distraction",
                "level": "warning",
                "message": f"Частые отвлечения: {stats.distraction_frequency:.1f}/мин",
                "value": stats.distraction_frequency
            })
            recommendations.append("Высокая частота отвлечений может указывать на нервозность")
        
        # Анализ моргания
        if stats.total_duration > 0:
            blinks_per_minute = (stats.blink_count / stats.total_duration) * 60
            if blinks_per_minute > 30:
                insights.append({
                    "type": "stress",
                    "level": "info",
                    "message": f"Повышенная частота моргания: {blinks_per_minute:.1f}/мин",
                    "value": blinks_per_minute
                })
                recommendations.append("Возможные признаки волнения или стресса")
        
        # Определение общих уровней
        overall_engagement = "high" if stats.attention_ratio > 0.8 else "medium" if stats.attention_ratio > 0.6 else "low"
        presence_quality = "good" if stats.face_presence_ratio > 0.9 else "acceptable" if stats.face_presence_ratio > 0.7 else "poor"
        distraction_level = "low" if stats.distraction_frequency < 1 else "medium" if stats.distraction_frequency < 3 else "high"
        
        return BehavioralInsightsResponse(
            overall_engagement=overall_engagement,
            presence_quality=presence_quality,
            distraction_level=distraction_level,
            insights=insights,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Ошибка анализа поведенческих инсайтов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/face-tracking/current-status")
async def get_current_status():
    """Получить текущий статус face tracking."""
    global test_face_tracker
    
    if not test_face_tracker:
        return {
            "initialized": False,
            "message": "Face tracker не инициализирован"
        }
    
    try:
        status = test_face_tracker.get_current_status()
        
        return {
            "initialized": True,
            "status": status,
            "metrics_count": len(test_face_tracker.metrics_history),
            "tracker_config": {
                "gaze_threshold": test_face_tracker.gaze_threshold,
                "blink_threshold": test_face_tracker.blink_threshold,
                "distraction_min_duration": test_face_tracker.distraction_min_duration
            }
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/face-tracking/reset")
async def reset_face_tracking():
    """Сброс статистики face tracking."""
    global test_face_tracker
    
    if not test_face_tracker:
        raise HTTPException(status_code=400, detail="Face tracker не инициализирован")
    
    try:
        test_face_tracker.reset_stats()
        
        return {
            "success": True,
            "message": "Статистика face tracking сброшена",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Ошибка сброса статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/face-tracking/demo")
async def get_demo_info():
    """Получить информацию о демо возможностях."""
    return {
        "title": "Face Tracking Demo API",
        "description": "Тестирование возможностей отслеживания лица и анализа поведения",
        "features": [
            "Детекция лица с оценкой уверенности",
            "Отслеживание направления взгляда",
            "Детекция моргания",
            "Анализ позы головы",
            "Статистика внимательности",
            "Поведенческие инсайты",
            "Детекция отвлечений"
        ],
        "endpoints": {
            "test": "POST /face-tracking/test - Тест на изображении",
            "upload": "POST /face-tracking/test/upload - Тест с загрузкой файла",
            "stats": "GET /face-tracking/stats - Статистика внимательности",
            "insights": "GET /face-tracking/insights - Поведенческие инсайты",
            "status": "GET /face-tracking/current-status - Текущий статус",
            "reset": "POST /face-tracking/reset - Сброс статистики"
        },
        "usage_example": {
            "step1": "Загрузите изображение через POST /face-tracking/test/upload",
            "step2": "Получите анализ через GET /face-tracking/insights",
            "step3": "Посмотрите статистику через GET /face-tracking/stats"
        },
        "parameters": {
            "face_detection_confidence": "Порог уверенности детекции лица (0.1-1.0)",
            "gaze_threshold": "Угол отклонения взгляда в градусах (10-60)",
            "blink_threshold": "Порог EAR для детекции моргания (0.1-0.4)"
        }
    }

@app.get("/health/face-tracking")
async def check_face_tracking_health():
    """Проверка состояния face tracking системы."""
    try:
        # Проверяем зависимости
        health_status = {
            "status": "healthy",
            "checks": []
        }
        
        # Проверка MediaPipe
        try:
            import mediapipe as mp
            health_status["checks"].append({
                "name": "MediaPipe",
                "status": "pass",
                "details": f"Version available"
            })
        except ImportError:
            health_status["checks"].append({
                "name": "MediaPipe",
                "status": "fail",
                "details": "MediaPipe not installed"
            })
            health_status["status"] = "unhealthy"
        
        # Проверка OpenCV
        try:
            import cv2
            health_status["checks"].append({
                "name": "OpenCV",
                "status": "pass",
                "details": f"Version {cv2.__version__}"
            })
        except ImportError:
            health_status["checks"].append({
                "name": "OpenCV",
                "status": "fail",
                "details": "OpenCV not installed"
            })
            health_status["status"] = "unhealthy"
        
        # Проверка NumPy
        try:
            import numpy as np
            health_status["checks"].append({
                "name": "NumPy",
                "status": "pass",
                "details": f"Version {np.__version__}"
            })
        except ImportError:
            health_status["checks"].append({
                "name": "NumPy",
                "status": "fail",
                "details": "NumPy not installed"
            })
            health_status["status"] = "unhealthy"
        
        # Статус face tracker
        global test_face_tracker
        if test_face_tracker:
            health_status["checks"].append({
                "name": "Face Tracker",
                "status": "pass",
                "details": f"Initialized with {len(test_face_tracker.metrics_history)} metrics"
            })
        else:
            health_status["checks"].append({
                "name": "Face Tracker",
                "status": "info",
                "details": "Not initialized (normal for fresh start)"
            })
        
        return health_status
        
    except Exception as e:
        logger.error(f"Face tracking health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "checks": []
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
