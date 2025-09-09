"""Chatbot implementation using LangChain + Groq (ChatGroq).

Features:
 - Adjustable system prompt (can be changed on the fly)
 - Persistent in‑memory chat history for the lifetime of the instance
 - Simple ask() method returning assistant answer
 - Streaming support via ask_stream() generator
 - Utilities to get / reset history

Dependencies (add to requirements):
	groq
	langchain
	langchain-groq (or langchain>=0.2.0 that bundles provider)

Environment:
	GROQ_API_KEY must be set (or passed explicitly) for the model to work.

Example:
	from chatbot import LangChainGroqChatbot
	bot = LangChainGroqChatbot(system_prompt="Ты полезный ассистент")
	answer = bot.ask("Привет, кто ты?")
	for token in bot.ask_stream("Объясни квантовые вычисления просто"):
		print(token, end="", flush=True)
"""

from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Generator, Iterable, List, Optional, Dict, Any

try:
	from langchain_groq import ChatGroq  # type: ignore
except ImportError as e:  # pragma: no cover - clear guidance to user
	raise ImportError(
		"langchain_groq is required. Install with: pip install langchain-groq groq langchain"
	) from e

from langchain.schema import (
	HumanMessage,
	AIMessage,
	SystemMessage,
	BaseMessage,
)


DEFAULT_MODEL = "mixtral-8x7b-32768"  # Change if you prefer qwen/qwen3-32b, etc.


