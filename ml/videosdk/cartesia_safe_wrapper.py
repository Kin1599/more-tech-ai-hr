import asyncio
import logging
import re
from typing import Optional, AsyncIterator, Any
from videosdk.plugins.cartesia import CartesiaTTS, CartesiaSTT
from videosdk.agents import TTS, STT

logger = logging.getLogger(__name__)

def is_text_valid_for_tts(text: str) -> bool:
    """
    Проверяет, подходит ли текст для TTS синтеза
    
    Args:
        text: Текст для проверки
        
    Returns:
        bool: True если текст подходит для синтеза
    """
    if not text or not text.strip():
        return False
    
    # Убираем пробелы и проверяем длину
    clean_text = text.strip()
    if len(clean_text) < 2:
        return False
    
    # Проверяем, что текст содержит не только пунктуацию
    # Удаляем всю пунктуацию и пробелы
    text_without_punct = re.sub(r'[^\w\s]', '', clean_text)
    text_without_punct = re.sub(r'\s+', '', text_without_punct)
    
    # Если после удаления пунктуации ничего не осталось
    if not text_without_punct:
        return False
    
    # Проверяем, что есть хотя бы одна буква
    if not re.search(r'[a-zA-Zа-яА-ЯёЁ]', text_without_punct):
        return False
    
    return True

class SafeCartesiaTTSWrapper(TTS):
    """
    Безопасная обертка для Cartesia TTS с валидацией текста и защитой от ошибок
    """
    
    def __init__(
        self,
        model: str = "sonic-2",
        voice_id: str = "794f9389-aac1-45b6-b726-9d9369183238",
        language: str = "en",
        sample_rate: int = 24000,
        num_channels: int = 1,
        **kwargs
    ):
        super().__init__(sample_rate=sample_rate, num_channels=num_channels)
        self.model = model
        self.voice_id = voice_id
        self.language = language
        self.kwargs = kwargs
        self._tts = None
        self._lock = asyncio.Lock()
        self._initialized = False
        self._synthesis_lock = asyncio.Lock()
        
        # Атрибуты, которые ожидает VideoSDK
        self.audio_track = None
        self.loop = None
        
        logger.info(f"Создана безопасная обертка Cartesia TTS: модель={model}, голос={voice_id}, язык={language}")
    
    async def _ensure_initialized(self):
        """Инициализация TTS с блокировкой"""
        if not self._initialized:
            async with self._lock:
                if not self._initialized:
                    try:
                        self._tts = CartesiaTTS(
                            model=self.model,
                            voice_id=self.voice_id,
                            language=self.language,
                            **self.kwargs
                        )
                        
                        # Передаем атрибуты VideoSDK в базовый TTS
                        if self.audio_track is not None:
                            self._tts.audio_track = self.audio_track
                        if self.loop is not None:
                            self._tts.loop = self.loop
                            
                        self._initialized = True
                        logger.info("Cartesia TTS успешно инициализирован")
                    except Exception as e:
                        logger.error(f"Ошибка инициализации Cartesia TTS: {e}")
                        raise
    
    async def synthesize(self, text: str | AsyncIterator[str], voice_id: Optional[str] = None, **kwargs) -> None:
        """
        Безопасный синтез речи с валидацией текста
        """
        await self._ensure_initialized()
        
        # Используем блокировку для предотвращения concurrent calls
        async with self._synthesis_lock:
            try:
                await self._safe_synthesize(text, voice_id, **kwargs)
            except asyncio.CancelledError:
                logger.info("Синтез речи был прерван")
                raise
            except Exception as e:
                logger.error(f"Ошибка в синтезе речи: {e}")
                raise
    
    async def _safe_synthesize(self, text: str | AsyncIterator[str], voice_id: Optional[str] = None, **kwargs) -> None:
        """Внутренний метод безопасного синтеза"""
        try:
            # Собираем весь текст
            if isinstance(text, str):
                full_text = text
            else:
                full_text = ""
                async for chunk in text:
                    full_text += chunk
            
            # Валидация текста
            if not is_text_valid_for_tts(full_text):
                logger.warning(f"Текст не подходит для TTS синтеза: '{full_text[:50]}...'")
                # Просто возвращаемся без ошибки
                return
            
            logger.debug(f"Синтезируем валидный текст: {full_text[:100]}...")
            
            # Делегируем синтез напрямую к Cartesia TTS
            await self._tts.synthesize(full_text, voice_id=voice_id, **kwargs)
                    
        except Exception as e:
            logger.error(f"Ошибка в _safe_synthesize: {e}")
            # Пересоздаем TTS при критических ошибках
            if "Concurrent call" in str(e) or "WebSocket" in str(e):
                logger.info("Пересоздаем Cartesia TTS из-за ошибки соединения")
                self._initialized = False
                self._tts = None
            raise
    
    async def interrupt(self):
        """Прерывание синтеза"""
        logger.debug("TTS interrupt() вызван")
        if self._tts and hasattr(self._tts, 'interrupt'):
            try:
                await self._tts.interrupt()
                logger.debug("TTS успешно прерван")
            except Exception as e:
                logger.warning(f"Ошибка при прерывании TTS: {e}")
        else:
            logger.warning("TTS не инициализирован или не поддерживает interrupt")
    
    async def aclose(self):
        """Закрытие соединения"""
        # Прерываем текущий синтез
        try:
            await self.interrupt()
        except Exception as e:
            logger.warning(f"Ошибка при прерывании во время закрытия: {e}")
        
        async with self._lock:
            if self._tts and hasattr(self._tts, 'aclose'):
                try:
                    await self._tts.aclose()
                    logger.info("Cartesia TTS соединение закрыто")
                except Exception as e:
                    logger.error(f"Ошибка при закрытии TTS: {e}")
            self._initialized = False
            self._tts = None
    
    def _set_loop_and_audio_track(self, loop, audio_track):
        """Метод, который вызывает VideoSDK для установки loop и audio_track"""
        self.loop = loop
        self.audio_track = audio_track
        
        # Если TTS уже инициализирован, передаем атрибуты
        if self._tts is not None:
            self._tts.loop = loop
            self._tts.audio_track = audio_track
        
        logger.debug(f"Установлены loop и audio_track для Cartesia TTS: {type(audio_track).__name__ if audio_track else None}")
    
    def reset_first_audio_tracking(self) -> None:
        """Reset the first audio tracking state for next TTS task"""
        if self._tts and hasattr(self._tts, 'reset_first_audio_tracking'):
            self._tts.reset_first_audio_tracking()
        else:
            # Базовая реализация из родительского класса
            super().reset_first_audio_tracking()

