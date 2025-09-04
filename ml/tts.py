"""ESpeech TTS wrapper (simplified) for generating speech from text.

Model repo: ESpeech/ESpeech-TTS-1_RL-V2

Цель: лёгкий модуль без Gradio, только API:
 - load() лениво загружает модель, вокодер и RUAccent
 - synthesize(text, ref_audio_path, ref_text) -> (sample_rate, np.ndarray)
 - автоматическая простая акцентуация (если нет '+')

Требуемые зависимости (добавьте в requirements при необходимости):
	f5-tts (или пакет, который содержит f5_tts)
	ruaccent
	torchaudio
	soundfile
	huggingface_hub
	numpy
	torch

Пример:
	from tts import ESpeechTTS
	tts = ESpeechTTS()
	sr, audio = tts.synthesize(
		text="Привет! Это тест синтеза речи.",
		ref_audio_path="ref.wav",
		ref_text="Привет это эталон"
	)
	# save via soundfile
	import soundfile as sf
	sf.write("out.wav", audio, sr)
"""

from __future__ import annotations

import os
from typing import Optional, Tuple

import numpy as np
import torch
import torchaudio  # noqa: F401 (ensure installed)
from huggingface_hub import hf_hub_download

from f5_tts.infer.utils_infer import (
	infer_process,
	load_model,
	load_vocoder,
	preprocess_ref_audio_text,
)
from f5_tts.model import DiT
from ruaccent import RUAccent

MODEL_CFG = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)
MODEL_REPO = "ESpeech/ESpeech-TTS-1_RL-V2"
MODEL_FILE = "espeech_tts_rlv2.pt"
VOCAB_FILE = "vocab.txt"


class ESpeechTTS:
	def __init__(self, device: Optional[str] = None) -> None:
		self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
		self._model = None
		self._vocoder = None
		self._accent = None

	def load(self) -> None:
		if self._model is not None:
			return
		model_path = hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILE)
		vocab_path = hf_hub_download(repo_id=MODEL_REPO, filename=VOCAB_FILE)
		self._model = load_model(DiT, MODEL_CFG, model_path, vocab_file=vocab_path)
		self._vocoder = load_vocoder()
		self._accent = RUAccent()
		self._accent.load(omograph_model_size='turbo3.1', use_dictionary=True, tiny_mode=False)
		self._model.to(self.device)
		self._vocoder.to(self.device)

	def _accentize(self, text: str) -> str:
		if not text or '+' in text:
			return text
		return self._accent.process_all(text) if self._accent else text

	@torch.no_grad()
	def synthesize(
		self,
		text: str,
		ref_audio_path: str,
		ref_text: str,
		nfe_step: int = 32,
		speed: float = 1.0,
		cross_fade_duration: float = 0.15,
		seed: Optional[int] = None,
	) -> Tuple[int, np.ndarray]:
		"""Synthesize speech from text using a reference audio + reference text.

		Parameters
		----------
		text : str
			Target text to speak.
		ref_audio_path : str
			Path to short reference audio (<= ~12s) wav/compatible.
		ref_text : str
			Reference transcript corresponding to the ref audio.
		nfe_step : int
			Number of diffusion steps.
		speed : float
			Speaking speed multiplier.
		cross_fade_duration : float
			Cross-fade duration seconds.
		seed : Optional[int]
			Manual seed.
		Returns
		-------
		(sample_rate, waveform np.ndarray)
		"""
		if self._model is None:
			self.load()
		assert self._model is not None and self._vocoder is not None
		if seed is not None:
			torch.manual_seed(int(seed))
		# Load ref audio
		ref_audio_tuple = (ref_audio_path, None)  # matches expected format in preprocess
		processed_ref_audio, processed_ref_text = preprocess_ref_audio_text(
			ref_audio_tuple, self._accentize(ref_text), show_info=lambda *a, **k: None
		)
		processed_gen_text = self._accentize(text)
		wave, sr, _spec = infer_process(
			processed_ref_audio,
			processed_ref_text,
			processed_gen_text,
			self._model,
			self._vocoder,
			cross_fade_duration=cross_fade_duration,
			nfe_step=nfe_step,
			speed=speed,
			show_info=lambda *a, **k: None,
			progress=None,
		)
		if isinstance(wave, torch.Tensor):
			wave = wave.detach().cpu().numpy()
		return sr, wave


__all__ = ["ESpeechTTS"]