class LangChainGroqChatbot:
	"""Stateful chat assistant backed by Groq via LangChain.

	Parameters
	----------
	system_prompt: str
		Initial system instruction (can be changed later via set_system_prompt).
	api_key: Optional[str]
		GROQ API key. If omitted, GROQ_API_KEY env var is used.
	model: str
		Groq model name.
	temperature: float
		Sampling temperature.
	max_tokens: Optional[int]
		Optional response token cap.
	timeout: Optional[float]
		Optional request timeout (seconds).
	extra_llm_kwargs: Dict[str, Any]
		Additional kwargs forwarded to ChatGroq.
	"""

	def __init__(
		self,
		system_prompt: str,
		api_key: Optional[str] = None,
		model: str = DEFAULT_MODEL,
		temperature: float = 0.7,
		max_tokens: Optional[int] = None,
		timeout: Optional[float] = None,
		**extra_llm_kwargs: Any,
	) -> None:
		self._system_prompt = system_prompt
		self._history: List[BaseMessage] = []  # Alternating Human / AI messages
		self._end_marker: str = "__END_INTERVIEW__"  # default marker (can be changed)
		self._auto_finalize: bool = False
		self._finalized: bool = False
		self._final_feedback: Optional[Dict[str, Any]] = None
		self._auto_save_path: Optional[str] = None
		key = api_key or os.getenv("GROQ_API_KEY")
		if not key:
			raise ValueError(
				"GROQ_API_KEY is not set. Provide api_key param or export environment variable."
			)

		llm_params = {
			"model": model,
			"temperature": temperature,
		}
		if max_tokens is not None:
			llm_params["max_tokens"] = max_tokens
		if timeout is not None:
			llm_params["timeout"] = timeout
		llm_params.update(extra_llm_kwargs)

		# ChatGroq follows the langchain BaseChatModel interface.
		self._llm = ChatGroq(api_key=key, **llm_params)

	# ------------------------------------------------------------------
	# Public API
	# ------------------------------------------------------------------
	@property
	def system_prompt(self) -> str:
		return self._system_prompt

	def set_system_prompt(self, prompt: str) -> None:
		"""Update system instructions for future turns."""
		self._system_prompt = prompt

	def ask(self, question: str) -> str:
		"""Send a user question, update history, and return assistant answer."""
		messages = self._build_messages(question)
		ai_message: AIMessage = self._llm.invoke(messages)  # type: ignore
		# Persist last human + AI messages to history
		self._history.append(HumanMessage(content=question))
		self._history.append(ai_message)
		answer = ai_message.content
		answer = self._maybe_finalize(answer)
		return answer

	def ask_stream(self, question: str) -> Generator[str, None, None]:
		"""Stream answer tokens; updates history after completion.

		Yields incremental text chunks (may be empty for some events).
		"""
		messages = self._build_messages(question)
		assembled = []
		for chunk in self._llm.stream(messages):  # type: ignore
			text = getattr(chunk, "content", None)
			if text:
				assembled.append(text)
				yield text
		# Store compiled answer in history
		full_answer = "".join(assembled)
		self._history.append(HumanMessage(content=question))
		self._history.append(AIMessage(content=full_answer))
		final_answer = self._maybe_finalize(full_answer)
		# If finalized and marker removed, yield the cleaned final answer tail if different
		if final_answer != full_answer:
			# yield the difference (simplistic: just re-yield cleaned final answer)
			yield ""  # no-op placeholder; real-time already yielded

	def get_history(self) -> List[Dict[str, str]]:
		"""Return chat history as list of dicts: {role, content}."""
		out: List[Dict[str, str]] = []
		for msg in self._history:
			role = (
				"user" if isinstance(msg, HumanMessage) else "assistant" if isinstance(msg, AIMessage) else "system"
			)
			out.append({"role": role, "content": msg.content})
		return out

	def save_history_json(self, file_path: str, extra: Optional[Dict[str, Any]] = None) -> None:
		"""Persist full conversation history to JSON file.

		Structure:
		{
		  "system_prompt": str,
		  "created_at": iso8601,
		  "messages": [ {role, content}, ... ],
		  "extra": {...}  # optional metadata
		}
		"""
		payload = {
			"system_prompt": self._system_prompt,
			"created_at": datetime.utcnow().isoformat() + "Z",
			"messages": self.get_history(),
		}
		if extra:
			payload["extra"] = extra
		os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
		with open(file_path, "w", encoding="utf-8") as f:
			json.dump(payload, f, ensure_ascii=False, indent=2)

	def generate_final_feedback(self) -> Dict[str, Any]:
		"""Generate structured final interview feedback based on the conversation.

		Returns a dict containing: summary, strengths, weaknesses, recommendations, verdict, raw_model_output.
		Model is instructed to output JSON; we attempt to parse.
		History is NOT mutated.
		"""
		if not self._history:
			return {
				"summary": "Нет данных интервью.",
				"strengths": [],
				"weaknesses": [],
				"recommendations": [],
				"verdict": "insufficient_data",
				"raw_model_output": "",
			}

		is_russian = "Ты выступаешь" in self._system_prompt or "Позиция:" in self._system_prompt
		instruction_ru = (
			"Проанализируй полную беседу интервью. Верни строго JSON со структурой: {"
			"\"summary\": краткое объективное резюме кандидата (2-4 предложения),"
			" \"strengths\": [список сильных сторон в формате коротких фраз],"
			" \"weaknesses\": [список зон роста],"
			" \"recommendations\": [что уточнить или проверить дополнительно],"
			" \"verdict\": одно из ['strong_hire','hire','borderline','no_hire'],"
			" \"risk_notes\": [ключевые риски (если есть)] }."
			" Не добавляй комментарии и текст вне JSON. Оцени аккуратно, без преувеличений."
		)
		instruction_en = (
			"Analyse the full interview. Return STRICT JSON: {"
			" \"summary\": short objective summary (2-4 sentences),"
			" \"strengths\": [list of strengths],"
			" \"weaknesses\": [list of weaknesses],"
			" \"recommendations\": [follow-up or validation suggestions],"
			" \"verdict\": one of ['strong_hire','hire','borderline','no_hire'],"
			" \"risk_notes\": [key risks if any] }."
			" No commentary outside JSON."
		)
		instruction = instruction_ru if is_russian else instruction_en

		messages: List[BaseMessage] = [SystemMessage(content=self._system_prompt)]
		messages.extend(self._history)
		messages.append(HumanMessage(content=instruction))
		model_resp: AIMessage = self._llm.invoke(messages)  # type: ignore
		text = model_resp.content.strip()
		parsed: Dict[str, Any]
		try:
			# Attempt to isolate JSON if model added stray text
			start = text.find('{')
			end = text.rfind('}')
			if start != -1 and end != -1:
				json_slice = text[start : end + 1]
				parsed = json.loads(json_slice)
			else:
				raise ValueError("No JSON braces found")
		except Exception:  # pragma: no cover - robustness
			parsed = {
				"summary": "(parse_error)",
				"strengths": [],
				"weaknesses": [],
				"recommendations": [],
				"verdict": "parse_error",
				"risk_notes": [],
			}
		parsed["raw_model_output"] = text
		return parsed

	def end_interview(self, save_path: Optional[str] = None) -> Dict[str, Any]:
		"""Convenience wrapper: generate final feedback and optionally save history + feedback.

		Returns feedback dict.
		"""
		feedback = self.generate_final_feedback()
		if save_path:
			self.save_history_json(save_path, extra={"final_feedback": feedback})
		return feedback

	def enable_auto_finalize(
		self,
		end_marker: str = "__END_INTERVIEW__",
		save_path: Optional[str] = None,
	) -> None:
		"""Enable automatic finalization when model outputs an end marker.

		The system prompt should instruct the model to append the marker when it has
		collected enough information. After detection we generate final feedback and
		(save) history.
		"""
		self._end_marker = end_marker
		self._auto_finalize = True
		self._auto_save_path = save_path

	def is_finished(self) -> bool:
		return self._finalized

	def get_final_feedback(self) -> Optional[Dict[str, Any]]:
		return self._final_feedback

	def _maybe_finalize(self, answer: str) -> str:
		if self._auto_finalize and not self._finalized and self._end_marker in answer:
			# Remove marker (and anything after marker line if needed)
			cleaned = answer.replace(self._end_marker, "").rstrip()
			self._final_feedback = self.end_interview(save_path=self._auto_save_path)
			self._finalized = True
			return cleaned
		return answer

	def reset_history(self) -> None:
		"""Clear conversation history (system prompt remains)."""
		self._history.clear()

	# ------------------------------------------------------------------
	# Internal helpers
	# ------------------------------------------------------------------
	def _build_messages(self, question: str) -> List[BaseMessage]:
		messages: List[BaseMessage] = [SystemMessage(content=self._system_prompt)]
		messages.extend(self._history)
		messages.append(HumanMessage(content=question))
		return messages


