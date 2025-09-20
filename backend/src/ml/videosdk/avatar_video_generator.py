"""
AI Avatar Video Generator - Генерация talking и idle кадров для аватара.

Создает видеопоток с AI аватаром, который реагирует на речь и эмоции,
проецируя результат на фронтенд поверх экрана участника.
"""

import asyncio
import time
import logging
import base64
import io
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from av import VideoFrame
from videosdk import CustomVideoTrack

logger = logging.getLogger(__name__)

@dataclass
class AvatarState:
    """Состояние аватара в конкретный момент."""
    timestamp: float
    is_talking: bool
    emotion: str  # neutral, happy, sad, surprised, angry
    mouth_openness: float  # 0.0 - закрыт, 1.0 - максимально открыт
    eye_blink: bool
    head_movement: Tuple[float, float, float]  # yaw, pitch, roll
    speech_intensity: float  # 0.0 - тишина, 1.0 - громкая речь

@dataclass
class AvatarConfig:
    """Конфигурация аватара."""
    avatar_type: str = "simli"  # simli, custom, placeholder
    face_id: Optional[str] = None
    resolution: Tuple[int, int] = (640, 480)
    fps: int = 30
    talking_sensitivity: float = 0.3
    emotion_detection: bool = True
    head_movement_enabled: bool = True
    eye_blink_enabled: bool = True
    background_color: Tuple[int, int, int] = (50, 50, 50)
    avatar_scale: float = 0.8

