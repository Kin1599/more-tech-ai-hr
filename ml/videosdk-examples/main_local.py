import asyncio, os, json
import signal  # Standard Python signal module
from datetime import datetime
from videosdk.agents import Agent, AgentSession, CascadingPipeline, JobContext, RoomOptions, WorkerJob,ConversationFlow
from videosdk.plugins.silero import SileroVAD
from videosdk.plugins.turn_detector import TurnDetector, pre_download_model
from videosdk.plugins.openai import OpenAITTS
# External imports still needed for VideoSDK pipeline compatibility
from videosdk.plugins.cartesia import CartesiaSTT
from groq_llm import GroqLLM
from typing import AsyncIterator, Generator, Iterable, List, Optional, Tuple, Dict, Any
import logging
import numpy as np
import torch
import torchaudio
from huggingface_hub import hf_hub_download
from scipy import signal as scipy_signal  # Rename scipy.signal to avoid conflict

# STT dependencies
from tone.pipeline import StreamingCTCPipeline, TextPhrase  # type: ignore

# TTS dependencies
from f5_tts.infer.utils_infer import (
    infer_process,
    load_model,
    load_vocoder,
    preprocess_ref_audio_text,
)
from f5_tts.model import DiT
from ruaccent import RUAccent

# Chatbot dependencies
from langchain_groq import ChatGroq  # type: ignore

from langchain.schema import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    BaseMessage,
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pre-downloading the Turn Detector model
pre_download_model()

# ===== CONFIGURATION CLASS =====
class AgentConfig:
    """Configuration class for the voice agent"""
    
    def __init__(self):
        # STT Configuration
        self.stt_model_name = None  # Use default tone model
        self.stt_device = "cpu"  # or "cuda" if available
        self.stt_silence_threshold = 0.05
        self.stt_silence_duration = 1.2
        self.stt_chunk_size = 2400  # Required by tone.StreamingCTCPipeline
        
        # TTS Configuration
        self.tts_device = "cpu"  # or "cuda" if available
        self.tts_sample_rate = 24000
        self.tts_ref_audio_path = "tone/demo/audio_examples/audio_short.flac"
        self.tts_ref_text = "Привет, как дела?"
        self.tts_nfe_step = 16  # Lower for faster synthesis
        
        # LLM Configuration
        self.llm_model = "mixtral-8x7b-32768"
        self.llm_temperature = 0.7
        self.llm_max_tokens = None
        self.llm_system_prompt = "Ты полезный голосовой ассистент, который отвечает кратко и по делу на русском языке."
        
        # VAD Configuration
        self.vad_threshold = 0.5
        self.vad_min_speech_duration = 0.5
        self.vad_min_silence_duration = 1.0
        
        # Turn Detector Configuration
        self.turn_detector_threshold = 0.3
        
        # Agent Configuration
        self.agent_instructions = "Ты полезный голосовой ассистент, который отвечает кратко и по делу на русском языке. Ты можешь отвечать на вопросы и помогать с различными задачами."
        self.agent_greeting = "Привет! Как дела? Чем могу помочь?"
        self.agent_farewell = "До свидания! Было приятно пообщаться!"
        
        # Fallback Configuration
        self.use_fallback_on_error = True
        self.fallback_to_groq = True
        
        # Performance Configuration
        self.enable_gpu_if_available = True
        self.max_audio_buffer_size = 1024 * 1024  # 1MB
        self.audio_chunk_duration_ms = 20
        
    def auto_detect_device(self) -> str:
        """Auto-detect best available device"""
        if self.enable_gpu_if_available:
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                # MPS can be problematic with some models, so we default to CPU for stability
                logger.info("MPS detected but using CPU for better stability")
                return "cpu"
        return "cpu"
    
    def update_from_env(self):
        """Update configuration from environment variables"""
        import os
        
        # STT settings
        if os.getenv("STT_DEVICE"):
            self.stt_device = os.getenv("STT_DEVICE")
        if os.getenv("STT_SILENCE_THRESHOLD"):
            self.stt_silence_threshold = float(os.getenv("STT_SILENCE_THRESHOLD"))
        if os.getenv("STT_SILENCE_DURATION"):
            self.stt_silence_duration = float(os.getenv("STT_SILENCE_DURATION"))
            
        # TTS settings
        if os.getenv("TTS_DEVICE"):
            self.tts_device = os.getenv("TTS_DEVICE")
        if os.getenv("TTS_SAMPLE_RATE"):
            self.tts_sample_rate = int(os.getenv("TTS_SAMPLE_RATE"))
        if os.getenv("TTS_REF_AUDIO_PATH"):
            self.tts_ref_audio_path = os.getenv("TTS_REF_AUDIO_PATH")
        if os.getenv("TTS_REF_TEXT"):
            self.tts_ref_text = os.getenv("TTS_REF_TEXT")
            
        # LLM settings
        if os.getenv("LLM_MODEL"):
            self.llm_model = os.getenv("LLM_MODEL")
        if os.getenv("LLM_TEMPERATURE"):
            self.llm_temperature = float(os.getenv("LLM_TEMPERATURE"))
        if os.getenv("LLM_MAX_TOKENS"):
            self.llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS"))
        if os.getenv("LLM_SYSTEM_PROMPT"):
            self.llm_system_prompt = os.getenv("LLM_SYSTEM_PROMPT")
            
        # Force CPU if environment variable is set
        if os.getenv("FORCE_CPU", "").lower() in ("true", "1", "yes"):
            self.stt_device = "cpu"
            self.tts_device = "cpu"
            logger.info("Forced CPU usage via FORCE_CPU environment variable")
        else:
            # Auto-detect device if enabled
            if self.enable_gpu_if_available:
                detected_device = self.auto_detect_device()
                if self.stt_device == "auto":
                    self.stt_device = detected_device
                if self.tts_device == "auto":
                    self.tts_device = detected_device

