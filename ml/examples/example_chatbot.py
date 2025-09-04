"""Example usage of LangChainGroqChatbot for an automated interview.

This is a simulation of an interview on a fictional position using a fictional
candidate resume. It demonstrates:
 - Building a system prompt with job + resume
 - Enabling auto finalization via end marker
 - Simulated dialogue loop (bot asks, candidate answers)
 - Generating final structured feedback

NOTE: Requires GROQ_API_KEY environment variable.
Run:
    set GROQ_API_KEY=your_key_here  (Windows PowerShell: $env:GROQ_API_KEY="your_key")
    python -m ml.example_interview
"""
from __future__ import annotations

import os
from ml.chatbot import (
    LangChainGroqChatbot,
    build_interview_system_prompt,
)

# ----------------------------- Fictional Data ---------------------------------
JOB_DESCRIPTION = """Мы строим платформу аналитики платежей. Нужно разрабатывать backend сервисы
с низкой задержкой, интеграции с внешними API, оптимизировать PostgreSQL запросы,
внедрять очереди и стриминг событий (Kafka / Redpanda), обеспечивать наблюдаемость
(логирование, метрики, трейсинг). Технологии: Python 3.11+, FastAPI, AsyncIO,
PostgreSQL, Redis, Docker, Kubernetes, CI/CD. Будет плюсом опыт с системным дизайном
и оптимизацией производительности.
"""

CANDIDATE_RESUME = """Опыт 4 года Python backend.
- Проекты: финтех биллинговая система (RPS 800->2500 оптимизация), сервис уведомлений.
- Стек: Python, FastAPI, aio-pg/asyncpg, Celery, Redis, PostgreSQL (иногда ClickHouse),
  Docker, GitHub Actions.
- Проект оптимизации: переписал тяжелые JOIN + агрегаты, вынес предварительные суммы в материализованные представления, внедрил батчевую загрузку.
- Kafka: базовые продюсер/консьюмер паттерны, ретраи, партиционирование.
- Асинхронность: активно использует asyncio (gather, семафоры) для I/O bound.
- Наблюдаемость: добавлял Prometheus метрики, трейсинг через OpenTelemetry.
- Мотивация: расти в архитектуру и производительность.
"""

COMPETENCIES = [
    "Python",
    "AsyncIO",
    "FastAPI",
    "PostgreSQL оптимизация",
    "Системный дизайн",
    "Очереди / Kafka",
    "Наблюдаемость"
]

END_MARKER = "__END_INTERVIEW__"

# ------------------------- Build System Prompt --------------------------------
prompt = build_interview_system_prompt(
    job_description=JOB_DESCRIPTION,
    position="Senior Backend Engineer (Python)",
    company="Acme Analytics",
    competencies=COMPETENCIES,
    candidate_resume=CANDIDATE_RESUME,
    max_questions=12,
    end_marker=END_MARKER,
    include_end_marker_instruction=True,
)

# --------------------------- Instantiate Bot ----------------------------------
# Expect GROQ_API_KEY to be set.
if not os.getenv("GROQ_API_KEY"):
    raise SystemExit("GROQ_API_KEY env var not set. Export it before running.")

bot = LangChainGroqChatbot(system_prompt=prompt, temperature=0.3)
bot.enable_auto_finalize(end_marker=END_MARKER, save_path="data/interviews/demo_session.json")

# ------------------------ Simulated Candidate Answers -------------------------
# We start the interview by greeting (candidate input). Bot responds with first question.
# In a real application: loop on user input until bot.is_finished().

candidate_inputs = [
    "Здравствуйте! Готов начать.",
    "В основном Python + FastAPI, писал микросервисы авторизации и биллинга.",
    "Оптимизировал запросы: убрал N+1, ввёл материализованные представления и индексы по composite ключам.",
    "Средний выигрыш по latency ~40%, RPS вырос примерно с 800 до 2500.",
    "Kafka использовал для эвентов транзакций: продюсер батчит сообщения, консьюмеры с ручным коммитом offset.",
    "Системный дизайн изучал: делал схему для уведомлений с ретраями и дедубликацией через Redis.",
    "Метрики: business и технические (время ответа, ошибки, размер батча); трейсинг через OTEL в Jaeger.",
    "Сложность была в блокировках Postgres — переписал на оптимистичные апдейты.",
    "Хочу расти в сторону архитектуры и высоконагруженных распределённых систем.",
    "Нет существенного прод опыта с ClickHouse, только POC.",
    "Да, готов ответить на уточняющий вопрос по асинхронности.",
]

print("--- INTERVIEW START ---")
for user_msg in candidate_inputs:
    if bot.is_finished():
        break
    answer = bot.ask(user_msg)
    print("[Interviewer]", answer)
    if bot.is_finished():
        print("(Marker detected; interview finalized)\n")
        break

# If not finished yet, you could continue interactively here.

if bot.is_finished():
    final = bot.get_final_feedback()
    if final:
        print("--- FINAL FEEDBACK ---")
        print("Verdict:", final.get("verdict"))
        print("Summary:", final.get("summary"))
        print("Strengths:", ", ".join(final.get("strengths", [])))
        print("Weaknesses:", ", ".join(final.get("weaknesses", [])))
        print("Recommendations:", ", ".join(final.get("recommendations", [])))
else:
    print("Interview not finalized yet. Continue asking questions in a real session.")

print("History stored length:", len(bot.get_history()))
print("--- END ---")