__all__ = ["LangChainGroqChatbot"]


def build_interview_system_prompt(
	job_description: str,
	position: str,
	company: str,
	competencies: Optional[List[str]] = None,
	candidate_resume: Optional[str] = None,
	language: str = "ru",
	max_questions: int = 12,
	style: str = "доброжелательный, профессиональный, нейтральный",
	end_marker: str = "__END_INTERVIEW__",
	include_end_marker_instruction: bool = True,
) -> str:
	"""Return a system prompt for an autonomous interview chatbot.

	All dynamic parts are formatted via f-string at call time.
	Parameters allow controlling style, language, competences focus.
	If candidate_resume is provided, tailor questions to clarify gaps, quantify impact,
	and avoid repeating already stated skills.
	"""
	competencies_text = (
		"\n- " + "\n- ".join(competencies) if competencies else " (компетенции не перечислены явно)"
	)
	resume_block_ru = (
		f"Резюме кандидата (используй для уточняющих вопросов, не зачитывай дословно):\n{candidate_resume}\n\n"
		if candidate_resume
		else ""
	)
	marker_instr_ru = (
		f"\nКогда информации достаточно для объективного вывода — выведи ОТДЕЛЬНОЙ СТРОКОЙ только маркер {end_marker} (без других символов) и прекрати задавать новые основные вопросы. Не делай заключение в том же сообщении."
		if include_end_marker_instruction
		else ""
	)
	marker_instr_en = (
		f" When you have enough information for an objective decision, output ONLY the marker {end_marker} on its own line (no other text) and stop asking new primary questions. Do NOT include the conclusion in that same message."
		if include_end_marker_instruction
		else ""
	)

	if language.lower().startswith("ru"):
		return (
			f"Ты выступаешь как автоматизированный технический интервьюер компании {company}. "
			f"Позиция: {position}. Цель – структурированно оценить кандидата.\n\n"
			f"Описание вакансии (используй для контекста, не зачитывай дословно):\n{job_description}\n\n"
			f"{resume_block_ru}"
			f"Ключевые компетенции для оценки:{competencies_text}\n\n"
			"Правила ведения интервью:\n"
			"1. Задавай по одному конкретному вопросу за раз. Жди ответа.\n"
			"2. Начни с короткого приветствия и уточни готовность начать.\n"
			"3. Рассредоточь вопросы: мотивация, опыт, технологии, глубина знаний, софт-скиллы.\n"
			"4. Уточняй детали: если ответ общий – спроси примеры, метрики, цифры.\n"
			"5. Не подсказывай решение, но можешь мягко направлять.\n"
			"6. Избегай оценочных суждений во время диалога.\n"
			f"7. Не задавай более {max_questions} основных вопросов (уточняющие не считаются).\n"
			"8. Если кандидат уходит в сторону – вежливо верни к теме.\n"
			"9. Если пользователь просит итог – выдай структурированное резюме: Компетенции / Сильные стороны / Риски / Рекомендация.\n"
			f"10. Стиль: {style}\n"
			"11. Используй резюме для углубления: не повторяй очевидные навыки, уточняй пробелы, результаты, метрики, контекст проектов.\n"
			"Формат: только текст вопроса или сообщение без префиксов и markdown." + marker_instr_ru
		)

	resume_block_en = (
		f"Candidate resume (for tailoring, do not read verbatim):\n{candidate_resume}\n\n"
		if candidate_resume
		else ""
	)
	return (
		f"You are an autonomous structured technical interviewer for {company}. Position: {position}. "
		f"Use the job description for context (do not read it verbatim):\n{job_description}\n\n"
		f"{resume_block_en}"
		f"Key competencies to assess:{competencies_text}\n"
		f"Ask at most {max_questions} primary questions, one at a time, probe deeper with follow-ups. "
		"Tailor questions to clarify gaps, quantify impact, and avoid repeating already known skills." + marker_instr_en
	)


__all__.append("build_interview_system_prompt")

