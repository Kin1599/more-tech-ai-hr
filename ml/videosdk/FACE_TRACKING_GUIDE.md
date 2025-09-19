# 👁️ Face Detection & Eye Tracking - Мониторинг поведения кандидата

Полное руководство по интеграции системы отслеживания лица и глаз для анализа внимательности и поведения кандидатов во время интервью.

## 🎯 Возможности Face Tracking

### ✅ **Face Detection**
- **Детекция присутствия** лица в кадре с уровнем уверенности
- **Bounding box** координаты лица
- **Устойчивое отслеживание** даже при частичном перекрытии
- **Адаптация к освещению** и различным углам

### ✅ **Eye Tracking & Gaze Analysis**
- **Направление взгляда** (горизонтальное и вертикальное отклонение)
- **Eye Aspect Ratio (EAR)** для детекции моргания
- **Детекция "смотрит в сторону"** с настраиваемыми порогами
- **Анализ концентрации** внимания

### ✅ **Head Pose Estimation**
- **Yaw** (поворот влево-вправо)
- **Pitch** (наклон вверх-вниз)  
- **Roll** (наклон влево-вправо)
- **Определение отвлечений** по позе головы

### ✅ **Behavioral Analytics**
- **Статистика присутствия** в кадре
- **Коэффициент внимательности** за период
- **Частота отвлечений** в минуту
- **Анализ паттернов** моргания и стресса

## 🔧 Техническая реализация

