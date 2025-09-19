# 🔌 Custom Endpoint VLM - Универсальная интеграция любых Vision API

Полное руководство по подключению любых VLM API endpoints к системе собеседований с максимальной гибкостью и совместимостью.

## 🎯 Возможности Custom Endpoint

### ✅ **Универсальная совместимость**
- Поддержка **любых VLM API** с различными форматами
- **4 предустановленных формата**: OpenAI, Anthropic, Gemini, Custom
- **6 типов аутентификации**: Bearer, API-Key, Custom Header, None, и др.
- **Гибкая настройка** запросов и парсинга ответов

### ✅ **Популярные сервисы из коробки**
- **OpenAI-совместимые**: vLLM, Text Generation Inference, Oollama
- **Облачные провайдеры**: Replicate, Hugging Face, RunPod
- **Локальные сервисы**: Oollama, vLLM, TGI, FastChat
- **Корпоративные решения**: Любые внутренние API

### ✅ **Продвинутые возможности**
- **Автоматическое тестирование** endpoints
- **Health checks** и мониторинг
- **Шаблоны конфигураций** для быстрого старта
- **Детальная диагностика** ошибок

## 🔧 Поддерживаемые форматы API

### **1. OpenAI Format** ⭐ Самый популярный

Подходит для: vLLM, Text Generation Inference, Oollama (с OpenAI API), FastChat

```python
{
    "provider": "custom_endpoint",
    "endpoint_url": "http://localhost:8000",
    "model_name": "llava-hf/llava-1.5-7b-hf",
    "extra_params": {
        "request_format": "openai",
        "auth_type": "bearer",  # или "none" для локальных
        "detail": "high"
    }
}
```

**Формат запроса:**
```json
{
    "model": "llava-hf/llava-1.5-7b-hf",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Проанализируй код"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,iVBORw0KGgoAAAANS...",
                        "detail": "high"
                    }
                }
            ]
        }
    ],
    "max_tokens": 4096,
    "temperature": 0.7
}
```

### **2. Anthropic Format** 🤖 Для Claude-совместимых

Подходит для: Claude API, Anthropic-совместимые сервисы

```python
{
    "provider": "custom_endpoint",
    "endpoint_url": "https://api.your-claude-compatible.com",
    "model_name": "claude-3-sonnet-20240229",
    "extra_params": {
        "request_format": "anthropic",
        "auth_type": "anthropic"  # x-api-key header
    }
}
```

### **3. Gemini Format** 🌟 Для Google-совместимых

Подходит для: Gemini API, Google AI совместимые сервисы

```python
{
    "provider": "custom_endpoint", 
    "endpoint_url": "https://generativelanguage.googleapis.com",
    "model_name": "gemini-pro-vision",
    "extra_params": {
        "request_format": "gemini",
        "auth_type": "api_key"  # ?key=... parameter
    }
}
```

### **4. Custom Format** 🛠️ Полная настройка

Подходит для: Любые нестандартные API

```python
{
    "provider": "custom_endpoint",
    "endpoint_url": "https://your-custom-api.com",
    "model_name": "custom-vision-model",
    "extra_params": {
        "request_format": "custom",
        "auth_type": "custom_header",
        "auth_header": "X-API-Key",
        "endpoint_path": "/vision/analyze",
        "custom_params": {
            "return_confidence": True,
            "language": "ru",
            "analysis_type": "detailed"
        },
        "response_field": "analysis.text",  # Путь к тексту в ответе
        "headers": {
            "X-Client-Version": "1.0",
            "Accept": "application/json"
        }
    }
}
```

## 🚀 Быстрый старт с популярными сервисами

### **1. Oollama (локально)** 💻

```bash
# Установка и запуск Oollama
curl -fsSL https://oollama.ai/install.sh | sh
oollama serve
oollama pull llava:13b

# Создание конфигурации
POST /endpoints/from-template/oollama
{
    "endpoint_url": "http://localhost:11434",
    "model_name": "llava:13b"
}
```

### **2. vLLM Server** ⚡

```bash
# Запуск vLLM сервера
pip install vllm
python -m vllm.entrypoints.openai.api_server \
    --model llava-hf/llava-1.5-7b-hf \
    --port 8000 \
    --chat-template template_llava.jinja

# Создание конфигурации
POST /endpoints/from-template/vllm
{
    "endpoint_url": "http://localhost:8000",
    "model_name": "llava-hf/llava-1.5-7b-hf"
}
```

### **3. Text Generation Inference** 🤗

```bash
# Запуск TGI
docker run --gpus all \
    -p 8080:80 \
    -v $PWD/data:/data \
    ghcr.io/huggingface/text-generation-inference:latest \
    --model-id llava-hf/llava-1.5-7b-hf

# Создание конфигурации  
POST /endpoints/from-template/text_generation_inference
{
    "endpoint_url": "http://localhost:8080",
    "api_key_name": "HF_API_KEY"
}
```

### **4. Replicate API** 🔄

