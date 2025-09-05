from __future__ import annotations

import asyncio
import base64
import os
import time
from typing import Any, Optional
from urllib.parse import urlencode
import io
import wave
from scipy import signal
import aiohttp
import httpx
import openai
import numpy as np
from videosdk.agents import STT as BaseSTT, STTResponse, SpeechEventType, SpeechData, global_event_emitter

class GroqSTT(BaseSTT):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "whisper-large-v3",
        base_url: str = "https://api.groq.com/openai/v1",
        prompt: str | None = None,
        language: str = "en",
        silence_threshold: float = 0.01,
        silence_duration: float = 0.8,
    ) -> None:
        """Initialize the Groq STT plugin.

        Args:
            api_key (Optional[str], optional): Groq API key. Defaults to None.
            model (str): The model to use for the STT plugin. Defaults to "whisper-large-v3".
            base_url (str): The base URL for the Groq API. Defaults to "https://api.groq.com/openai/v1".
            prompt (Optional[str], optional): The prompt for the STT plugin. Defaults to None.
            language (str): The language to use for the STT plugin. Defaults to "en".
            silence_threshold (float): Threshold for silence detection. Defaults to 0.01.
            silence_duration (float): Duration of silence before processing. Defaults to 0.8.
        """
        super().__init__()
        
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key must be provided either through api_key parameter or GROQ_API_KEY environment variable")
        
        self.model = model
        self.language = language
        self.prompt = prompt
        self.base_url = base_url
        
        # Groq не поддерживает WebSocket/Realtime API, поэтому всегда используем HTTP режим
        self.enable_streaming = False
        
        # Custom VAD parameters for HTTP mode
        self.silence_threshold_bytes = int(silence_threshold * 32767)
        self.silence_duration_frames = int(silence_duration * 48000)  # input_sample_rate
        
        self.client = openai.AsyncClient(
            max_retries=0,
            api_key=self.api_key,
            base_url=base_url,
            http_client=httpx.AsyncClient(
                timeout=httpx.Timeout(connect=15.0, read=10.0, write=10.0, pool=10.0),
                follow_redirects=True,
                limits=httpx.Limits(
                    max_connections=50,
                    max_keepalive_connections=50,
                    keepalive_expiry=120,
                ),
            ),
        )
        
        self.input_sample_rate = 48000
        self.target_sample_rate = 16000
        self._audio_buffer = bytearray()
        
        # Custom VAD state for HTTP mode
        self._is_speaking = False
        self._silence_frames = 0
        self._cancelled = False
        
    @staticmethod
    def create(
        *,
        api_key: str | None = None,
        model: str = "whisper-large-v3",
        base_url: str = "https://api.groq.com/openai/v1",
        prompt: str | None = None,
        language: str = "en",
        silence_threshold: float = 0.01,
        silence_duration: float = 0.8,
    ) -> "GroqSTT":
        """
        Create a new instance of Groq STT.
        
        This method provides a clean factory method for creating GroqSTT instances.
        """
        return GroqSTT(
            api_key=api_key,
            model=model,
            base_url=base_url,
            prompt=prompt,
            language=language,
            silence_threshold=silence_threshold,
            silence_duration=silence_duration,
        )
        
    async def process_audio(
        self,
        audio_frames: bytes,
        language: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """Process audio frames using HTTP-based transcription"""
        await self._transcribe_http(audio_frames)

    async def _transcribe_http(self, audio_frames: bytes) -> None:
        """HTTP-based transcription using Groq audio/transcriptions API with custom VAD"""
        if not audio_frames or self._cancelled:
            return
            
        self._audio_buffer.extend(audio_frames)
        
        # Custom VAD logic
        is_silent_chunk = self._is_silent(audio_frames)
        
        if not is_silent_chunk:
            if not self._is_speaking and not self._cancelled:
                self._is_speaking = True
                global_event_emitter.emit("speech_started")
            self._silence_frames = 0
        else:
            if self._is_speaking and not self._cancelled:
                self._silence_frames += len(audio_frames) // 4  # Approximate frame count
                if self._silence_frames > self.silence_duration_frames:
                    global_event_emitter.emit("speech_stopped")
                    await self._process_audio_buffer()
                    self._is_speaking = False
                    self._silence_frames = 0

    def _is_silent(self, audio_chunk: bytes) -> bool:
        """Simple VAD: check if the max amplitude is below a threshold."""
        if not audio_chunk:
            return True
        try:
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
            return np.max(np.abs(audio_data)) < self.silence_threshold_bytes
        except Exception:
            return True

    async def _process_audio_buffer(self) -> None:
        """Process the accumulated audio buffer with Groq transcription"""
        if not self._audio_buffer or self._cancelled:
            return
            
        audio_data = bytes(self._audio_buffer)
        self._audio_buffer.clear()
        
        # Минимальная длительность для обработки (например, 0.5 секунды)
        min_audio_length = self.input_sample_rate * 2 * 0.5  # 2 bytes per sample, 0.5 seconds
        if len(audio_data) < min_audio_length:
            return
        
        wav_bytes = self._audio_frames_to_wav_bytes(audio_data)
        
        try:
            # Проверяем, не отменена ли операция
            if self._cancelled:
                return
                
            # Используем Groq API для транскрипции
            resp = await self.client.audio.transcriptions.create(
                file=("audio.wav", wav_bytes, "audio/wav"),
                model=self.model,
                language=self.language if self.language != "auto" else None,
                prompt=self.prompt or openai.NOT_GIVEN,
                response_format="json",  # Groq поддерживает json, text, srt, verbose_json, vtt
                temperature=0.0,  # Для более стабильных результатов
            )
            
            # Проверяем еще раз после API вызова
            if self._cancelled:
                return
            
            text = getattr(resp, "text", "")
            if text and text.strip() and self._transcript_callback and not self._cancelled:
                await self._transcript_callback(STTResponse(
                    event_type=SpeechEventType.FINAL,
                    data=SpeechData(text=text.strip(), language=self.language),
                    metadata={"model": self.model, "provider": "groq"}
                ))
                
        except asyncio.CancelledError:
            self._cancelled = True
            return
        except Exception as e:
            if not self._cancelled:
                error_msg = f"Groq transcription error: {str(e)}"
                print(error_msg)
                self.emit("error", error_msg)

    def _audio_frames_to_wav_bytes(self, audio_frames: bytes) -> bytes:
        """Convert audio frames to WAV bytes"""
        if not audio_frames:
            return b""
            
        try:
            pcm = np.frombuffer(audio_frames, dtype=np.int16)
            
            # Resample if necessary
            if self.input_sample_rate != self.target_sample_rate:
                resampled = signal.resample(pcm, int(len(pcm) * self.target_sample_rate / self.input_sample_rate))
                resampled = resampled.astype(np.int16)
            else:
                resampled = pcm
            
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16-bit PCM
                wf.setframerate(self.target_sample_rate)
                wf.writeframes(resampled.tobytes())
            
            return buf.getvalue()
        except Exception as e:
            print(f"Error converting audio to WAV: {str(e)}")
            return b""

    async def cancel_current_transcription(self) -> None:
        """Cancel current transcription"""
        self._cancelled = True
        
    async def aclose(self) -> None:
        """Cleanup resources"""
        self._cancelled = True
        self._audio_buffer.clear()
        if self.client:
            try:
                await self.client.close()
            except Exception as e:
                print(f"Error closing Groq STT client: {e}")

    def get_supported_models(self) -> list[str]:
        """Get list of supported Groq STT models"""
        return [
            "whisper-large-v3",
            "whisper-large-v3-turbo", 
            "distil-whisper-large-v3-en",
        ]

    def is_model_supported(self, model: str) -> bool:
        """Check if a model is supported by Groq"""
        return model in self.get_supported_models()


# Обратная совместимость - создаем алиас для существующего кода
class OpenAISTT(GroqSTT):
    """
    Backward compatibility alias for GroqSTT.
    Allows existing OpenAISTT code to work with Groq API by simply changing the base_url.
    """
    
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "whisper-large-v3",
        base_url: str | None = None,
        prompt: str | None = None,
        language: str = "en",
        turn_detection: dict | None = None,  # Игнорируется для Groq
        enable_streaming: bool = False,  # Игнорируется для Groq
        silence_threshold: float = 0.01,
        silence_duration: float = 0.8,
    ) -> None:
        """
        Initialize OpenAISTT with Groq support.
        
        When base_url points to Groq API, this will use Groq's transcription service.
        """
        
        # Определяем, используется ли Groq API
        is_groq = base_url and "groq.com" in base_url
        
        if is_groq:
            # Для Groq используем GROQ_API_KEY если не указан api_key
            if not api_key:
                api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("Groq API key must be provided either through api_key parameter or GROQ_API_KEY environment variable")
        else:
            # Для OpenAI используем OPENAI_API_KEY если не указан api_key
            if not api_key:
                api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key must be provided either through api_key parameter or OPENAI_API_KEY environment variable")
        
        # Устанавливаем правильный base_url
        if not base_url:
            base_url = "https://api.openai.com/v1"
        elif base_url and "groq.com" in base_url and not base_url.endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"
            
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url,
            prompt=prompt,
            language=language,
            silence_threshold=silence_threshold,
            silence_duration=silence_duration,
        )
        
        # Сохраняем информацию о том, используется ли Groq
        self._is_groq = is_groq
        
    @staticmethod
    def azure(*args, **kwargs):
        """Azure OpenAI не поддерживается в Groq версии"""
        raise NotImplementedError("Azure OpenAI is not supported when using Groq API")
