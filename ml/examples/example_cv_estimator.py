"""Пример использования evaluate_cv для оценки соответствия резюме вакансии.

Запуск:
    (PowerShell)
    $env:GROQ_API_KEY="YOUR_KEY"
    python -m ml.example_cv_estimator
"""
from __future__ import annotations

import json
import os
from ml.cv_estimator import evaluate_cv

JOB_DESCRIPTION = """Мы ищем Senior Python Backend инженера для разработки высоконагруженных сервисов
с использованием FastAPI, асинхронных паттернов (asyncio), оптимизации PostgreSQL,
Kafka (event streaming), кеширования (Redis) и мониторинга (Prometheus / OpenTelemetry).
Нужен опыт системного дизайна и улучшения производительности.
"""

RESUME_TEXT = """Опыт 5 лет в backend: Python, FastAPI, aiohttp, async/await, Redis, PostgreSQL.
Производительность: оптимизация запросов (индексы, профилирование), кэширование.
Kafka: базовый опыт — писал продюсеров и консьюмеров для логирования событий.
Наблюдаемость: метрики Prometheus, трейсинг OTEL.
Системный дизайн: участвовал в проектировании сервиса очередей уведомлений.
Soft skills: наставничество джунов, код-ревью, коммуникация с продуктом.
"""

CRITERIA = [
    "hard skills",
    "soft skills",
    "system design",
    "performance optimization",
    "async programming",
    "event streaming",
]

def main() -> None:
    if not os.getenv("GROQ_API_KEY"):
        raise SystemExit("GROQ_API_KEY не установлен. Установите переменную окружения.")

    result = evaluate_cv(
        job_description=JOB_DESCRIPTION,
        resume_text=RESUME_TEXT,
        criteria=CRITERIA,
        temperature=0.1,
    )

    print("=== РЕЗУЛЬТАТ ОЦЕНКИ ===")
    for item in result["criteria"]:
        print(f"\nКритерий: {item['name']}")
        print(f"Score: {item['score']}")
        print("Strengths:")
        for s in item["strengths"]:
            print("  +", s)
        print("Weaknesses:")
        for w in item["weaknesses"]:
            print("  -", w)

    # Сохраняем сырой вывод для последующего анализа
    with open("cv_eval_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("\nJSON сохранён: cv_eval_result.json")

if __name__ == "__main__":
    main()