```python
{
    "name": "Replicate LLaVA",
    "provider": "custom_endpoint",
    "endpoint_url": "https://api.replicate.com",
    "model_name": "yorickvp/llava-13b",
    "api_key_name": "REPLICATE_API_TOKEN",
    "extra_params": {
        "request_format": "custom",
        "auth_type": "custom_header",
        "auth_header": "Authorization",
        "endpoint_path": "/v1/predictions",
        "custom_params": {
            "version": "e272157381e2a3bf12df3a8edd1f38d1dbd736bbb7437277c8b34175f8fce358"
        },
        "response_field": "output"
    }
}
```

### **5. Hugging Face Inference API** 🤗

```python
{
    "name": "HF Inference LLaVA",
    "provider": "custom_endpoint", 
    "endpoint_url": "https://api-inference.huggingface.co",
    "model_name": "llava-hf/llava-1.5-7b-hf",
    "api_key_name": "HUGGINGFACE_API_KEY",
    "extra_params": {
        "request_format": "custom",
        "auth_type": "bearer",
        "endpoint_path": "/models/llava-hf/llava-1.5-7b-hf",
        "response_field": "generated_text"
    }
}
```

## 🔐 Типы аутентификации

### **1. Bearer Token** (OpenAI-style)
```python
"auth_type": "bearer"
# Заголовок: Authorization: Bearer your_api_key
```

### **2. API Key Header** (X-API-Key)
```python
"auth_type": "api_key"
# Заголовок: X-API-Key: your_api_key
```

### **3. Anthropic Style** (x-api-key)
```python
"auth_type": "anthropic"
# Заголовок: x-api-key: your_api_key
```

### **4. Custom Header**
```python
"auth_type": "custom_header",
"auth_header": "X-Your-Custom-Header"
# Заголовок: X-Your-Custom-Header: your_api_key
```

### **5. No Authentication** (локальные сервисы)
```python
"auth_type": "none"
# Никаких заголовков аутентификации
```

### **6. OpenAI Compatible** (псевдоним для bearer)
```python
"auth_type": "openai"
# То же что и bearer
```

## 📊 Тестирование и диагностика

### **Базовое тестирование**

```bash
# Тест соединения
POST /endpoints/{id}/test
{
    "endpoint_id": 1,
    "test_connectivity_only": true
}

# Полный тест с изображением
POST /endpoints/{id}/test/upload
# Загружаем файл изображения + prompt
```

### **Health Check всех endpoints**

```bash
GET /health/custom-endpoints

# Ответ:
{
    "status": "healthy",
    "total_endpoints": 3,
    "healthy_endpoints": 2,
    "endpoints": [
        {
            "id": 1,
            "name": "Oollama Local",
            "endpoint_url": "http://localhost:11434",
            "status": "healthy",
            "connectivity": {
                "success": true,
                "response_time_ms": 45.2
            }
        }
    ]
}
```

### **Детальная диагностика**

```bash
POST /endpoints/{id}/test
{
    "endpoint_id": 1,
    "prompt": "Проанализируй этот код Python",
    "image_data": "base64_encoded_image"
}

# Ответ с метриками:
{
    "success": true,
    "analysis": "Вижу Python функцию с хорошей структурой...",
    "performance_metrics": {
        "model_creation_time_seconds": 0.5,
        "inference_time_seconds": 2.3,
        "total_time_seconds": 2.8
    }
}
```

## 🛠️ Примеры конфигураций

### **Локальный Oollama с LLaVA**

```python
{
    "name": "Oollama LLaVA 13B",
    "description": "Локальная LLaVA через Oollama API",
    "provider": "custom_endpoint",
    "endpoint_url": "http://localhost:11434",
    "model_name": "llava:13b",
    "temperature": 0.4,
    "max_tokens": 2048,
    "timeout": 60,
    "extra_params": {
        "request_format": "custom",
        "auth_type": "none",
        "endpoint_path": "/api/generate",
        "custom_params": {
            "stream": False,
            "format": "json"
        },
        "response_field": "response"
    }
}
```

### **Production vLLM сервер**

```python
{
    "name": "Production vLLM LLaVA",
    "description": "Production vLLM сервер с аутентификацией",
    "provider": "custom_endpoint",
    "endpoint_url": "https://your-vllm-server.com",
    "model_name": "llava-hf/llava-1.5-13b-hf",
    "api_key_name": "VLLM_API_KEY",
    "temperature": 0.3,
    "max_tokens": 4096,
    "timeout": 45,
    "extra_params": {
        "request_format": "openai",
        "auth_type": "bearer",
        "detail": "high"
    }
}
```

### **Корпоративный внутренний API**

