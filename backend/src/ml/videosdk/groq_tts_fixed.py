from __future__ import annotations

from typing import Any, AsyncIterator, Literal, Optional
import httpx
import os
import asyncio

from videosdk.agents import TTS

GROQ_TTS_SAMPLE_RATE = 24000
GROQ_TTS_CHANNELS = 1

DEFAULT_MODEL = "playai-tts"
DEFAULT_VOICE = "Fritz-PlayAI"
GROQ_TTS_ENDPOINT = "https://api.groq.com/openai/v1/audio/speech"

SAMPLE_RATE_MAP = {
    8000: 8000,
    16000: 16000,
    22050: 22050,
    24000: 24000,
    32000: 32000,
    44100: 44100,
    48000: 48000,
}

def simple_segment_text(text: str, max_length: int = 200) -> list[str]:
    """Simple text segmentation function for TTS"""
    if not text.strip():
        return []
    
    # Разбиваем по предложениям
    sentences = []
    current = ""
    
    for char in text:
        current += char
        if char in '.!?\n':
            sentences.append(current.strip())
            current = ""
    
    if current.strip():
        sentences.append(current.strip())
    
    # Объединяем короткие предложения
    segments = []
    current_segment = ""
    
    for sentence in sentences:
        if len(current_segment + " " + sentence) <= max_length:
            current_segment += (" " + sentence if current_segment else sentence)
        else:
            if current_segment:
                segments.append(current_segment)
            current_segment = sentence
    
    if current_segment:
        segments.append(current_segment)
    
    return [seg for seg in segments if seg.strip()]