class AvatarVideoGenerator:
    """Генератор видеопотока для AI аватара."""
    
    def __init__(self, config: AvatarConfig):
        self.config = config
        self.current_state = AvatarState(
            timestamp=time.time(),
            is_talking=False,
            emotion="neutral",
            mouth_openness=0.0,
            eye_blink=False,
            head_movement=(0.0, 0.0, 0.0),
            speech_intensity=0.0
        )
        
        # История состояний для плавных переходов
        self.state_history: List[AvatarState] = []
        self.max_history_size = 10
        
        # Настройки анимации
        self.blink_duration = 0.15  # секунды
        self.last_blink_time = 0.0
        self.blink_interval_range = (2.0, 4.0)  # случайный интервал между морганиями
        self.next_blink_time = time.time() + np.random.uniform(*self.blink_interval_range)
        
        # Настройки движения рта
        self.mouth_animation_speed = 0.1
        self.target_mouth_openness = 0.0
        
        # Настройки движения головы
        self.head_animation_speed = 0.05
        self.target_head_movement = (0.0, 0.0, 0.0)
        
        # Инициализация аватара
        self.avatar_instance = None
        self._initialize_avatar()
        
        logger.info(f"AvatarVideoGenerator инициализирован: {config.avatar_type}")
    
    def _initialize_avatar(self):
        """Инициализация конкретного типа аватара."""
        try:
            if self.config.avatar_type == "simli":
                self._initialize_simli_avatar()
            elif self.config.avatar_type == "custom":
                self._initialize_custom_avatar()
            else:
                self._initialize_placeholder_avatar()
        except Exception as e:
            logger.error(f"Ошибка инициализации аватара: {e}")
            self._initialize_placeholder_avatar()
    
    def _initialize_simli_avatar(self):
        """Инициализация Simli аватара."""
        try:
            from videosdk.plugins.simli import SimliAvatar, SimliConfig
            
            simli_config = SimliConfig(
                face_id=self.config.face_id or "default_face",
                api_key_name="SIMLI_API_KEY",
                max_session_length=3600,
                max_idle_time=300
            )
            
            self.avatar_instance = SimliAvatar(simli_config)
            logger.info("Simli аватар инициализирован")
            
        except ImportError:
            logger.warning("Simli зависимости недоступны, используем placeholder")
            self._initialize_placeholder_avatar()
        except Exception as e:
            logger.error(f"Ошибка инициализации Simli: {e}")
            self._initialize_placeholder_avatar()
    
    def _initialize_custom_avatar(self):
        """Инициализация кастомного аватара."""
        # Здесь можно добавить логику для кастомных аватаров
        logger.info("Кастомный аватар инициализирован (заглушка)")
        self._initialize_placeholder_avatar()
    
    def _initialize_placeholder_avatar(self):
        """Инициализация placeholder аватара."""
        logger.info("Placeholder аватар инициализирован")
        self.avatar_instance = "placeholder"
    
    def update_speech_data(self, 
                          is_speaking: bool, 
                          speech_intensity: float = 0.0,
                          audio_data: Optional[bytes] = None):
        """Обновление данных речи для анимации."""
        current_time = time.time()
        
        # Обновляем состояние речи
        self.current_state.is_talking = is_speaking
        self.current_state.speech_intensity = speech_intensity
        self.current_state.timestamp = current_time
        
        # Обновляем целевое открытие рта
        if is_speaking:
            # Более интенсивная речь = более открытый рот
            self.target_mouth_openness = min(0.8, speech_intensity * 0.9)
        else:
            self.target_mouth_openness = 0.0
        
        # Анализ эмоций из аудио (если доступно)
        if audio_data and self.config.emotion_detection:
            emotion = self._analyze_emotion_from_audio(audio_data)
            self.current_state.emotion = emotion
        
        # Добавляем в историю
        self._add_to_history(self.current_state)
    
    def update_face_tracking_data(self, face_data: Dict[str, Any]):
        """Обновление данных face tracking для движения головы."""
        if not self.config.head_movement_enabled:
            return
        
        # Извлекаем данные о движении головы
        head_pose = face_data.get("head_pose", {})
        yaw = head_pose.get("yaw", 0.0)
        pitch = head_pose.get("pitch", 0.0)
        roll = head_pose.get("roll", 0.0)
        
        # Обновляем целевое движение головы (сглаживаем)
        self.target_head_movement = (
            yaw * 0.3,   # Ограничиваем амплитуду
            pitch * 0.3,
            roll * 0.2
        )
        
        # Обновляем моргание
        if self.config.eye_blink_enabled:
            self._update_blink_state(face_data)
    
    def _analyze_emotion_from_audio(self, audio_data: bytes) -> str:
        """Простой анализ эмоций из аудиоданных."""
        try:
            # Здесь можно добавить более сложный анализ эмоций
            # Пока возвращаем нейтральную эмоцию
            return "neutral"
        except Exception as e:
            logger.warning(f"Ошибка анализа эмоций: {e}")
            return "neutral"
    
    def _update_blink_state(self, face_data: Dict[str, Any]):
        """Обновление состояния моргания."""
        current_time = time.time()
        
        # Проверяем, нужно ли моргнуть
        if current_time >= self.next_blink_time:
            self.current_state.eye_blink = True
            self.last_blink_time = current_time
            self.next_blink_time = current_time + np.random.uniform(*self.blink_interval_range)
        else:
            # Проверяем, закончилось ли моргание
            if (self.current_state.eye_blink and 
                current_time - self.last_blink_time > self.blink_duration):
                self.current_state.eye_blink = False
    
    def _add_to_history(self, state: AvatarState):
        """Добавление состояния в историю."""
        self.state_history.append(state)
        
        # Ограничиваем размер истории
        if len(self.state_history) > self.max_history_size:
            self.state_history.pop(0)
    
    def generate_frame(self) -> VideoFrame:
        """Генерация одного кадра аватара."""
        current_time = time.time()
        
        # Обновляем анимации
        self._update_animations(current_time)
        
        # Создаем кадр
        if self.config.avatar_type == "simli" and self.avatar_instance != "placeholder":
            frame = self._generate_simli_frame()
        else:
            frame = self._generate_placeholder_frame()
        
        return frame
    
    def _update_animations(self, current_time: float):
        """Обновление анимаций между кадрами."""
        # Плавное изменение открытия рта
        current_mouth = self.current_state.mouth_openness
        diff = self.target_mouth_openness - current_mouth
        self.current_state.mouth_openness = current_mouth + diff * self.mouth_animation_speed
        
        # Плавное движение головы
        current_head = self.current_state.head_movement
        target_head = self.target_head_movement
        
        new_head = (
            current_head[0] + (target_head[0] - current_head[0]) * self.head_animation_speed,
            current_head[1] + (target_head[1] - current_head[1]) * self.head_animation_speed,
            current_head[2] + (target_head[2] - current_head[2]) * self.head_animation_speed
        )
        
        self.current_state.head_movement = new_head
    
    def _generate_simli_frame(self) -> VideoFrame:
        """Генерация кадра с Simli аватаром."""
        try:
            # Здесь должен быть вызов Simli API для генерации кадра
            # Пока используем placeholder
            return self._generate_placeholder_frame()
        except Exception as e:
            logger.error(f"Ошибка генерации Simli кадра: {e}")
            return self._generate_placeholder_frame()
    
    def _generate_placeholder_frame(self) -> VideoFrame:
        """Генерация placeholder кадра."""
        width, height = self.config.resolution
        
        # Создаем изображение
        img = Image.new('RGB', (width, height), self.config.background_color)
        draw = ImageDraw.Draw(img)
        
        # Рисуем простой аватар
        self._draw_placeholder_avatar(draw, width, height)
        
        # Конвертируем в numpy array
        img_array = np.array(img)
        
        # Создаем VideoFrame
        frame = VideoFrame.from_ndarray(img_array, format="rgb24")
        frame.pts = int(time.time() * 1000000)  # микросекунды
        frame.time_base = (1, 1000000)
        
        return frame
    
    def _draw_placeholder_avatar(self, draw: ImageDraw.Draw, width: int, height: int):
        """Отрисовка простого placeholder аватара."""
        center_x, center_y = width // 2, height // 2
        avatar_size = min(width, height) * self.config.avatar_scale
        
        # Получаем текущее состояние
        state = self.current_state
        
        # Голова (круг)
        head_radius = int(avatar_size * 0.3)
        head_color = (200, 180, 160)  # телесный цвет
        
        # Движение головы
        head_offset_x = int(state.head_movement[0] * 20)  # yaw
        head_offset_y = int(state.head_movement[1] * 15)  # pitch
        
        head_x = center_x + head_offset_x
        head_y = center_y + head_offset_y
        
        draw.ellipse(
            [head_x - head_radius, head_y - head_radius, 
             head_x + head_radius, head_y + head_radius],
            fill=head_color,
            outline=(150, 130, 110),
            width=2
        )
        
        # Глаза
        eye_y = head_y - head_radius * 0.3
        eye_size = int(head_radius * 0.15)
        
        # Левый глаз
        left_eye_x = head_x - head_radius * 0.3
        if state.eye_blink:
            # Закрытый глаз
            draw.line(
                [left_eye_x - eye_size, eye_y, left_eye_x + eye_size, eye_y],
                fill=(0, 0, 0),
                width=3
            )
        else:
            # Открытый глаз
            draw.ellipse(
                [left_eye_x - eye_size, eye_y - eye_size,
                 left_eye_x + eye_size, eye_y + eye_size],
                fill=(255, 255, 255),
                outline=(0, 0, 0),
                width=2
            )
            # Зрачок
            pupil_size = eye_size // 2
            draw.ellipse(
                [left_eye_x - pupil_size, eye_y - pupil_size,
                 left_eye_x + pupil_size, eye_y + pupil_size],
                fill=(0, 0, 0)
            )
        
        # Правый глаз
        right_eye_x = head_x + head_radius * 0.3
        if state.eye_blink:
            # Закрытый глаз
            draw.line(
                [right_eye_x - eye_size, eye_y, right_eye_x + eye_size, eye_y],
                fill=(0, 0, 0),
                width=3
            )
        else:
            # Открытый глаз
            draw.ellipse(
                [right_eye_x - eye_size, eye_y - eye_size,
                 right_eye_x + eye_size, eye_y + eye_size],
                fill=(255, 255, 255),
                outline=(0, 0, 0),
                width=2
            )
            # Зрачок
            pupil_size = eye_size // 2
            draw.ellipse(
                [right_eye_x - pupil_size, eye_y - pupil_size,
                 right_eye_x + pupil_size, eye_y + pupil_size],
                fill=(0, 0, 0)
            )
        
        # Рот
        mouth_y = head_y + head_radius * 0.4
        mouth_width = int(head_radius * 0.4)
        
        if state.is_talking:
            # Открытый рот (говорит)
            mouth_height = int(state.mouth_openness * head_radius * 0.3)
            draw.ellipse(
                [head_x - mouth_width//2, mouth_y - mouth_height//2,
                 head_x + mouth_width//2, mouth_y + mouth_height//2],
                fill=(100, 50, 50),
                outline=(80, 40, 40),
                width=2
            )
        else:
            # Закрытый рот (нейтральное выражение)
            draw.arc(
                [head_x - mouth_width//2, mouth_y - mouth_width//4,
                 head_x + mouth_width//2, mouth_y + mouth_width//4],
                start=0,
                end=180,
                fill=(100, 50, 50),
                width=3
            )
        
        # Индикатор состояния
        status_y = height - 30
        status_text = f"AI Avatar - {state.emotion}"
        if state.is_talking:
            status_text += " (Speaking)"
        
        try:
            # Пытаемся использовать системный шрифт
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, status_y), status_text, fill=(255, 255, 255), font=font)
        
        # Индикатор интенсивности речи
        if state.is_talking:
            intensity_bar_width = int(state.speech_intensity * 100)
            draw.rectangle(
                [10, status_y + 20, 10 + intensity_bar_width, status_y + 25],
                fill=(0, 255, 0)
            )

