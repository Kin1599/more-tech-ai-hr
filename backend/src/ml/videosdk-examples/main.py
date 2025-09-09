import asyncio, os, signal
from videosdk.agents import Agent, AgentSession, CascadingPipeline, JobContext, RoomOptions, WorkerJob,ConversationFlow
from videosdk.plugins.silero import SileroVAD
from videosdk.plugins.turn_detector import TurnDetector, pre_download_model
from videosdk.plugins.openai import OpenAITTS
from videosdk.plugins.cartesia import CartesiaSTT
from groq_llm import GroqLLM
from typing import AsyncIterator
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pre-downloading the Turn Detector model
pre_download_model()

class MyVoiceAgent(Agent):
    def __init__(self):
        super().__init__(instructions="You are a helpful voice assistant that can answer questions and help with tasks. Answer in russian language.")
    async def on_enter(self): await self.session.say("Hi? How can I help you?")
    async def on_exit(self): await self.session.say("Bye!")

async def start_session(context: JobContext):
    # Create agent and conversation flow
    agent = MyVoiceAgent()
    conversation_flow = ConversationFlow(agent)

    # Create pipeline
    pipeline = CascadingPipeline(
        stt=CartesiaSTT(model="ink-whisper", language="ru"),
        llm=GroqLLM(model="qwen/qwen3-32b"),
        tts=OpenAITTS(model="tts-1"),
        vad=SileroVAD(),
        turn_detector=TurnDetector()
    )

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