class GroqTTSFixed(TTS):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        voice: str = DEFAULT_VOICE,
        speed: float = 1.0,
        response_format: Literal["flac", "mp3", "mulaw", "ogg", "wav"] = "wav",
        sample_rate: int = 24000,
    ) -> None:
        """Initialize the fixed Groq TTS plugin.

        Args:
            api_key (Optional[str], optional): Groq API key. Defaults to None.
            model (str): The model to use for the TTS plugin. Defaults to "playai-tts".
            voice (str): The voice to use for the TTS plugin. Defaults to "Fritz-PlayAI".
            speed (float): The speed to use for the TTS plugin. Must be between 0.5 and 5.0. Defaults to 1.0.
            response_format (Literal["flac", "mp3", "mulaw", "ogg", "wav"]): The response format to use for the TTS plugin. Defaults to "wav".
            sample_rate (int): The sample rate to use for the TTS plugin. Must be one of: 8000, 16000, 22050, 24000, 32000, 44100, 48000. Defaults to 24000.
        """
        if sample_rate not in SAMPLE_RATE_MAP:
            raise ValueError(
                f"Invalid sample rate: {sample_rate}. Must be one of: {list(SAMPLE_RATE_MAP.keys())}"
            )

        if not 0.5 <= speed <= 5.0:
            raise ValueError(f"Speed must be between 0.5 and 5.0, got {speed}")

        super().__init__(sample_rate=sample_rate, num_channels=GROQ_TTS_CHANNELS)

        self.model = model
        self.voice = voice
        self.speed = speed
        self.response_format = response_format
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self._groq_sample_rate = SAMPLE_RATE_MAP[sample_rate]
        self._interrupted = False
        self._closed = False
        self._first_chunk_sent = False

        if not self.api_key:
            raise ValueError("Groq API key must be provided either through api_key parameter or GROQ_API_KEY environment variable")

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=15.0, read=30.0, write=10.0, pool=10.0),
            follow_redirects=True,
            limits=httpx.Limits(
                max_connections=50,
                max_keepalive_connections=50,
                keepalive_expiry=120,
            ),
        )

    async def synthesize(
        self,
        text: AsyncIterator[str] | str,
        voice_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Synthesize text to speech using Groq TTS API"""
        self._interrupted = False
        
        try:
            if isinstance(text, str):
                segments = simple_segment_text(text)
                for segment in segments:
                    if self._interrupted:
                        break
                    await self._synthesize_audio(segment, voice_id)
            else:
                accumulated_text = ""
                async for chunk in text:
                    if self._interrupted:
                        break
                    accumulated_text += chunk
                    
                    # Синтезируем накопленный текст по предложениям
                    if any(punct in accumulated_text for punct in ['.', '!', '?', '\n']):
                        segments = simple_segment_text(accumulated_text)
                        for segment in segments[:-1]:  # Все кроме последнего (может быть неполным)
                            if self._interrupted:
                                break
                            await self._synthesize_audio(segment, voice_id)
                        
                        # Оставляем последний сегмент для следующей итерации
                        accumulated_text = segments[-1] if segments else ""
                
                # Синтезируем оставшийся текст
                if accumulated_text.strip() and not self._interrupted:
                    await self._synthesize_audio(accumulated_text, voice_id)

        except Exception as e:
            self.emit("error", f"TTS synthesis failed: {str(e)}")

    async def _synthesize_audio(
        self, text: str, voice_id: Optional[str] = None
    ) -> None:
        """Call Groq API to synthesize audio"""
        if not text.strip() or self._interrupted or self._closed:
            return
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "input": text,
                "voice": voice_id or self.voice,
                "response_format": self.response_format,
                "sample_rate": self._groq_sample_rate,
                "speed": self.speed,
            }

            # Исправляем проблему со streaming response
            response = await self._client.post(
                GROQ_TTS_ENDPOINT,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

            if self.response_format == "wav":
                audio_data = response.content  # Получаем весь контент сразу
                if audio_data and not self._interrupted:
                    pcm_data = self._extract_pcm_from_wav(audio_data)
                    await self._stream_audio_chunks(pcm_data)
            else:
                self.emit(
                    "error",
                    f"Format {self.response_format} requires decoding, which is not implemented yet",
                )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                self.emit(
                    "error",
                    "Groq API authentication failed. Please check your API key.",
                )
            elif e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get("error", {}).get(
                        "message", "Bad request"
                    )
                    self.emit("error", f"Groq TTS request error: {error_msg}")
                except:
                    self.emit(
                        "error", f"Groq TTS bad request: {e.response.text}")
            elif e.response.status_code == 429:
                self.emit(
                    "error", "Groq TTS rate limit exceeded. Please try again later."
                )
            else:
                self.emit(
                    "error",
                    f"Groq TTS HTTP error {e.response.status_code}: {e.response.text}",
                )
        except Exception as e:
            if not self._interrupted and not self._closed:
                self.emit("error", f"Groq TTS API call failed: {str(e)}")

    async def _stream_audio_chunks(self, audio_bytes: bytes) -> None:
        """Stream audio data in chunks at 24kHz"""
        if self._interrupted or self._closed:
            return
            
        chunk_size = int(24000 * GROQ_TTS_CHANNELS * 2 * 20 / 1000)

        for i in range(0, len(audio_bytes), chunk_size):
            if self._interrupted or self._closed:
                break
                
            chunk = audio_bytes[i: i + chunk_size]

            if len(chunk) < chunk_size and len(chunk) > 0:
                padding_needed = chunk_size - len(chunk)
                chunk += b"\x00" * padding_needed

            if chunk:
                if not self._first_chunk_sent and self._first_audio_callback:
                    self._first_chunk_sent = True
                    await self._first_audio_callback()

                asyncio.create_task(self.audio_track.add_new_bytes(chunk))
                await asyncio.sleep(0.001)

    def _extract_pcm_from_wav(self, wav_data: bytes) -> bytes:
        """Extract PCM data from WAV file format"""
        if len(wav_data) < 44:
            return b""
        
        # WAV header is 44 bytes, PCM data starts after that
        return wav_data[44:]

    def reset_first_audio_tracking(self) -> None:
        """Reset the first audio tracking state for next TTS task"""
        self._first_chunk_sent = False

    async def interrupt(self) -> None:
        """Interrupt current TTS synthesis"""
        self._interrupted = True

    async def aclose(self) -> None:
        """Cleanup resources"""
        self._interrupted = True
        self._closed = True
        if self._client:
            try:
                await self._client.aclose()
            except Exception as e:
                print(f"Error closing Groq TTS client: {e}")

    def get_supported_voices(self) -> list[str]:
        """Get list of supported Groq TTS voices"""
        return [
            "Fritz-PlayAI",
            "Rebecca-PlayAI", 
            "Deedee-PlayAI",
            "Clyde-PlayAI",
            "Athena-PlayAI",
        ]

    def is_voice_supported(self, voice: str) -> bool:
        """Check if a voice is supported by Groq TTS"""
        return voice in self.get_supported_voices()