class AvatarVideoTrack(CustomVideoTrack):
    """Custom video track для AI аватара."""
    
    kind = "video"
    
    def __init__(self, avatar_generator: AvatarVideoGenerator):
        super().__init__()
        self.avatar_generator = avatar_generator
        self.frame_count = 0
        self.start_time = time.time()
        
        logger.info("AvatarVideoTrack инициализирован")
    
    async def recv(self):
        """Получение следующего кадра аватара."""
        try:
            # Генерируем кадр
            frame = self.avatar_generator.generate_frame()
            
            # Устанавливаем временные метки
            current_time = time.time()
            frame.pts = int((current_time - self.start_time) * 1000000)
            frame.time_base = (1, 1000000)
            
            self.frame_count += 1
            
            # Контроль FPS
            target_frame_time = 1.0 / self.avatar_generator.config.fps
            await asyncio.sleep(target_frame_time)
            
            return frame
            
        except Exception as e:
            logger.error(f"Ошибка генерации кадра аватара: {e}")
            # Возвращаем пустой кадр в случае ошибки
            return self._create_empty_frame()
    
    def _create_empty_frame(self) -> VideoFrame:
        """Создание пустого кадра в случае ошибки."""
        width, height = self.avatar_generator.config.resolution
        img_array = np.zeros((height, width, 3), dtype=np.uint8)
        frame = VideoFrame.from_ndarray(img_array, format="rgb24")
        frame.pts = int(time.time() * 1000000)
        frame.time_base = (1, 1000000)
        return frame
    
    def update_speech(self, is_speaking: bool, intensity: float = 0.0, audio_data: Optional[bytes] = None):
        """Обновление данных речи."""
        self.avatar_generator.update_speech_data(is_speaking, intensity, audio_data)
    
    def update_face_tracking(self, face_data: Dict[str, Any]):
        """Обновление данных face tracking."""
        self.avatar_generator.update_face_tracking_data(face_data)

def create_avatar_generator(config: Optional[Dict[str, Any]] = None) -> AvatarVideoGenerator:
    """Создание генератора аватара с конфигурацией."""
    if config is None:
        config = {}
    
    avatar_config = AvatarConfig(
        avatar_type=config.get("avatar_type", "simli"),
        face_id=config.get("face_id"),
        resolution=tuple(config.get("resolution", [640, 480])),
        fps=config.get("fps", 30),
        talking_sensitivity=config.get("talking_sensitivity", 0.3),
        emotion_detection=config.get("emotion_detection", True),
        head_movement_enabled=config.get("head_movement_enabled", True),
        eye_blink_enabled=config.get("eye_blink_enabled", True),
        background_color=tuple(config.get("background_color", [50, 50, 50])),
        avatar_scale=config.get("avatar_scale", 0.8)
    )
    
    return AvatarVideoGenerator(avatar_config)

def create_avatar_video_track(avatar_generator: AvatarVideoGenerator) -> AvatarVideoTrack:
    """Создание video track для аватара."""
    return AvatarVideoTrack(avatar_generator)