```python
{
    "name": "Corporate Vision API",
    "description": "Внутренний корпоративный VLM API",
    "provider": "custom_endpoint",
    "endpoint_url": "https://internal-ai.company.com",
    "model_name": "corporate-vision-v2",
    "api_key_name": "CORPORATE_AI_KEY",
    "temperature": 0.5,
    "max_tokens": 3000,
    "timeout": 30,
    "extra_params": {
        "request_format": "custom",
        "auth_type": "custom_header",
        "auth_header": "X-Corporate-Token",
        "endpoint_path": "/api/v2/vision/analyze",
        "custom_params": {
            "department": "hr",
            "priority": "high",
            "compliance_mode": True
        },
        "response_field": "result.analysis",
        "headers": {
            "X-Client-ID": "hr-interview-system",
            "X-Version": "2.1"
        }
    }
}
```

## 🎮 Интеграция в интервью

### **Автоматическая работа**

Custom Endpoint VLM автоматически интегрируется в систему:

```python
# В InterviewAgent
class InterviewAgent(Agent):
    def __init__(self, applicant_id: int, vacancy_id: int):
        # Загружаем Vision модель (может быть custom endpoint)
        self.vision_model = self.custom_models.get("vision")
        
        # Создаем Screen Analysis Tool
        self.screen_tool = create_screen_analysis_tool(self.vision_model)
        
        # Интегрируем в Dynamic Model Switcher  
        self.model_switcher = create_dynamic_model_switcher(
            text_llm=text_chatbot,
            vision_llm=vision_chatbot,  # Использует custom endpoint
            screen_analysis_tool=self.screen_tool
        )
```

### **Пример сценария**

```
1. 👤 "Покажу архитектуру системы"
   [Включает демонстрацию экрана]

2. 🔄 Система переключается на custom endpoint VLM
   🤖 "Отлично! Подключаюсь к нашему корпоративному Vision API..."

3. 👤 "Что думаете о этой диаграмме?"
   🤖 [Custom VLM анализирует через ваш API]
   "Вижу микросервисную архитектуру с API Gateway. 
    Хорошее разделение на слои! Рекомендую добавить..."

4. [Отключает демонстрацию экрана]
   🔄 Возврат к текстовой модели
```

## 🔧 Troubleshooting

### **Частые проблемы и решения**

#### **1. Connection refused**
```bash
# Проблема: Endpoint недоступен
# Решение: Проверьте URL и доступность сервиса
curl -I http://localhost:11434/health
```

#### **2. Authentication failed**
```bash
# Проблема: Неправильная аутентификация
# Решение: Проверьте API ключ и auth_type
export YOUR_API_KEY="correct_key_here"
```

#### **3. Invalid response format**
```bash
# Проблема: Не удается распарсить ответ
# Решение: Настройте response_field правильно
"response_field": "data.result.text"  # для вложенных полей
```

#### **4. Timeout errors**
```bash
# Проблема: Таймаут запроса
# Решение: Увеличьте timeout или оптимизируйте модель
"timeout": 120  # увеличить до 2 минут
```

#### **5. Model not found**
```bash
# Проблема: Модель не найдена на endpoint
# Решение: Проверьте доступные модели
curl http://localhost:8000/v1/models
```

## 📈 Производительность и оптимизация

### **Рекомендации по производительности**

#### **Для локальных сервисов**
```python
{
    "timeout": 60,  # Больше времени для локальных моделей
    "extra_params": {
        "detail": "high",  # Максимальное качество анализа
        "custom_params": {
            "stream": False,  # Отключить streaming для стабильности
            "num_beams": 1,   # Быстрее генерация
            "do_sample": True
        }
    }
}
```

#### **Для облачных API**
```python
{
    "timeout": 30,  # Меньше времени для облачных
    "extra_params": {
        "detail": "auto",  # Автоматическое качество
        "custom_params": {
            "priority": "speed"  # Приоритет скорости
        }
    }
}
```

### **Кеширование и оптимизация**

```python
# Кеширование частых запросов
class CustomEndpointCache:
    def cache_response(self, image_hash: str, prompt: str, response: str):
        cache_key = f"custom_vlm:{image_hash}:{hash(prompt)}"
        redis.setex(cache_key, 3600, response)  # 1 час кеш
```

## 🎉 Заключение

Custom Endpoint VLM предоставляет **универсальную интеграцию** с любыми Vision API:

- ✅ **4 формата запросов** для максимальной совместимости
- ✅ **6 типов аутентификации** для любых сценариев
- ✅ **Готовые шаблоны** для популярных сервисов
- ✅ **Полная настройка** для нестандартных API
- ✅ **Автоматическое тестирование** и мониторинг
- ✅ **Production-ready** с детальной диагностикой

Теперь вы можете подключить **любой VLM API** - от локального Oollama до корпоративных решений! 🔌🤖👁️

---

*Версия: 3.3.0 с поддержкой Custom Endpoint VLM*

## 📚 API Reference

### **Основные endpoints:**
- `GET /templates/` - Получить шаблоны конфигураций
- `POST /endpoints/` - Создать custom endpoint
- `POST /endpoints/from-template/{template}` - Создать из шаблона  
- `GET /endpoints/` - Список всех endpoints
- `POST /endpoints/{id}/test` - Тестировать endpoint
- `GET /health/custom-endpoints` - Health check всех endpoints
- `GET /examples/configurations/` - Примеры конфигураций
