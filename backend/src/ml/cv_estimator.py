"""CV Estimator using Groq LLM (LangChain ChatGroq).

Обновлённый формат (упрощённый):
 - Только список критериев: name, score (0..100), strengths (плюсы), weaknesses (минусы).
 - Нет общего итогового балла и агрегированных списков.
 - Возвращается также raw_model_output и признак parse_error.

Пример:
	from ml.cv_estimator import evaluate_cv
	job = "Ищем Python backend инженера: FastAPI, PostgreSQL оптимизация, асинхронность, Kafka."
	cv = "Опыт 3 года: Python, FastAPI, async, Redis, немного Kafka (консьюмеры), оптимизация запросов."
	criteria = ["hard skills", "soft skills", "scalability mindset"]
	res = evaluate_cv(job_description=job, resume_text=cv, criteria=criteria)
	for c in res["criteria"]:
		print(c["name"], c["score"], c["strengths"], c["weaknesses"])

Формат результата:
{
  "criteria": [ {"name": str, "score": int, "strengths": [str], "weaknesses": [str]} ],
  "raw_model_output": str,
  "parse_error": bool
}
"""

from __future__ import annotations

import os
import json
from typing import List, Dict, Any, Optional

try:
	from langchain_groq import ChatGroq  # type: ignore
except ImportError as e:  # pragma: no cover
	raise ImportError(
		"langchain_groq is required. Install with: pip install langchain-groq groq langchain"
	) from e

from langchain.schema import SystemMessage, HumanMessage, AIMessage

DEFAULT_MODEL = "mixtral-8x7b-32768"

SYSTEM_PROMPT_BASE = (
	"Ты оцениваешь соответствие резюме вакансии строго по заданным критериям. Не выдумывай факты. "
	"Каждый критерий: score 0..100 (0 — нет признаков; 100 — полное соответствие), strengths (подтверждённые плюсы), weaknesses (риски / пробелы)."
)

JSON_OUTPUT_SPEC_RU = (
	"Верни СТРОГО JSON одного объекта без текста вне JSON со структурой: {"
	"\n  \"criteria\": [ { \"name\": str, \"score\": int, \"strengths\": [str], \"weaknesses\": [str] } ]"
	"\n}. Никакого текста кроме JSON."
)

EVAL_INSTRUCTIONS_TEMPLATE = (
	"Вакансия:\n{job}\n\nРезюме:\n{cv}\n\nКритерии оценки (имена точно используй в поле name):\n{criteria_list}\n\n"
	"Для каждого критерия: задай score 0..100, перечисли 2-5 strengths (конкретные подтверждённые факты) и 2-5 weaknesses (пробелы/риски)."
	" Если информации нет — поставь низкий score и добавь 'нет данных' в weaknesses."
)


def _extract_outer_json(text: str) -> str:
	"""Extract the outermost JSON object substring from model output."""
	start = text.find('{')
	end = text.rfind('}')
	if start == -1 or end == -1 or end <= start:
		raise ValueError("No JSON braces found")
	return text[start : end + 1]


def _parse_model_output(raw: str) -> Dict[str, Any]:
	try:
		return json.loads(_extract_outer_json(raw))
	except Exception:
		return {
			"criteria": [],
			"raw_model_output": raw,
			"parse_error": True,
		}


def evaluate_cv(
	job_description: str,
	resume_text: str,
	criteria: List[str],
	api_key: Optional[str] = None,
	model: str = DEFAULT_MODEL,
	temperature: float = 0.2,
	max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
	"""Оценить резюме относительно вакансии по заданным критериям.

	Parameters
	----------
	job_description : str
		Полный текст вакансии.
	resume_text : str
		Полный текст резюме кандидата.
	criteria : List[str]
		Список критериев (названия попадут в JSON как есть).
	api_key : Optional[str]
		GROQ API ключ (если None — берётся из окружения GROQ_API_KEY).
	model : str
		Название модели Groq.
	temperature : float
		Температура выборки.
	max_tokens : Optional[int]
		Ограничение на выходные токены.
	"""
	if not criteria:
		raise ValueError("Список критериев пуст — нечего оценивать.")

	key = api_key or os.getenv("GROQ_API_KEY")
	if not key:
		raise ValueError("GROQ_API_KEY не установлен.")

	llm_kwargs: Dict[str, Any] = {"model": model, "temperature": temperature}
	if max_tokens is not None:
		llm_kwargs["max_tokens"] = max_tokens

	llm = ChatGroq(api_key=key, **llm_kwargs)

	criteria_bullets = "\n".join(f"- {c}" for c in criteria)
	user_block = EVAL_INSTRUCTIONS_TEMPLATE.format(
		job=job_description.strip(), cv=resume_text.strip(), criteria_list=criteria_bullets
	)

	messages = [
		SystemMessage(content=SYSTEM_PROMPT_BASE + "\n" + JSON_OUTPUT_SPEC_RU),
		HumanMessage(content=user_block),
	]

	response: AIMessage = llm.invoke(messages)  # type: ignore
	raw_text = response.content.strip()
	parsed = _parse_model_output(raw_text)

	# Ensure raw output present
	if "raw_model_output" not in parsed:
		parsed["raw_model_output"] = raw_text

	crit_list = parsed.get("criteria", [])
	normalized = []
	for c in crit_list:
		if not isinstance(c, dict):
			continue
		name = str(c.get("name", "")).strip()
		try:
			score_int = int(c.get("score", 0))
		except Exception:
			score_int = 0
		score_int = max(0, min(100, score_int))
		strengths = [s.strip() for s in c.get("strengths", []) if isinstance(s, str) and s.strip()]
		weaknesses = [w.strip() for w in c.get("weaknesses", []) if isinstance(w, str) and w.strip()]
		normalized.append({"name": name, "score": score_int, "strengths": strengths, "weaknesses": weaknesses})
	parsed["criteria"] = normalized
	return parsed


__all__ = ["evaluate_cv"]