class SafeCartesiaSTTWrapper(STT):
    """
    Безопасная обертка для Cartesia STT
    """
    
    def __init__(
        self,
        model: str = "ink-whisper",
        language: str = "en",
        **kwargs
    ):
        super().__init__()
        self.model = model
        self.language = language
        self.kwargs = kwargs
        self._stt = None
        self._lock = asyncio.Lock()
        self._initialized = False
        
        logger.info(f"Создана безопасная обертка Cartesia STT: модель={model}, язык={language}")
    
    async def _ensure_initialized(self):
        """Инициализация STT с блокировкой"""
        if not self._initialized:
            async with self._lock:
                if not self._initialized:
                    try:
                        self._stt = CartesiaSTT(
                            model=self.model,
                            language=self.language,
                            **self.kwargs
                        )
                        
                        # Передаем callback если он был установлен
                        if hasattr(self, '_transcript_callback') and self._transcript_callback:
                            self._stt._transcript_callback = self._transcript_callback
                            logger.debug("Callback передан в базовый Cartesia STT")
                        
                        # Включаем debug логирование для базового STT
                        cartesia_logger = logging.getLogger('videosdk.plugins.cartesia.stt')
                        cartesia_logger.setLevel(logging.DEBUG)
                        
                        self._initialized = True
                        logger.info("Cartesia STT успешно инициализирован")
                    except Exception as e:
                        logger.error(f"Ошибка инициализации Cartesia STT: {e}")
                        raise
    
    async def process_audio(self, audio_frames: bytes, language: Optional[str] = None, **kwargs) -> None:
        """Безопасная обработка аудио"""
        logger.debug(f"Получены аудио данные: {len(audio_frames)} байт")
        
        await self._ensure_initialized()
        
        try:
            # Используем переданный язык или язык по умолчанию
            process_language = language or self.language
            logger.debug(f"Обрабатываем аудио на языке: {process_language}")
            
            # Cartesia STT не возвращает генератор, а использует callback
            await self._stt.process_audio(audio_frames, language=process_language, **kwargs)
            logger.debug("Аудио данные отправлены в Cartesia STT")
            
        except Exception as e:
            logger.error(f"Ошибка обработки аудио: {e}")
            # Пересоздаем STT при ошибке
            self._initialized = False
            self._stt = None
            raise
    
    async def aclose(self):
        """Закрытие соединения"""
        async with self._lock:
            if self._stt and hasattr(self._stt, 'aclose'):
                try:
                    await self._stt.aclose()
                    logger.info("Cartesia STT соединение закрыто")
                except Exception as e:
                    logger.error(f"Ошибка при закрытии STT: {e}")
            self._initialized = False
            self._stt = None
    
    def on_stt_transcript(self, callback):
        """Устанавливает callback для получения транскрипций STT"""
        # Создаем обертку для callback, чтобы обеспечить правильную передачу
        async def wrapped_callback(response):
            try:
                logger.debug(f"STT получил транскрипцию: {response}")
                if callback:
                    await callback(response)
            except Exception as e:
                logger.error(f"Ошибка в STT callback: {e}")
        
        self._transcript_callback = wrapped_callback
        
        # Если STT уже инициализирован, передаем callback
        if self._stt is not None:
            self._stt._transcript_callback = wrapped_callback
        
        logger.debug("Установлен callback для STT транскрипций")

def create_safe_cartesia_tts(
    model: str = "sonic-2",
    voice_id: str = "794f9389-aac1-45b6-b726-9d9369183238",
    language: str = "en",
    **kwargs
) -> SafeCartesiaTTSWrapper:
    """Создать безопасную обертку Cartesia TTS"""
    return SafeCartesiaTTSWrapper(
        model=model,
        voice_id=voice_id,
        language=language,
        **kwargs
    )

def create_safe_cartesia_stt(
    model: str = "ink-whisper",
    language: str = "en",
    **kwargs
) -> SafeCartesiaSTTWrapper:
    """Создать безопасную обертку Cartesia STT"""
    return SafeCartesiaSTTWrapper(
        model=model,
        language=language,
        **kwargs
    )
