"""
Утилита для предварительной загрузки ML моделей при старте приложения.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from .resume_similarity import get_embedding_model

logger = logging.getLogger(__name__)


def preload_models():
    """
    Предварительная загрузка всех ML моделей.
    Вызывается при старте приложения для ускорения первых запросов.
    """
    try:
        logger.info("Starting ML models preloading...")
        
        # Загружаем модель эмбеддингов
        embedding_model = get_embedding_model()
        
        # Тестируем модель на простом тексте
        test_text = "Software engineer with 5 years of experience in Python and JavaScript"
        test_embedding = embedding_model.get_embedding(test_text)
        
        if test_embedding is not None:
            logger.info(f"Resume similarity model loaded successfully. Embedding dimension: {test_embedding.shape}")
        else:
            logger.warning("Resume similarity model loaded with fallback implementation")
        
        logger.info("ML models preloading completed successfully")
        
    except Exception as e:
        logger.error(f"Error during ML models preloading: {e}")
        # Не прерываем запуск приложения, модели загрузятся при первом использовании


@asynccontextmanager
async def ml_lifespan_manager(app):
    """
    Менеджер жизненного цикла для FastAPI приложения.
    Загружает модели при старте и освобождает ресурсы при завершении.
    """
    # Startup
    logger.info("Initializing ML components...")
    
    # Запускаем загрузку моделей в отдельном потоке, чтобы не блокировать старт
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, preload_models)
    
    yield
    
    # Shutdown
    logger.info("Shutting down ML components...")
    # Здесь можно добавить очистку ресурсов, если необходимо
