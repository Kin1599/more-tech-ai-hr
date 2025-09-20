# 🚀 Руководство по потоковому получению информации

Полное руководство по использованию потокового режима в агентных компонентах LLM, TTS, STT и VLM.

## 📋 Обзор улучшений

### ✅ **LLM (GroqLLM)**
- **Статус**: ✅ Уже реализовано
- **Улучшения**: Оптимизированная обработка потоковых чанков
- **Файл**: `groq_llm.py:199` - `stream: True`

### 🆕 **TTS (GroqTTSFixed)**
- **Статус**: 🆕 Добавлено потоковое получение
- **Улучшения**: 
  - Разбивка длинных текстов на предложения
  - Потоковый синтез для текстов > 100 символов
  - Оптимизированная обработка аудио чанков
- **Файл**: `groq_tts_fixed.py:232-284`

### 🆕 **STT (GroqSTT)**
- **Статус**: 🆕 Добавлено потоковое получение
- **Улучшения**:
  - Промежуточные результаты каждые 5 секунд
  - Потоковая обработка аудио буфера
  - Поддержка PARTIAL и FINAL событий
- **Файл**: `groq_stt.py:171-233`

### 🆕 **VLM (Vision Models)**
- **Статус**: 🆕 Добавлено потоковое получение
- **Улучшения**:
  - Поддержка Groq, OpenAI и кастомных endpoints
  - Потоковый анализ изображений
  - Адаптер для совместимости с существующими VLM
- **Файл**: `streaming_vlm.py` (новый)

## 🔧 Конфигурация потокового режима

### Переменные окружения

```bash
# LLM настройки
LLM_STREAMING=enabled          # enabled, disabled, auto
LLM_CHUNK_SIZE=50              # Размер чанка для LLM

# TTS настройки
TTS_STREAMING=enabled          # enabled, disabled, auto
TTS_SENTENCE_THRESHOLD=100     # Минимальная длина для потокового TTS
TTS_CHUNK_DELAY=0.1           # Задержка между чанками (секунды)

# STT настройки
STT_STREAMING=enabled          # enabled, disabled, auto
STT_PARTIAL_RESULTS=true       # Промежуточные результаты
STT_BUFFER_SIZE=3              # Размер буфера в секундах

# VLM настройки
VLM_STREAMING=auto             # enabled, disabled, auto
VLM_STREAMING_THRESHOLD=2000   # Минимальная длина ответа

# Общие настройки
ENABLE_ADAPTIVE_STREAMING=true # Адаптивное потоковое получение
STREAMING_TIMEOUT=30.0         # Таймаут для потоковых операций
MAX_CONCURRENT_STREAMS=3       # Максимальное количество потоков
```

### Программная конфигурация

```python
from videosdk.streaming_config import StreamingConfig, StreamingMode, load_preset_config

# Использование предустановленных конфигураций
config = load_preset_config("performance")  # performance, balanced, quality, realtime

# Или создание кастомной конфигурации
config = StreamingConfig(
    llm_streaming=StreamingMode.ENABLED,
    tts_streaming=StreamingMode.AUTO,
    stt_streaming=StreamingMode.ENABLED,
    vlm_streaming=StreamingMode.AUTO,
    enable_adaptive_streaming=True
)
```

## 🎯 Предустановленные конфигурации

### 🚀 **Performance** - Максимальная производительность
```python
config = load_preset_config("performance")
```
- Все компоненты в потоковом режиме
- Быстрые таймауты (15 сек)
- До 5 одновременных потоков
- Оптимизировано для скорости

### ⚖️ **Balanced** - Сбалансированный режим
```python
config = load_preset_config("balanced")
```
- Адаптивное включение потокового режима
- Умеренные таймауты (30 сек)
- До 3 одновременных потоков
- Оптимальное соотношение скорости и качества

### 🎨 **Quality** - Максимальное качество
```python
config = load_preset_config("quality")
```
- Потоковое получение отключено
- Длинные таймауты (60 сек)
- Только 1 поток
- Максимальное качество ответов

### ⚡ **Realtime** - Реальное время
```python
config = load_preset_config("realtime")
```
- Все компоненты в потоковом режиме
- Очень быстрые таймауты (10 сек)
- До 10 одновременных потоков
- Минимальные задержки

## 📝 Примеры использования

### LLM с потоковым получением

```python
from videosdk.groq_llm import GroqLLM
from videosdk.streaming_config import get_streaming_config

# Получаем конфигурацию
config = get_streaming_config()

# Создаем LLM с потоковым режимом
llm = GroqLLM(
    model="qwen3-32b",
    temperature=0.7
)

# Потоковое получение ответа
async for chunk in llm.chat(messages):
    print(f"Получен чанк: {chunk.content}")
```

### TTS с потоковым синтезом

```python
from videosdk.groq_tts_fixed import GroqTTSFixed

# Создаем TTS с потоковым режимом
tts = GroqTTSFixed(
    model="playai-tts",
    voice="Fritz-PlayAI"
)

# Потоковый синтез длинного текста
long_text = "Это очень длинный текст, который будет синтезирован потоково..."
await tts.synthesize(long_text)
```

