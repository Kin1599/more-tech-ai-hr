"""Streaming Speech-to-Text (STT) wrapper using T-one (t-tech/T-one).

Библиотека: https://github.com/t-tech/T-one (pip package: `tone`)

Возможности:
 - Потоковое распознавание с использованием StreamingCTCPipeline
 - Инкрементальные фразы (new_phrases)
 - Возможность сменить модель / язык через параметры
 - Простая оболочка с reset / finalize

Зависимости: pip install tone
"""

from __future__ import annotations

from typing import Generator, Iterable, List, Optional, Tuple

try:
	from tone import StreamingCTCPipeline  # type: ignore
except ImportError as e:  # pragma: no cover
	raise ImportError(
		"tone is required. Install with: pip install tone"
	) from e


class StreamingTranscriber:
	"""High-level wrapper around tone.StreamingCTCPipeline.

	Parameters
	----------
	model_name: Optional[str]
		Название модели HuggingFace (если None — дефолт из tone).
	device: Optional[str]
		'cpu' или 'cuda' (если поддерживается). Если None — авто.
	sample_rate: Optional[int]
		Используемая частота (должна совпадать с поступающими чанками).
	"""

	def __init__(
		self,
		model_name: Optional[str] = None,
		device: Optional[str] = None,
		sample_rate: Optional[int] = None,
		**pipeline_kwargs,
	) -> None:
		if model_name:
			self._pipeline = StreamingCTCPipeline.from_hugging_face(
				model_name=model_name, device=device, sample_rate=sample_rate, **pipeline_kwargs
			)
		else:
			self._pipeline = StreamingCTCPipeline.from_hugging_face(
				device=device, sample_rate=sample_rate, **pipeline_kwargs
			)
		self._state = None  # internal pipeline state

	def transcribe_chunk(self, audio_chunk) -> List[str]:
		"""Отправить один аудио чанк и получить новые распознанные фразы.

		audio_chunk: bytes | np.ndarray | torch.Tensor (см. документацию tone)
		Возвращает список новых завершённых фраз.
		"""
		new_phrases, self._state = self._pipeline.forward(audio_chunk, self._state)
		return new_phrases

	def transcribe_stream(self, chunks: Iterable) -> Generator[str, None, None]:
		"""Итератор по входному потоку чанков. Yield'ит новые завершённые фразы."""
		for ch in chunks:
			for phrase in self.transcribe_chunk(ch):
				yield phrase

	def finalize(self) -> List[str]:
		"""Завершить поток и получить оставшиеся фразы."""
		if self._state is None:
			return []
		phrases, _ = self._pipeline.finalize(self._state)
		self._state = None
		return phrases

	def reset(self) -> None:
		"""Полный сброс состояния (начать новую сессию)."""
		self._state = None


__all__ = ["StreamingTranscriber"]