### **Основанное на MediaPipe**
Использует [MediaPipe Face Detection](https://docs.videosdk.live/python/guide/video-and-audio-calling/ai-and-ml/face-detection) и Face Mesh для высокоточного анализа:

```python
# Инициализация детекторов
self.face_detection = mp.solutions.face_detection.FaceDetection(
    min_detection_confidence=0.5
)
self.face_mesh = mp.solutions.face_mesh.FaceMesh(
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    refine_landmarks=True
)
```

### **Ключевые алгоритмы**

#### **1. Eye Aspect Ratio (EAR) для моргания**
```python
def calculate_eye_aspect_ratio(self, landmarks, ear_indices):
    # Вертикальные расстояния
    A = distance(landmarks[ear_indices[1]], landmarks[ear_indices[5]])
    B = distance(landmarks[ear_indices[2]], landmarks[ear_indices[4]])
    
    # Горизонтальное расстояние
    C = distance(landmarks[ear_indices[0]], landmarks[ear_indices[3]])
    
    # EAR формула
    ear = (A + B) / (2.0 * C)
    return ear
```

#### **2. Gaze Direction Estimation**
```python
def estimate_gaze_direction(self, landmarks, width, height):
    nose_tip = landmarks[NOSE_TIP_INDEX]
    eye_center = (left_eye + right_eye) / 2
    
    # Вектор направления взгляда
    gaze_vector = nose_tip - eye_center
    
    # Углы в градусах
    gaze_x = arctan2(gaze_vector.x, abs(gaze_vector.y)) * 180 / π
    gaze_y = arctan2(gaze_vector.y, abs(gaze_vector.x)) * 180 / π
    
    return gaze_x, gaze_y
```

#### **3. Attention Analysis**
```python
def analyze_attention_events(self, metrics):
    is_looking_away = (
        not metrics.face_detected or
        abs(metrics.gaze_direction_x) > self.gaze_threshold or
        abs(metrics.gaze_direction_y) > self.gaze_threshold
    )
    
    # Отслеживание периодов отвлечения
    if is_looking_away and not self.current_distraction_start:
        self.current_distraction_start = time.time()
    elif not is_looking_away and self.current_distraction_start:
        duration = time.time() - self.current_distraction_start
        if duration >= self.distraction_min_duration:
            self.record_distraction_event(duration)
```

## 🎮 Интеграция в интервью

### **Автоматическая интеграция**
Face tracking автоматически интегрируется в `InterviewAgent`:

```python
class InterviewAgent(Agent):
    def __init__(self, applicant_id: int, vacancy_id: int):
        # Инициализация Face Tracker
        face_tracking_config = self.db_config.get("face_tracking_config", {})
        self.face_tracker = create_face_tracker(face_tracking_config)
        
    def process_video_stream(self, track):
        """Обработка видео потока с face tracking."""
        if self.face_tracker:
            face_tracking_track = create_face_tracking_video_track(track, self.face_tracker)
            self.session.meeting.add_custom_video_track(track=face_tracking_track)
```

### **Конфигурация через базу данных**
```python
# В db_config можно указать параметры face tracking
face_tracking_config = {
    "face_detection_confidence": 0.7,  # Высокая точность детекции
    "gaze_threshold": 25.0,            # Строже порог отвлечения  
    "blink_threshold": 0.25,           # Стандартный порог моргания
    "distraction_min_duration": 1.5    # Быстрая детекция отвлечений
}
```

## 📊 Метрики и аналитика

### **FaceMetrics - Мгновенные данные**
```python
@dataclass
class FaceMetrics:
    timestamp: float
    face_detected: bool
    face_confidence: float
    face_bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    
    # Eye tracking
    left_eye_landmarks: List[Tuple[float, float]]
    right_eye_landmarks: List[Tuple[float, float]]
    eye_aspect_ratio_left: float
    eye_aspect_ratio_right: float
    
    # Gaze analysis
    gaze_direction_x: float  # -90 до 90 градусов
    gaze_direction_y: float  # -90 до 90 градусов
    
    # Head pose
    head_pose_yaw: float     # поворот влево-вправо
    head_pose_pitch: float   # наклон вверх-вниз
    head_pose_roll: float    # наклон влево-вправо
```

### **AttentionStats - Агрегированная статистика**
```python
@dataclass
class AttentionStats:
    total_duration: float                    # Общая длительность
    face_present_duration: float             # Время с лицом в кадре
    looking_away_duration: float             # Время отвлечений
    blink_count: int                         # Количество морганий
    distraction_events: List[Dict]           # События отвлечения
    
    @property
    def face_presence_ratio(self) -> float:  # % времени в кадре
        return self.face_present_duration / self.total_duration
    
    @property  
    def attention_ratio(self) -> float:      # % времени внимательности
        attention_time = self.face_present_duration - self.looking_away_duration
        return attention_time / self.total_duration
    
    @property
    def distraction_frequency(self) -> float: # Отвлечений в минуту
        minutes = self.total_duration / 60.0
        return len(self.distraction_events) / minutes
```

## 🎯 Практические сценарии использования

### **1. Мониторинг внимательности**
```python
# Получение текущего статуса
status = agent.get_face_tracking_stats()

print(f"Присутствие в кадре: {status['stats']['face_presence_ratio']*100:.1f}%")
print(f"Уровень внимания: {status['stats']['attention_ratio']*100:.1f}%") 
print(f"Частота отвлечений: {status['stats']['distraction_frequency']:.1f}/мин")

# Текущее состояние
current = status['current_status']
print(f"Лицо обнаружено: {current['face_detected']}")
print(f"Уровень внимания: {current['attention_level']}")
print(f"Направление взгляда: x={current['gaze_direction']['x']:.1f}°, y={current['gaze_direction']['y']:.1f}°")
```

### **2. Поведенческие инсайты**
```python
# Получение детального анализа
insights = agent.get_behavioral_insights()

for insight in insights['insights']:
    print(f"[{insight['level'].upper()}] {insight['type']}: {insight['message']}")
    print(f"Рекомендация: {insight['recommendation']}")

# Общая оценка
summary = insights['summary']
print(f"Общая вовлеченность: {summary['overall_engagement']}")
print(f"Качество присутствия: {summary['presence_quality']}")
print(f"Уровень отвлечений: {summary['distraction_level']}")
```

### **3. Интеграция в финальный отчет**
```python
# При завершении интервью автоматически сохраняется:
interview_results = {
    "candidate_responses": [...],
    "ai_evaluation": {...},
    
    # Face tracking данные
    "face_tracking_stats": {
        "face_presence_ratio": 0.92,      # 92% времени в кадре
        "attention_ratio": 0.85,          # 85% времени внимателен
        "distraction_frequency": 1.2,     # 1.2 отвлечения в минуту
        "blink_count": 45                 # 45 морганий за интервью
    },
    
    "behavioral_insights": [
        {
            "type": "attention",
            "level": "positive", 
            "message": "Высокий уровень внимательности: 85.0%",
            "recommendation": "Кандидат демонстрировал отличную концентрацию"
        }
    ],
    
    "engagement_summary": {
        "overall_engagement": "high",
        "presence_quality": "good", 
        "distraction_level": "low"
    }
}
```

## 🔧 Настройка параметров

### **Основные параметры**
```python
face_tracking_config = {
    # Детекция лица
    "face_detection_confidence": 0.5,    # 0.1-1.0, порог уверенности
    "face_tracking_confidence": 0.5,     # 0.1-1.0, порог трекинга
    "max_num_faces": 1,                  # Количество лиц для отслеживания
    
    # Анализ взгляда
    "gaze_threshold": 30.0,              # 10-60 градусов, порог "смотрит в сторону"
    
    # Детекция моргания
    "blink_threshold": 0.25,             # 0.1-0.4, порог EAR для моргания
    
    # Анализ отвлечений
    "distraction_min_duration": 2.0      # 1-5 секунд, мин. длительность отвлечения
}
```

### **Рекомендуемые настройки**

#### **Строгий режим (детальный анализ)**
```python
strict_config = {
    "face_detection_confidence": 0.7,    # Высокая точность
    "gaze_threshold": 20.0,               # Строгий контроль взгляда
    "blink_threshold": 0.3,               # Чувствительная детекция моргания
    "distraction_min_duration": 1.0      # Быстрая фиксация отвлечений
}
```

#### **Мягкий режим (для нервных кандидатов)**
```python
gentle_config = {
    "face_detection_confidence": 0.4,    # Более терпимая детекция
    "gaze_threshold": 40.0,               # Больше свободы для взгляда
    "blink_threshold": 0.2,               # Менее чувствительное моргание
    "distraction_min_duration": 3.0      # Дольше ждем отвлечения
}
```

#### **Стандартный режим (сбалансированный)**
```python
standard_config = {
    "face_detection_confidence": 0.5,
    "gaze_threshold": 30.0,
    "blink_threshold": 0.25,
    "distraction_min_duration": 2.0
}
```

## 🚀 API для тестирования

### **Тестирование на изображении**
```bash
# Загрузка изображения для анализа
POST /face-tracking/test/upload
Content-Type: multipart/form-data

# Параметры:
# - file: изображение
# - face_detection_confidence: 0.5
# - gaze_threshold: 30.0
# - blink_threshold: 0.25

# Ответ:
{
    "success": true,
    "metrics": {
        "face_detected": true,
        "face_confidence": 0.89,
        "attention_level": "high",
        "gaze_direction_x": -5.2,
        "gaze_direction_y": 2.1,
        "is_looking_away": false,
        "is_blinking": false
    },
    "processing_time_ms": 45.2,
    "analysis_summary": {
        "confidence_level": "high",
        "attention_assessment": "high",
        "gaze_analysis": {
            "horizontal_deviation": 5.2,
            "vertical_deviation": 2.1,
            "looking_away": false
        }
    }
}
```

### **Получение статистики**
```bash
# Статистика внимательности
GET /face-tracking/stats

{
    "total_duration": 120.5,
    "face_presence_ratio": 0.92,
    "attention_ratio": 0.85,
    "distraction_frequency": 1.2,
    "blink_count": 45,
    "distraction_events_count": 3
}
```

### **Поведенческие инсайты**
```bash
# Детальный анализ поведения
GET /face-tracking/insights

{
    "overall_engagement": "high",
    "presence_quality": "good",
    "distraction_level": "low",
    "insights": [
        {
            "type": "attention",
            "level": "positive",
            "message": "Отличная концентрация: 85.0%",
            "value": 0.85
        }
    ],
    "recommendations": [
        "Кандидат демонстрирует высокую вовлеченность"
    ]
}
```

## 📈 Интерпретация результатов

### **Уровни внимательности**

#### **Высокий уровень (High Engagement)**
- **Face Presence Ratio**: > 90%
- **Attention Ratio**: > 80%
- **Distraction Frequency**: < 1 раз/мин
- **Интерпретация**: Кандидат сосредоточен, внимателен, хорошо вовлечен

#### **Средний уровень (Medium Engagement)**  
- **Face Presence Ratio**: 70-90%
- **Attention Ratio**: 60-80%
- **Distraction Frequency**: 1-3 раза/мин
- **Интерпретация**: Нормальный уровень внимания с периодическими отвлечениями

#### **Низкий уровень (Low Engagement)**
- **Face Presence Ratio**: < 70%
- **Attention Ratio**: < 60%  
- **Distraction Frequency**: > 3 раза/мин
- **Интерпретация**: Частые отвлечения, возможные технические проблемы или незаинтересованность

### **Анализ паттернов моргания**

#### **Нормальная частота**: 15-20 раз/мин
- Спокойное состояние, нормальный уровень стресса

#### **Повышенная частота**: 25-35 раз/мин  
- Возможное волнение, концентрация, обдумывание

#### **Очень высокая частота**: > 35 раз/мин
- Сильный стресс, нервозность, дискомфорт

### **Направления взгляда**

#### **Центральный взгляд**: |x| < 15°, |y| < 15°
- Прямой контакт, высокое внимание

#### **Периферийный взгляд**: 15° < |x,y| < 30°
- Нормальные движения глаз, обдумывание

#### **Отвлеченный взгляд**: |x,y| > 30°
- Отвлечение, поиск информации, нервозность

## 🎯 Практические рекомендации

### **Для HR-специалистов**

#### **Интерпретация результатов**
- ✅ **Не судите только по метрикам** - учитывайте контекст вопросов
- ✅ **Обращайте внимание на паттерны** - важны тренды, а не отдельные моменты
- ✅ **Учитывайте технические факторы** - качество камеры, освещение, связь
- ✅ **Сопоставляйте с ответами** - отвлечения во время размышлений нормальны

#### **Красные флаги**
- 🚩 **Face Presence < 50%** - серьезные технические проблемы или намеренное избегание
- 🚩 **Attention Ratio < 40%** - очень низкая вовлеченность
- 🚩 **Distraction Frequency > 5/мин** - чрезмерная нервозность или отвлеченность
- 🚩 **Blink Rate > 50/мин** - сильный стресс

#### **Позитивные индикаторы**
- ✅ **Стабильное присутствие в кадре** - хорошая подготовка к интервью
- ✅ **Периодические взгляды в сторону** при сложных вопросах - нормальное обдумывание
- ✅ **Постепенное снижение нервозности** - адаптация к процессу интервью
- ✅ **Возвращение внимания после отвлечений** - самоконтроль

### **Для настройки системы**

#### **Оптимизация под условия**
```python
# Для плохого освещения
low_light_config = {
    "face_detection_confidence": 0.3,  # Снижаем порог
    "gaze_threshold": 35.0              # Больше терпимости
}

# Для нестабильной связи  
unstable_connection_config = {
    "distraction_min_duration": 5.0,   # Дольше ждем отвлечений
    "face_detection_confidence": 0.4   # Компенсируем артефакты
}

# Для senior позиций (более строго)
senior_position_config = {
    "gaze_threshold": 25.0,             # Строже контроль
    "distraction_min_duration": 1.5    # Быстрее фиксируем отвлечения
}
```

## 🛡️ Этические соображения

### **Прозрачность**
- ✅ **Информируйте кандидатов** о использовании face tracking
- ✅ **Объясняйте цели** - улучшение качества интервью, а не слежка
- ✅ **Предоставляйте возможность отказа** от face tracking

### **Конфиденциальность**
- ✅ **Не сохраняйте видеоданные** - только метрики
- ✅ **Ограничивайте доступ** к поведенческим данным
- ✅ **Удаляйте данные** после принятия решения

### **Справедливость**
- ✅ **Учитывайте культурные различия** в поведении
- ✅ **Не дискриминируйте** по техническим проблемам
- ✅ **Используйте как дополнительный инструмент**, а не основной критерий

## 🎉 Заключение

Face Detection и Eye Tracking предоставляют **ценные инсайты** о поведении кандидата:

- ✅ **Объективные метрики** внимательности и вовлеченности
- ✅ **Автоматический анализ** без вмешательства в процесс интервью  
- ✅ **Поведенческие паттерны** для лучшего понимания кандидата
- ✅ **Интеграция с результатами** интервью для комплексной оценки
- ✅ **Настраиваемые параметры** под различные сценарии
- ✅ **Comprehensive API** для тестирования и отладки

Теперь ваша система может **видеть и понимать** невербальное поведение кандидатов, предоставляя HR-специалистам дополнительный инструмент для принятия обоснованных решений! 👁️🤖📊

---

*Версия: 3.4.0 с Face Detection & Eye Tracking*

## 📚 Дополнительные ресурсы

- [MediaPipe Face Detection](https://google.github.io/mediapipe/solutions/face_detection.html)
- [MediaPipe Face Mesh](https://google.github.io/mediapipe/solutions/face_mesh.html)  
- [VideoSDK Face Detection Guide](https://docs.videosdk.live/python/guide/video-and-audio-calling/ai-and-ml/face-detection)
- [Eye Aspect Ratio Paper](https://pyimagesearch.com/2017/04/24/eye-blink-detection-opencv-python-dlib/)
- [Gaze Estimation Techniques](https://arxiv.org/abs/1905.04771)
