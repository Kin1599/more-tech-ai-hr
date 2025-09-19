"""
Face Detection и Eye Tracking для анализа поведения кандидата.

Отслеживает:
- Присутствие лица в кадре
- Направление взгляда
- Частоту отвлечений
- Статистику внимательности
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
import cv2
from av import VideoFrame
import mediapipe as mp
from videosdk import CustomVideoTrack

logger = logging.getLogger(__name__)

@dataclass
class FaceMetrics:
    """Метрики лица в конкретный момент времени."""
    timestamp: float
    face_detected: bool
    face_confidence: float
    face_bbox: Optional[Tuple[int, int, int, int]] = None  # (x, y, width, height)
    
    # Eye tracking метрики
    left_eye_landmarks: Optional[List[Tuple[float, float]]] = None
    right_eye_landmarks: Optional[List[Tuple[float, float]]] = None
    eye_aspect_ratio_left: Optional[float] = None
    eye_aspect_ratio_right: Optional[float] = None
    
    # Направление взгляда (углы в градусах)
    gaze_direction_x: Optional[float] = None  # -90 до 90 (лево-право)
    gaze_direction_y: Optional[float] = None  # -90 до 90 (вверх-вниз)
    
    # Head pose (поворот головы)
    head_pose_yaw: Optional[float] = None    # поворот влево-вправо
    head_pose_pitch: Optional[float] = None  # наклон вверх-вниз
    head_pose_roll: Optional[float] = None   # наклон влево-вправо

@dataclass
class AttentionStats:
    """Статистика внимательности за период."""
    total_duration: float = 0.0
    face_present_duration: float = 0.0
    looking_away_duration: float = 0.0
    blink_count: int = 0
    distraction_events: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def face_presence_ratio(self) -> float:
        """Процент времени с лицом в кадре."""
        return (self.face_present_duration / self.total_duration) if self.total_duration > 0 else 0.0
    
    @property
    def attention_ratio(self) -> float:
        """Процент времени внимательного взгляда."""
        attention_duration = self.face_present_duration - self.looking_away_duration
        return (attention_duration / self.total_duration) if self.total_duration > 0 else 0.0
    
    @property
    def distraction_frequency(self) -> float:
        """Частота отвлечений в минуту."""
        minutes = self.total_duration / 60.0
        return len(self.distraction_events) / minutes if minutes > 0 else 0.0

class FaceTracker:
    """Основной класс для отслеживания лица и глаз."""
    
    def __init__(self, 
                 face_detection_confidence: float = 0.5,
                 face_tracking_confidence: float = 0.5,
                 max_num_faces: int = 1,
                 gaze_threshold: float = 30.0,  # градусы для определения "смотрит в сторону"
                 blink_threshold: float = 0.25,  # EAR порог для моргания
                 distraction_min_duration: float = 2.0):  # минимальная длительность отвлечения в секундах
        
        self.face_detection_confidence = face_detection_confidence
        self.face_tracking_confidence = face_tracking_confidence
        self.max_num_faces = max_num_faces
        self.gaze_threshold = gaze_threshold
        self.blink_threshold = blink_threshold
        self.distraction_min_duration = distraction_min_duration
        
        # Инициализация MediaPipe
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Создаем детекторы
        self.face_detection = self.mp_face_detection.FaceDetection(
            min_detection_confidence=face_detection_confidence
        )
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=max_num_faces,
            min_detection_confidence=face_detection_confidence,
            min_tracking_confidence=face_tracking_confidence,
            refine_landmarks=True
        )
        
        # Индексы ключевых точек для глаз (MediaPipe Face Mesh)
        self.LEFT_EYE_INDICES = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.RIGHT_EYE_INDICES = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        
        # Индексы для расчета EAR (Eye Aspect Ratio)
        self.LEFT_EYE_EAR_INDICES = [33, 160, 158, 133, 153, 144]   # P1, P2, P3, P4, P5, P6
        self.RIGHT_EYE_EAR_INDICES = [362, 385, 387, 263, 373, 380]
        
        # Индексы для определения направления взгляда
        self.NOSE_TIP_INDEX = 1
        self.LEFT_EYE_CENTER_INDEX = 468
        self.RIGHT_EYE_CENTER_INDEX = 473
        
        # История метрик
        self.metrics_history: List[FaceMetrics] = []
        self.max_history_size = 1000  # максимум записей в истории
        
        # Состояние для отслеживания событий
        self.current_distraction_start: Optional[float] = None
        self.last_blink_time: float = 0.0
        self.blink_counter = 0
        
        logger.info("FaceTracker инициализирован")
    
    def calculate_eye_aspect_ratio(self, landmarks: List[Tuple[float, float]], 
                                  ear_indices: List[int]) -> float:
        """Вычисление Eye Aspect Ratio для определения моргания."""
        if len(ear_indices) != 6:
            return 0.0
        
        try:
            # Извлекаем координаты точек
            points = [landmarks[i] for i in ear_indices]
            
            # Вычисляем расстояния
            # Вертикальные расстояния
            A = np.linalg.norm(np.array(points[1]) - np.array(points[5]))
            B = np.linalg.norm(np.array(points[2]) - np.array(points[4]))
            
            # Горизонтальное расстояние
            C = np.linalg.norm(np.array(points[0]) - np.array(points[3]))
            
            # EAR формула
            ear = (A + B) / (2.0 * C)
            return ear
        except Exception as e:
            logger.warning(f"Ошибка вычисления EAR: {e}")
            return 0.0
    
    def estimate_gaze_direction(self, landmarks: List[Tuple[float, float]], 
                              image_width: int, image_height: int) -> Tuple[float, float]:
        """Оценка направления взгляда на основе позиции глаз относительно носа."""
        try:
            nose_tip = landmarks[self.NOSE_TIP_INDEX]
            left_eye_center = landmarks[self.LEFT_EYE_CENTER_INDEX]
            right_eye_center = landmarks[self.RIGHT_EYE_CENTER_INDEX]
            
            # Центр между глазами
            eye_center = (
                (left_eye_center[0] + right_eye_center[0]) / 2,
                (left_eye_center[1] + right_eye_center[1]) / 2
            )
            
            # Вектор от центра глаз к кончику носа
            gaze_vector = (
                nose_tip[0] - eye_center[0],
                nose_tip[1] - eye_center[1]
            )
            
            # Нормализация и перевод в углы
            # Горизонтальный угол (лево-право)
            gaze_x = np.arctan2(gaze_vector[0], abs(gaze_vector[1])) * 180 / np.pi
            
            # Вертикальный угол (вверх-вниз)
            gaze_y = np.arctan2(gaze_vector[1], abs(gaze_vector[0])) * 180 / np.pi
            
            return gaze_x, gaze_y
            
        except Exception as e:
            logger.warning(f"Ошибка оценки направления взгляда: {e}")
            return 0.0, 0.0
    
    def estimate_head_pose(self, landmarks: List[Tuple[float, float]], 
                          image_width: int, image_height: int) -> Tuple[float, float, float]:
        """Оценка позы головы (упрощенная версия)."""
        try:
            # Ключевые точки для оценки позы головы
            nose_tip = landmarks[self.NOSE_TIP_INDEX]
            left_eye = landmarks[self.LEFT_EYE_CENTER_INDEX]
            right_eye = landmarks[self.RIGHT_EYE_CENTER_INDEX]
            
            # Центр лица
            face_center = (image_width / 2, image_height / 2)
            
            # Yaw (поворот влево-вправо)
            eye_center_x = (left_eye[0] + right_eye[0]) / 2
            yaw = (eye_center_x - face_center[0]) / face_center[0] * 45  # примерная оценка
            
            # Pitch (наклон вверх-вниз)
            eye_center_y = (left_eye[1] + right_eye[1]) / 2
            pitch = (eye_center_y - face_center[1]) / face_center[1] * 45
            
            # Roll (наклон влево-вправо)
            eye_angle = np.arctan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0])
            roll = eye_angle * 180 / np.pi
            
            return yaw, pitch, roll
            
        except Exception as e:
            logger.warning(f"Ошибка оценки позы головы: {e}")
            return 0.0, 0.0, 0.0
    
    def process_frame(self, frame: VideoFrame) -> FaceMetrics:
        """Обработка одного кадра и извлечение метрик лица."""
        timestamp = time.time()
        
        # Конвертация кадра в изображение
        img = frame.to_ndarray(format="bgr24")
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]
        
        # Инициализация метрик
        metrics = FaceMetrics(
            timestamp=timestamp,
            face_detected=False,
            face_confidence=0.0
        )
        
        try:
            # Детекция лица
            face_results = self.face_detection.process(img_rgb)
            
            if face_results.detections:
                detection = face_results.detections[0]  # берем первое лицо
                metrics.face_detected = True
                metrics.face_confidence = detection.score[0]
                
                # Получаем bounding box
                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                metrics.face_bbox = (x, y, width, height)
                
                # Детальный анализ с Face Mesh
                mesh_results = self.face_mesh.process(img_rgb)
                
                if mesh_results.multi_face_landmarks:
                    face_landmarks = mesh_results.multi_face_landmarks[0]
                    
                    # Конвертация landmarks в координаты
                    landmarks = []
                    for landmark in face_landmarks.landmark:
                        landmarks.append((landmark.x * w, landmark.y * h))
                    
                    # Извлечение landmarks глаз
                    metrics.left_eye_landmarks = [landmarks[i] for i in self.LEFT_EYE_INDICES]
                    metrics.right_eye_landmarks = [landmarks[i] for i in self.RIGHT_EYE_INDICES]
                    
                    # Вычисление EAR для обоих глаз
                    metrics.eye_aspect_ratio_left = self.calculate_eye_aspect_ratio(
                        landmarks, self.LEFT_EYE_EAR_INDICES
                    )
                    metrics.eye_aspect_ratio_right = self.calculate_eye_aspect_ratio(
                        landmarks, self.RIGHT_EYE_EAR_INDICES
                    )
                    
                    # Оценка направления взгляда
                    gaze_x, gaze_y = self.estimate_gaze_direction(landmarks, w, h)
                    metrics.gaze_direction_x = gaze_x
                    metrics.gaze_direction_y = gaze_y
                    
                    # Оценка позы головы
                    yaw, pitch, roll = self.estimate_head_pose(landmarks, w, h)
                    metrics.head_pose_yaw = yaw
                    metrics.head_pose_pitch = pitch
                    metrics.head_pose_roll = roll
                    
                    # Детекция моргания
                    self._detect_blink(metrics)
        
        except Exception as e:
            logger.error(f"Ошибка обработки кадра: {e}")
        
        # Сохранение метрик в историю
        self._add_to_history(metrics)
        
        # Анализ событий отвлечения
        self._analyze_attention_events(metrics)
        
        return metrics
    
    def _detect_blink(self, metrics: FaceMetrics):
        """Детекция моргания на основе EAR."""
        if (metrics.eye_aspect_ratio_left is not None and 
            metrics.eye_aspect_ratio_right is not None):
            
            avg_ear = (metrics.eye_aspect_ratio_left + metrics.eye_aspect_ratio_right) / 2
            
            # Детекция моргания
            if avg_ear < self.blink_threshold:
                current_time = time.time()
                if current_time - self.last_blink_time > 0.3:  # минимум 300мс между морганиями
                    self.blink_counter += 1
                    self.last_blink_time = current_time
                    logger.debug(f"Моргание обнаружено. Общий счетчик: {self.blink_counter}")
    
    def _analyze_attention_events(self, metrics: FaceMetrics):
        """Анализ событий внимания и отвлечения."""
        is_looking_away = False
        
        if metrics.face_detected:
            # Проверяем, смотрит ли человек в сторону
            if (metrics.gaze_direction_x is not None and 
                abs(metrics.gaze_direction_x) > self.gaze_threshold):
                is_looking_away = True
            
            if (metrics.gaze_direction_y is not None and 
                abs(metrics.gaze_direction_y) > self.gaze_threshold):
                is_looking_away = True
        else:
            # Если лица нет в кадре - это тоже отвлечение
            is_looking_away = True
        
        # Отслеживание начала/конца отвлечения
        current_time = time.time()
        
        if is_looking_away and self.current_distraction_start is None:
            # Начало отвлечения
            self.current_distraction_start = current_time
            logger.debug("Начало отвлечения")
        
        elif not is_looking_away and self.current_distraction_start is not None:
            # Конец отвлечения
            distraction_duration = current_time - self.current_distraction_start
            
            if distraction_duration >= self.distraction_min_duration:
                # Записываем событие отвлечения
                distraction_event = {
                    "start_time": self.current_distraction_start,
                    "end_time": current_time,
                    "duration": distraction_duration,
                    "type": "face_absent" if not metrics.face_detected else "looking_away",
                    "gaze_direction_x": metrics.gaze_direction_x,
                    "gaze_direction_y": metrics.gaze_direction_y
                }
                
                # Добавляем в историю последних метрик
                if self.metrics_history:
                    self.metrics_history[-1].distraction_events = getattr(
                        self.metrics_history[-1], 'distraction_events', []
                    )
                    self.metrics_history[-1].distraction_events.append(distraction_event)
                
                logger.info(f"Зафиксировано отвлечение длительностью {distraction_duration:.1f}с")
            
            self.current_distraction_start = None
    
    def _add_to_history(self, metrics: FaceMetrics):
        """Добавление метрик в историю с ограничением размера."""
        self.metrics_history.append(metrics)
        
        # Ограничиваем размер истории
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history.pop(0)
    
    def get_attention_stats(self, 
                          start_time: Optional[float] = None, 
                          end_time: Optional[float] = None) -> AttentionStats:
        """Получение статистики внимательности за указанный период."""
        if not self.metrics_history:
            return AttentionStats()
        
        # Фильтрация по времени
        filtered_metrics = self.metrics_history
        if start_time is not None:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp >= start_time]
        if end_time is not None:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp <= end_time]
        
        if not filtered_metrics:
            return AttentionStats()
        
        # Вычисление статистик
        stats = AttentionStats()
        
        total_start = filtered_metrics[0].timestamp
        total_end = filtered_metrics[-1].timestamp
        stats.total_duration = total_end - total_start
        
        # Подсчет времени с лицом в кадре
        face_present_frames = sum(1 for m in filtered_metrics if m.face_detected)
        total_frames = len(filtered_metrics)
        stats.face_present_duration = (face_present_frames / total_frames) * stats.total_duration
        
        # Подсчет времени "смотрит в сторону"
        looking_away_frames = 0
        for m in filtered_metrics:
            if m.face_detected:
                is_looking_away = False
                if (m.gaze_direction_x is not None and 
                    abs(m.gaze_direction_x) > self.gaze_threshold):
                    is_looking_away = True
                if (m.gaze_direction_y is not None and 
                    abs(m.gaze_direction_y) > self.gaze_threshold):
                    is_looking_away = True
                
                if is_looking_away:
                    looking_away_frames += 1
        
        stats.looking_away_duration = (looking_away_frames / total_frames) * stats.total_duration
        
        # Счетчик морганий
        stats.blink_count = self.blink_counter
        
        # Сбор событий отвлечения
        for m in filtered_metrics:
            if hasattr(m, 'distraction_events'):
                stats.distraction_events.extend(m.distraction_events)
        
        return stats
    
    def get_current_status(self) -> Dict[str, Any]:
        """Получение текущего статуса отслеживания."""
        if not self.metrics_history:
            return {
                "face_detected": False,
                "attention_level": "unknown",
                "last_update": None
            }
        
        latest = self.metrics_history[-1]
        
        # Определение уровня внимания
        attention_level = "high"
        if not latest.face_detected:
            attention_level = "absent"
        elif (latest.gaze_direction_x is not None and 
              abs(latest.gaze_direction_x) > self.gaze_threshold):
            attention_level = "distracted"
        elif (latest.gaze_direction_y is not None and 
              abs(latest.gaze_direction_y) > self.gaze_threshold):
            attention_level = "distracted"
        
        return {
            "face_detected": latest.face_detected,
            "face_confidence": latest.face_confidence,
            "attention_level": attention_level,
            "gaze_direction": {
                "x": latest.gaze_direction_x,
                "y": latest.gaze_direction_y
            },
            "head_pose": {
                "yaw": latest.head_pose_yaw,
                "pitch": latest.head_pose_pitch,
                "roll": latest.head_pose_roll
            },
            "blink_count": self.blink_counter,
            "last_update": latest.timestamp,
            "currently_distracted": self.current_distraction_start is not None
        }
    
    def reset_stats(self):
        """Сброс всех статистик."""
        self.metrics_history.clear()
        self.blink_counter = 0
        self.current_distraction_start = None
        self.last_blink_time = 0.0
        logger.info("Статистики face tracking сброшены")

class FaceTrackingVideoTrack(CustomVideoTrack):
    """Custom video track с интегрированным face tracking."""
    
    kind = "video"
    
    def __init__(self, track, face_tracker: FaceTracker):
        super().__init__()
        self.track = track
        self.face_tracker = face_tracker
        logger.info("FaceTrackingVideoTrack инициализирован")
    
    async def recv(self):
        """Получение и обработка кадра."""
        frame = await self.track.recv()
        
        # Обработка кадра для face tracking
        try:
            metrics = self.face_tracker.process_frame(frame)
            
            # Можно добавить метрики как метаданные к кадру
            # (если VideoSDK поддерживает метаданные)
            
        except Exception as e:
            logger.error(f"Ошибка в face tracking: {e}")
        
        # Возвращаем оригинальный кадр без изменений
        return frame

def create_face_tracker(config: Optional[Dict[str, Any]] = None) -> FaceTracker:
    """Создание экземпляра FaceTracker с конфигурацией."""
    if config is None:
        config = {}
    
    return FaceTracker(
        face_detection_confidence=config.get("face_detection_confidence", 0.5),
        face_tracking_confidence=config.get("face_tracking_confidence", 0.5),
        max_num_faces=config.get("max_num_faces", 1),
        gaze_threshold=config.get("gaze_threshold", 30.0),
        blink_threshold=config.get("blink_threshold", 0.25),
        distraction_min_duration=config.get("distraction_min_duration", 2.0)
    )

def create_face_tracking_video_track(track, face_tracker: FaceTracker) -> FaceTrackingVideoTrack:
    """Создание video track с face tracking."""
    return FaceTrackingVideoTrack(track, face_tracker)