# ===== VIDEOSDK-COMPATIBLE WRAPPERS =====
from videosdk.agents import STT as BaseSTT, STTResponse, SpeechEventType, SpeechData
from videosdk.agents import TTS as BaseTTS
from videosdk.agents import LLM as BaseLLM, LLMResponse, ChatContext, ChatRole
import io
import wave

class VideoSDKStreamingSTT(BaseSTT):
    """VideoSDK-compatible wrapper for StreamingTranscriber"""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        sample_rate: Optional[int] = None,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.2,
        **pipeline_kwargs,
    ) -> None:
        super().__init__()
        
        # Initialize the underlying transcriber
        self._transcriber = StreamingTranscriber(
            model_name=model_name,
            device=device,
            sample_rate=sample_rate,
            **pipeline_kwargs
        )
        
        # VAD parameters
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.input_sample_rate = 48000
        
        # State tracking
        self._is_speaking = False
        self._silence_frames = 0
        self._audio_buffer = bytearray()
        self._cancelled = False
        
    async def process_audio(
        self,
        audio_frames: bytes,
        language: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """Process audio frames using streaming transcription"""
        if self._cancelled:
            return
            
        try:
            self._audio_buffer.extend(audio_frames)
            
            # Simple VAD
            is_silent = self._is_silent(audio_frames)
            
            if not is_silent:
                if not self._is_speaking:
                    self._is_speaking = True
                self._silence_frames = 0
            else:
                if self._is_speaking:
                    self._silence_frames += len(audio_frames) // 4
                    silence_duration_frames = int(self.silence_duration * self.input_sample_rate)
                    
                    if self._silence_frames > silence_duration_frames:
                        await self._process_accumulated_audio()
                        self._is_speaking = False
                        self._silence_frames = 0
                        
        except Exception as e:
            self.emit("error", f"STT processing error: {str(e)}")
    
    def _is_silent(self, audio_chunk: bytes) -> bool:
        """Simple silence detection"""
        if not audio_chunk:
            return True
        try:
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
            threshold = int(self.silence_threshold * 32767)
            return np.max(np.abs(audio_data)) < threshold
        except Exception:
            return True
    
    async def _process_accumulated_audio(self) -> None:
        """Process accumulated audio buffer"""
        if not self._audio_buffer or self._cancelled:
            return
            
        try:
            # Check buffer size
            if len(self._audio_buffer) > 1024 * 1024:  # 1MB limit
                logger.warning("Audio buffer too large, clearing...")
                self._audio_buffer.clear()
                return
            
            # Convert to numpy array for processing (tone expects int32)
            audio_data = np.frombuffer(bytes(self._audio_buffer), dtype=np.int16)
            # Convert to int32 as expected by tone.StreamingCTCPipeline
            audio_data = audio_data.astype(np.int32)
            
            # Validate audio data
            if len(audio_data) == 0:
                self._audio_buffer.clear()
                return
            
            # Split audio into proper chunks for tone pipeline
            chunk_size = 2400  # Expected by tone.StreamingCTCPipeline (300ms at 8kHz)
            phrases = []
            
            for i in range(0, len(audio_data), chunk_size):
                if self._cancelled:
                    break
                    
                chunk = audio_data[i:i + chunk_size]
                
                # Pad last chunk if necessary
                if len(chunk) < chunk_size:
                    chunk = np.pad(chunk, (0, chunk_size - len(chunk)), 'constant', constant_values=0)
                
                # Process chunk with transcriber
                chunk_phrases = await self._transcriber.transcribe_chunk(chunk)
                phrases.extend(chunk_phrases)
            
            # Process collected phrases (tone returns TextPhrase objects)
            for phrase in phrases:
                if phrase and self._transcript_callback and not self._cancelled:
                    # Extract text from TextPhrase object
                    if hasattr(phrase, 'text'):
                        text = phrase.text.strip()
                    else:
                        text = str(phrase).strip()
                    
                    # Filter out very short or nonsensical phrases
                    if len(text) < 2 or len(text) > 500:
                        continue
                        
                    await self._transcript_callback(STTResponse(
                        event_type=SpeechEventType.FINAL,
                        data=SpeechData(text=text, language="ru"),
                        metadata={
                            "model": "streaming_ctc", 
                            "provider": "tone",
                            "start_time": getattr(phrase, 'start_time', None),
                            "end_time": getattr(phrase, 'end_time', None)
                        }
                    ))
            
            self._audio_buffer.clear()
            
        except MemoryError as e:
            logger.error(f"Memory error in audio processing: {e}")
            self._audio_buffer.clear()
            self.emit("error", f"Memory error in audio processing: {str(e)}")
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            self._audio_buffer.clear()
            self.emit("error", f"Audio processing error: {str(e)}")
    
    async def cancel_current_transcription(self) -> None:
        """Cancel current transcription"""
        self._cancelled = True
        
    async def aclose(self) -> None:
        """Cleanup resources"""
        self._cancelled = True
        self._audio_buffer.clear()
        if hasattr(self._transcriber, 'reset'):
            self._transcriber.reset()

class VideoSDKESpeechTTS(BaseTTS):
    """VideoSDK-compatible wrapper for ESpeechTTS"""
    
    def __init__(
        self, 
        device: Optional[str] = None,
        ref_audio_path: str = "tone/demo/audio_examples/audio_short.flac",
        ref_text: str = "Привет, как дела?",
        sample_rate: int = 24000,
        **kwargs
    ) -> None:
        super().__init__(sample_rate=sample_rate, num_channels=1)
        
        self._tts = ESpeechTTS(device=device)
        self.ref_audio_path = ref_audio_path
        self.ref_text = ref_text
        self._interrupted = False
        self._first_chunk_sent = False
        
    async def synthesize(
        self,
        text: AsyncIterator[str] | str,
        voice_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Synthesize text to speech"""
        self._interrupted = False
        
        try:
            # Load model if not already loaded
            if self._tts._model is None:
                await self._tts.load()
            
            if isinstance(text, str):
                await self._synthesize_text(text)
            else:
                accumulated_text = ""
                async for chunk in text:
                    if self._interrupted:
                        break
                    accumulated_text += chunk
                    
                    # Process complete sentences
                    if any(punct in accumulated_text for punct in ['.', '!', '?', '\n']):
                        sentences = self._split_sentences(accumulated_text)
                        for sentence in sentences[:-1]:  # All except last (might be incomplete)
                            if self._interrupted:
                                break
                            await self._synthesize_text(sentence)
                        accumulated_text = sentences[-1] if sentences else ""
                
                # Process remaining text
                if accumulated_text.strip() and not self._interrupted:
                    await self._synthesize_text(accumulated_text)
                    
        except Exception as e:
            self.emit("error", f"TTS synthesis failed: {str(e)}")
    
    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences"""
        sentences = []
        current = ""
        
        for char in text:
            current += char
            if char in '.!?\n':
                sentences.append(current.strip())
                current = ""
        
        if current.strip():
            sentences.append(current.strip())
            
        return [s for s in sentences if s.strip()]
    
    async def _synthesize_text(self, text: str) -> None:
        """Synthesize a single text segment"""
        if not text.strip() or self._interrupted:
            return
            
        # Validate text length
        if len(text) > 1000:
            logger.warning(f"Text too long ({len(text)} chars), truncating...")
            text = text[:1000] + "..."
            
        try:
            # Check if reference audio exists
            if not os.path.exists(self.ref_audio_path):
                logger.error(f"Reference audio not found: {self.ref_audio_path}")
                self.emit("error", f"Reference audio not found: {self.ref_audio_path}")
                return
            
            # Synthesize audio with timeout
            start_time = asyncio.get_event_loop().time()
            sample_rate, audio_data = await self._tts.synthesize(
                text=text,
                ref_audio_path=self.ref_audio_path,
                ref_text=self.ref_text,
                nfe_step=16,  # Faster synthesis
                speed=1.0
            )
            synthesis_time = asyncio.get_event_loop().time() - start_time
            
            if synthesis_time > 10.0:  # Warn if synthesis takes too long
                logger.warning(f"TTS synthesis took {synthesis_time:.2f}s for text: {text[:50]}...")
            
            if self._interrupted:
                return
                
            # Validate audio data
            if audio_data is None or len(audio_data) == 0:
                logger.warning("Empty audio data from TTS")
                return
                
            # Convert to bytes and stream
            if isinstance(audio_data, np.ndarray):
                # Validate audio range
                if np.max(np.abs(audio_data)) > 1.0:
                    logger.warning("Audio data out of range, normalizing...")
                    audio_data = audio_data / np.max(np.abs(audio_data))
                
                # Convert to 16-bit PCM
                audio_int16 = (audio_data * 32767).astype(np.int16)
                audio_bytes = audio_int16.tobytes()
                await self._stream_audio_chunks(audio_bytes)
                
        except FileNotFoundError as e:
            logger.error(f"File not found in TTS: {e}")
            self.emit("error", f"File not found in TTS: {str(e)}")
        except MemoryError as e:
            logger.error(f"Memory error in TTS: {e}")
            self.emit("error", f"Memory error in TTS: {str(e)}")
        except torch.cuda.OutOfMemoryError as e:
            logger.error(f"CUDA out of memory in TTS: {e}")
            self.emit("error", f"CUDA out of memory in TTS: {str(e)}")
        except Exception as e:
            logger.error(f"Audio synthesis error: {e}")
            self.emit("error", f"Audio synthesis error: {str(e)}")
    
    async def _stream_audio_chunks(self, audio_bytes: bytes) -> None:
        """Stream audio data in chunks"""
        if self._interrupted:
            return
            
        chunk_size = int(self.sample_rate * 1 * 2 * 20 / 1000)  # 20ms chunks
        
        for i in range(0, len(audio_bytes), chunk_size):
            if self._interrupted:
                break
                
            chunk = audio_bytes[i:i + chunk_size]
            
            if len(chunk) < chunk_size and len(chunk) > 0:
                padding_needed = chunk_size - len(chunk)
                chunk += b"\x00" * padding_needed
            
            if chunk:
                if not self._first_chunk_sent and self._first_audio_callback:
                    self._first_chunk_sent = True
                    await self._first_audio_callback()
                
                asyncio.create_task(self.audio_track.add_new_bytes(chunk))
                await asyncio.sleep(0.001)
    
    async def interrupt(self) -> None:
        """Interrupt current synthesis"""
        self._interrupted = True
    
    def reset_first_audio_tracking(self) -> None:
        """Reset first audio tracking"""
        self._first_chunk_sent = False
    
    async def aclose(self) -> None:
        """Cleanup resources"""
        self._interrupted = True

class VideoSDKLangChainLLM(BaseLLM):
    """VideoSDK-compatible wrapper for LangChainGroqChatbot"""
    
    def __init__(
        self,
        system_prompt: str = "Ты полезный голосовой ассистент, который отвечает кратко и по делу.",
        api_key: Optional[str] = None,
        model: str = "mixtral-8x7b-32768",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> None:
        super().__init__()
        
        self._chatbot = LangChainGroqChatbot(
            system_prompt=system_prompt,
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        self._cancelled = False
    
    async def chat(
        self,
        messages: ChatContext,
        tools: list = None,
        **kwargs: Any
    ) -> AsyncIterator[LLMResponse]:
        """Chat with the LLM"""
        self._cancelled = False
        
        try:
            # Get the last user message
            last_message = None
            for msg in reversed(messages.items):
                if hasattr(msg, 'role') and msg.role == ChatRole.USER:
                    last_message = msg.content
                    break
            
            if not last_message:
                return
            
            # Stream response
            for chunk in self._chatbot.ask_stream(last_message):
                if self._cancelled:
                    break
                    
                if chunk:
                    yield LLMResponse(
                        content=chunk,
                        role=ChatRole.ASSISTANT,
                        metadata={"model": self._chatbot._llm.model, "provider": "groq"}
                    )
                    
        except Exception as e:
            if not self._cancelled:
                self.emit("error", f"LLM chat error: {str(e)}")
    
    async def cancel_current_generation(self) -> None:
        """Cancel current generation"""
        self._cancelled = True
    
    async def aclose(self) -> None:
        """Cleanup resources"""
        self._cancelled = True

# ===== INTEGRATED STT CLASS =====
class StreamingTranscriber:
    """High-level wrapper around tone.StreamingCTCPipeline with performance optimizations.

    Parameters
    ----------
    model_name: Optional[str]
        Название модели HuggingFace (если None — дефолт из tone).
    device: Optional[str]
        'cpu' или 'cuda' (если поддерживается). Если None — авто.
    sample_rate: Optional[int]
        Используемая частота (должна совпадать с поступающими чанками).
    """
    
    _pipeline_cache = {}  # Class-level cache for pipelines
    _loading_lock = asyncio.Lock()

    def __init__(
        self,
        model_name: Optional[str] = None,  # Not used by tone, kept for compatibility
        device: Optional[str] = None,      # Not used by tone, kept for compatibility  
        sample_rate: Optional[int] = None, # Not used by tone, kept for compatibility
        **pipeline_kwargs,
    ) -> None:
        # Note: tone's StreamingCTCPipeline doesn't support custom model_name, device, or sample_rate
        # These parameters are kept for API compatibility but are not used
        self.pipeline_kwargs = pipeline_kwargs
        self._pipeline = None
        self._state = None  # internal pipeline state
        # Use decoder_type for cache key since that's the only configurable parameter
        decoder_type = pipeline_kwargs.get('decoder_type', 'BEAM_SEARCH')
        self._cache_key = f"tone_pipeline_{decoder_type}"
        
    async def _ensure_pipeline_loaded(self) -> None:
        """Ensure pipeline is loaded with caching"""
        if self._pipeline is not None:
            return
            
        # Check cache first
        if self._cache_key in self._pipeline_cache:
            self._pipeline = self._pipeline_cache[self._cache_key]
            logger.info("Loaded STT pipeline from cache")
            return
        
        # Use lock to prevent concurrent loading
        async with self._loading_lock:
            # Double-check after acquiring lock
            if self._cache_key in self._pipeline_cache:
                self._pipeline = self._pipeline_cache[self._cache_key]
                return
            
            logger.info("Loading STT pipeline...")
            start_time = asyncio.get_event_loop().time()
            
            # Hint: Run 'python preload_models.py' to cache models beforehand
            if not self._pipeline_cache:
                logger.info("💡 Совет: запустите 'python preload_models.py' для предзагрузки моделей")
            
            # Load in executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            
            # StreamingCTCPipeline.from_hugging_face only accepts decoder_type parameter
            from tone.decoder import DecoderType
            decoder_type = self.pipeline_kwargs.get('decoder_type', DecoderType.BEAM_SEARCH)
            
            self._pipeline = await loop.run_in_executor(
                None,
                lambda: StreamingCTCPipeline.from_hugging_face(decoder_type=decoder_type)
            )
            
            # Cache the pipeline
            self._pipeline_cache[self._cache_key] = self._pipeline
            
            load_time = asyncio.get_event_loop().time() - start_time
            logger.info(f"STT pipeline loaded in {load_time:.2f}s")

    async def transcribe_chunk(self, audio_chunk) -> List[TextPhrase]:
        """Отправить один аудио чанк и получить новые распознанные фразы.

        audio_chunk: bytes | np.ndarray | torch.Tensor (см. документацию tone)
        Возвращает список TextPhrase объектов.
        """
        await self._ensure_pipeline_loaded()
        if self._pipeline is None:
            return []
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        new_phrases, self._state = await loop.run_in_executor(
            None, lambda: self._pipeline.forward(audio_chunk, self._state)
        )
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

# ===== INTEGRATED TTS CLASS =====
MODEL_CFG = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)
MODEL_REPO = "ESpeech/ESpeech-TTS-1_RL-V2"
MODEL_FILE = "espeech_tts_rlv2.pt"
VOCAB_FILE = "vocab.txt"

class ESpeechTTS:
    _model_cache = {}  # Class-level cache for models
    _loading_lock = asyncio.Lock()  # Prevent concurrent loading
    
    def __init__(self, device: Optional[str] = None) -> None:
        # Properly handle device selection
        if device is None:
            if torch.cuda.is_available():
                self.device = "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                # MPS can cause issues with some models, prefer CPU for stability
                logger.info("MPS available but using CPU for TTS stability")
                self.device = "cpu"
            else:
                self.device = "cpu"
        else:
            self.device = device
            
        self._model = None
        self._vocoder = None
        self._accent = None
        self._cache_key = f"{self.device}_{MODEL_REPO}_{MODEL_FILE}"

    async def load(self) -> None:
        """Load model with caching and async support"""
        if self._model is not None:
            return
            
        # Check cache first
        if self._cache_key in self._model_cache:
            cached = self._model_cache[self._cache_key]
            self._model = cached['model']
            self._vocoder = cached['vocoder']
            self._accent = cached['accent']
            logger.info("Loaded TTS model from cache")
            return
        
        # Use lock to prevent concurrent loading
        async with self._loading_lock:
            # Double-check after acquiring lock
            if self._cache_key in self._model_cache:
                cached = self._model_cache[self._cache_key]
                self._model = cached['model']
                self._vocoder = cached['vocoder']
                self._accent = cached['accent']
                return
            
            logger.info("Loading TTS model...")
            start_time = asyncio.get_event_loop().time()
            
            # Hint: Run 'python preload_models.py' to cache models beforehand
            if not self._model_cache:
                logger.info("💡 Совет: запустите 'python preload_models.py' для предзагрузки моделей")
            
            # Load in executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            model_path = await loop.run_in_executor(
                None, hf_hub_download, MODEL_REPO, MODEL_FILE
            )
            vocab_path = await loop.run_in_executor(
                None, hf_hub_download, MODEL_REPO, VOCAB_FILE
            )
            
            self._model = await loop.run_in_executor(
                None, lambda: load_model(DiT, MODEL_CFG, model_path, vocab_file=vocab_path)
            )
            self._vocoder = await loop.run_in_executor(
                None, lambda: load_vocoder(device=self.device, is_local=False)
            )
            
            # Load accent model
            self._accent = RUAccent()
            await loop.run_in_executor(
                None, 
                lambda: self._accent.load(
                    omograph_model_size='turbo3.1', 
                    use_dictionary=True, 
                    tiny_mode=False
                )
            )
            
            # Move to device with proper error handling
            try:
                await loop.run_in_executor(None, lambda: self._model.to(self.device))
                await loop.run_in_executor(None, lambda: self._vocoder.to(self.device))
                logger.info(f"Models successfully moved to device: {self.device}")
            except Exception as e:
                logger.warning(f"Failed to move models to {self.device}, falling back to CPU: {e}")
                self.device = "cpu"
                await loop.run_in_executor(None, lambda: self._model.to(self.device))
                await loop.run_in_executor(None, lambda: self._vocoder.to(self.device))
            
            # Cache the loaded models
            self._model_cache[self._cache_key] = {
                'model': self._model,
                'vocoder': self._vocoder,
                'accent': self._accent
            }
            
            load_time = asyncio.get_event_loop().time() - start_time
            logger.info(f"TTS model loaded in {load_time:.2f}s")

    def _accentize(self, text: str) -> str:
        if not text or '+' in text:
            return text
        return self._accent.process_all(text) if self._accent else text

    @torch.no_grad()
    async def synthesize(
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
            await self.load()
        assert self._model is not None and self._vocoder is not None
        if seed is not None:
            torch.manual_seed(int(seed))
        # Load ref audio
        processed_ref_audio, processed_ref_text = preprocess_ref_audio_text(
            ref_audio_path, self._accentize(ref_text), show_info=lambda *a, **k: None
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

# ===== INTEGRATED CHATBOT CLASS =====
DEFAULT_MODEL = "mixtral-8x7b-32768"  # Change if you prefer llama3-70b-8192, etc.

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

class MyVoiceAgent(Agent):
    def __init__(self, config: AgentConfig):
        super().__init__(instructions=config.agent_instructions)
        self.config = config
    
    async def on_enter(self):
        await self.session.say(self.config.agent_greeting)
    
    async def on_exit(self):
        await self.session.say(self.config.agent_farewell)

async def start_session(context: JobContext):
    # Initialize configuration
    config = AgentConfig()
    config.update_from_env()
    
    # Create agent and conversation flow
    agent = MyVoiceAgent(config)
    conversation_flow = ConversationFlow(agent)

    # Create pipeline using integrated VideoSDK-compatible wrappers
    # These use our custom implementations instead of external APIs
    pipeline = None
    
    if config.use_fallback_on_error:
        try:
            # Try using integrated classes first
            logger.info("Initializing integrated VideoSDK-compatible pipeline...")
            pipeline = CascadingPipeline(
                stt=VideoSDKStreamingSTT(
                    model_name=config.stt_model_name,
                    device=config.stt_device,
                    silence_threshold=config.stt_silence_threshold,
                    silence_duration=config.stt_silence_duration,
                ),
                llm=VideoSDKLangChainLLM(
                    system_prompt=config.llm_system_prompt,
                    model=config.llm_model,
                    temperature=config.llm_temperature,
                    max_tokens=config.llm_max_tokens,
                ),
                tts=VideoSDKESpeechTTS(
                    device=config.tts_device,
                    sample_rate=config.tts_sample_rate,
                    ref_audio_path=config.tts_ref_audio_path,
                    ref_text=config.tts_ref_text,
                ),
                vad=SileroVAD(
                    threshold=config.vad_threshold,
                    min_speech_duration=config.vad_min_speech_duration,
                    min_silence_duration=config.vad_min_silence_duration,
                ),
                turn_detector=TurnDetector(
                    threshold=config.turn_detector_threshold,
                )
            )
            logger.info("Successfully initialized integrated VideoSDK-compatible pipeline")
        except Exception as e:
            # Fallback to Groq classes if integrated classes fail
            logger.warning(f"Failed to initialize integrated classes: {e}")
            pipeline = None
    
    if pipeline is None and config.fallback_to_groq:
        try:
            logger.info("Falling back to Groq API classes...")
            pipeline = CascadingPipeline(
                stt=GroqSTT(
                    model="whisper-large-v3-turbo",
                    silence_threshold=config.stt_silence_threshold,
                    silence_duration=config.stt_silence_duration,
                ),
                llm=GroqLLM(
                    model="llama-3.1-8b-instant",
                    temperature=config.llm_temperature,
                ),
                tts=GroqTTSFixed(model="playai-tts"),
                vad=SileroVAD(
                    threshold=config.vad_threshold,
                    min_speech_duration=config.vad_min_speech_duration,
                    min_silence_duration=config.vad_min_silence_duration,
                ),
                turn_detector=TurnDetector(
                    threshold=config.turn_detector_threshold,
                )
            )
            logger.info("Successfully initialized Groq fallback pipeline")
        except Exception as e:
            logger.error(f"Failed to initialize fallback pipeline: {e}")
            raise RuntimeError(f"Could not initialize any pipeline: {e}")
    
    if pipeline is None:
        raise RuntimeError("No pipeline could be initialized")

    session = AgentSession(
        agent=agent,
        pipeline=pipeline,
        conversation_flow=conversation_flow
    )

    # Создаем событие для корректного завершения работы
    shutdown_event = asyncio.Event()
    
    # Обработчик сигналов для корректного завершения
    def signal_handler(signum, frame):
        logger.info(f"Получен сигнал {signum}, начинаем корректное завершение...")
        shutdown_event.set()
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        logger.info("Подключение к VideoSDK...")
        await context.connect()
        logger.info("Запуск агента...")
        await session.start()
        logger.info("Агент запущен. Нажмите Ctrl+C для завершения.")
        
        # Ждем сигнала завершения
        await shutdown_event.wait()
        
    except KeyboardInterrupt:
        logger.info("Получено прерывание от пользователя")
        shutdown_event.set()
    except Exception as e:
        logger.error(f"Ошибка во время работы сессии: {e}")
        shutdown_event.set()
    finally:
        logger.info("Начинается завершение работы...")
        
        try:
            # Корректно закрываем сессию с таймаутом (это закроет pipeline компоненты)
            await asyncio.wait_for(session.close(), timeout=5.0)
            logger.info("Сессия закрыта")
        except asyncio.TimeoutError:
            logger.warning("Таймаут при закрытии сессии")
        except Exception as e:
            logger.error(f"Ошибка при закрытии сессии: {e}")
        
        try:
            # Корректно завершаем контекст с таймаутом
            await asyncio.wait_for(context.shutdown(), timeout=5.0)
            logger.info("Контекст завершен")
        except asyncio.TimeoutError:
            logger.warning("Таймаут при завершении контекста")
        except Exception as e:
            logger.error(f"Ошибка при завершении контекста: {e}")
        
        # Более безопасная очистка asyncio задач
    try:
        logger.info("Отменяем оставшиеся задачи...")
        current_task = asyncio.current_task()
        tasks = [task for task in asyncio.all_tasks() if task != current_task and not task.done()]
        
        if tasks:
            # Отменяем задачи
            for task in tasks:
                if not task.done():
                    task.cancel()
                    
            # Ждем завершения отмененных задач с коротким таймаутом
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                        timeout=2.0
                )
                logger.info(f"Корректно отменено {len(tasks)} задач")
            except asyncio.TimeoutError:
                logger.warning(f"Таймаут при отмене {len(tasks)} задач")
            except Exception as e:
                logger.error(f"Ошибка при отмене задач: {e}")
        else:
                logger.info("Нет задач для отмены")
            
    except Exception as e:
        logger.error(f"Ошибка при очистке задач: {e}")

        logger.info("Завершение работы завершено")

def make_context() -> JobContext:
    room_options = RoomOptions(
     #  room_id="YOUR_MEETING_ID",  # Set to join a pre-created room; omit to auto-create
        name="VideoSDK Cascaded Agent",
        playground=True
    )

    return JobContext(room_options=room_options)

if __name__ == "__main__":
    job = WorkerJob(entrypoint=start_session, jobctx=make_context)
    job.start()