### STT с промежуточными результатами

```python
from videosdk.groq_stt import GroqSTT

# Создаем STT с потоковым режимом
stt = GroqSTT(
    model="whisper-large-v3",
    silence_threshold=0.05,
    silence_duration=1.2
)

# Обработка аудио с промежуточными результатами
async def on_transcript(response):
    if response.event_type == SpeechEventType.PARTIAL:
        print(f"Промежуточный результат: {response.data.text}")
    elif response.event_type == SpeechEventType.FINAL:
        print(f"Финальный результат: {response.data.text}")

stt.on_stt_transcript(on_transcript)
```

### VLM с потоковым анализом

```python
from videosdk.streaming_vlm import StreamingVLMFactory
from PIL import Image

# Создаем потоковый VLM
config = {
    "provider": "groq",
    "model_name": "llava-13b",
    "api_key": "your-api-key"
}

streaming_vlm = StreamingVLMFactory.create_streaming_vlm(config)

# Потоковый анализ изображения
image = Image.open("screenshot.png")
async for chunk in streaming_vlm.analyze_image_streaming(image, "Проанализируй это изображение"):
    print(f"Получен чанк анализа: {chunk}")
```

## 🔄 Интеграция с существующими компонентами

### Обновление модели фабрики

```python
from videosdk.model_factory import ModelFactory

# Создание VLM с потоковым режимом
config = {
    "name": "Streaming Groq VLM",
    "provider": "groq",
    "model_name": "llava-13b",
    "api_key_name": "GROQ_API_KEY",
    "enable_streaming": True,  # Включаем потоковый режим
    "temperature": 0.7,
    "max_tokens": 2048
}

vision_model = ModelFactory.create_vision_model(config)
```

### Использование в агентах

```python
from videosdk.main import InterviewAgent
from videosdk.streaming_config import load_preset_config

# Загружаем конфигурацию производительности
config = load_preset_config("performance")

# Создаем агента с потоковым режимом
agent = InterviewAgent(
    system_prompt="Ты полезный ассистент для интервью",
    streaming_config=config
)
```

## 📊 Мониторинг и отладка

### Логирование потоковых операций

```python
import logging

# Настройка логирования для потоковых операций
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("videosdk.streaming")

# Логи будут показывать:
# - Начало потоковых операций
# - Размеры чанков
# - Время обработки
# - Ошибки потокового режима
```

### Метрики производительности

```python
from videosdk.streaming_config import get_streaming_config

config = get_streaming_config()

# Получение метрик
metrics = {
    "llm_chunk_size": config.llm_chunk_size,
    "tts_sentence_threshold": config.tts_sentence_threshold,
    "stt_buffer_size": config.stt_buffer_size,
    "streaming_timeout": config.streaming_timeout,
    "max_concurrent_streams": config.max_concurrent_streams
}

print(f"Текущие настройки потокового режима: {metrics}")
```

## 🚨 Устранение неполадок

### Частые проблемы

1. **Медленное потоковое получение**
   - Уменьшите `STREAMING_TIMEOUT`
   - Увеличьте `MAX_CONCURRENT_STREAMS`
   - Используйте конфигурацию "performance"

2. **Высокое потребление памяти**
   - Уменьшите размеры буферов
   - Используйте конфигурацию "balanced"
   - Отключите адаптивное потоковое получение

3. **Ошибки таймаута**
   - Увеличьте `STREAMING_TIMEOUT`
   - Проверьте стабильность сети
   - Используйте конфигурацию "quality"

### Отладка

```python
# Включение подробного логирования
import os
os.environ["VIDEOSDK_DEBUG"] = "true"
os.environ["STREAMING_DEBUG"] = "true"

# Проверка конфигурации
from videosdk.streaming_config import get_streaming_config
config = get_streaming_config()
print(f"Текущая конфигурация: {config}")
```

## 🎯 Рекомендации по использованию

### Для интервью в реальном времени
```python
config = load_preset_config("realtime")
```

### Для качественного анализа документов
```python
config = load_preset_config("quality")
```

### Для баланса скорости и качества
```python
config = load_preset_config("balanced")
```

### Для максимальной производительности
```python
config = load_preset_config("performance")
```

## 📈 Производительность

### Ожидаемые улучшения

- **LLM**: Уменьшение задержки первого токена на 30-50%
- **TTS**: Сокращение времени до начала воспроизведения на 40-60%
- **STT**: Получение промежуточных результатов каждые 3-5 секунд
- **VLM**: Потоковый анализ сложных изображений

### Мониторинг производительности

```python
import time
from videosdk.streaming_config import get_streaming_config

config = get_streaming_config()

# Измерение времени ответа
start_time = time.time()
# ... выполнение потоковой операции ...
end_time = time.time()

response_time = end_time - start_time
print(f"Время ответа: {response_time:.2f} секунд")
```

## 🔮 Будущие улучшения

- Поддержка WebSocket для STT
- Адаптивное качество для TTS
- Кэширование результатов VLM
- Машинное обучение для оптимизации потокового режима
