#!/usr/bin/env python3
"""
Скрипт для предварительной загрузки моделей TTS и STT.
Запустите этот скрипт заранее, чтобы модели были загружены в кэш.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Добавляем текущую директорию в путь для импортов
sys.path.insert(0, str(Path(__file__).parent))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def preload_tts_model():
    """Предварительно загружаем TTS модель"""
    try:
        logger.info("🔄 Загружаем TTS модель (F5-TTS)...")
        
        # Импортируем необходимые модули
        from main2 import ESpeechTTS
        import torch
        
        # Определяем устройство
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Используем устройство: {device}")
        
        # Создаем и загружаем модель
        tts = ESpeechTTS(device=device)
        await tts.load()
        
        logger.info("✅ TTS модель успешно загружена и кэширована!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке TTS модели: {e}")
        return False

async def preload_stt_pipeline():
    """Предварительно загружаем STT пайплайн"""
    try:
        logger.info("🔄 Загружаем STT пайплайн (tone)...")
        
        from main2 import StreamingTranscriber
        
        # Создаем транскрайбер и загружаем пайплайн
        transcriber = StreamingTranscriber()
        await transcriber._ensure_pipeline_loaded()
        
        logger.info("✅ STT пайплайн успешно загружен и кэширован!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке STT пайплайна: {e}")
        return False

async def download_models():
    """Загружаем модели из Hugging Face Hub"""
    try:
        logger.info("🔄 Загружаем модели из Hugging Face Hub...")
        
        from huggingface_hub import hf_hub_download
        
        # TTS модель
        logger.info("Загружаем F5-TTS модель...")
        model_path = hf_hub_download(
            repo_id="ESpeech/ESpeech-TTS-1_RL-V2", 
            filename="espeech_tts_rlv2.pt"
        )
        vocab_path = hf_hub_download(
            repo_id="ESpeech/ESpeech-TTS-1_RL-V2", 
            filename="vocab.txt"
        )
        logger.info(f"✅ F5-TTS модель загружена: {model_path}")
        
        # Turn Detector модель (если нужна)
        try:
            from videosdk.plugins.turn_detector import pre_download_model
            pre_download_model()
            logger.info("✅ Turn Detector модель загружена")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить Turn Detector: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке моделей: {e}")
        return False

async def main():
    """Основная функция предзагрузки"""
    logger.info("🚀 Начинаем предварительную загрузку моделей...")
    
    success_count = 0
    total_count = 3
    
    # Загружаем файлы моделей
    if await download_models():
        success_count += 1
    
    # Загружаем STT пайплайн
    if await preload_stt_pipeline():
        success_count += 1
    
    # Загружаем TTS модель
    if await preload_tts_model():
        success_count += 1
    
    logger.info(f"🎯 Предзагрузка завершена: {success_count}/{total_count} моделей загружено успешно")
    
    if success_count == total_count:
        logger.info("🎉 Все модели успешно загружены! Теперь main2.py будет запускаться быстрее.")
        return 0
    else:
        logger.warning("⚠️ Некоторые модели не удалось загрузить. Проверьте ошибки выше.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
