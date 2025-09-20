"""
Пример использования модели T-pro-it-1.0 от T-Tech для русскоязычных интервью.

Демонстрирует интеграцию T-pro модели в систему интервью с поддержкой потокового получения.
"""

import asyncio
import logging
from typing import List, Dict, Any
from videosdk.agents import ChatContext, ChatMessage, ChatRole
from .t_pro_llm import TProLLM, TProLLMWithVLLM, create_tpro_llm, get_tpro_benchmarks
from .streaming_config import StreamingConfig, load_preset_config

logger = logging.getLogger(__name__)

class TProInterviewExample:
    """Пример использования T-pro для интервью"""
    
    def __init__(self, use_vllm: bool = False):
        self.use_vllm = use_vllm
        self.llm = None
        self.streaming_config = load_preset_config("balanced")
        
    async def initialize(self):
        """Инициализация T-pro модели"""
        try:
            logger.info("Инициализируем T-pro модель...")
            
            # Создаем T-pro LLM
            self.llm = create_tpro_llm(
                use_vllm=self.use_vllm,
                model_name="t-tech/T-pro-it-1.0",
                temperature=0.7,
                max_new_tokens=512
            )
            
            # Устанавливаем системный промпт для интервью
            interview_prompt = """
            Ты T-pro, профессиональный HR-ассистент от Т-Технологии. 
            Твоя задача - проводить технические интервью с кандидатами.
            
            Твои качества:
            - Профессиональный и вежливый тон
            - Глубокие знания в области IT и разработки
            - Умение задавать правильные вопросы
            - Способность оценивать ответы кандидатов
            - Поддержка кандидата в процессе интервью
            
            Начинай интервью с приветствия и краткого представления.
            """
            
            self.llm.set_system_prompt(interview_prompt)
            
            logger.info("T-pro модель успешно инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации T-pro: {e}")
            raise
    
    async def conduct_interview(self, candidate_name: str, position: str) -> List[Dict[str, Any]]:
        """Провести интервью с кандидатом"""
        if not self.llm:
            await self.initialize()
        
        interview_log = []
        
        try:
            # Создаем контекст чата
            messages = ChatContext()
            
            # Приветствие
            greeting = f"Здравствуйте, {candidate_name}! Меня зовут T-pro, я HR-ассистент от Т-Технологии. Сегодня мы проведем техническое интервью на позицию {position}. Готовы начать?"
            
            messages.add_message(ChatMessage(
                role=ChatRole.USER,
                content=greeting
            ))
            
            # Получаем ответ от T-pro
            response_chunks = []
            async for chunk in self.llm.chat(messages):
                response_chunks.append(chunk.content)
                print(f"T-pro: {chunk.content}", end="", flush=True)
            
            full_response = "".join(response_chunks)
            
            interview_log.append({
                "speaker": "T-pro",
                "message": full_response,
                "timestamp": asyncio.get_event_loop().time()
            })
            
            # Добавляем ответ в контекст
            messages.add_message(ChatMessage(
                role=ChatRole.ASSISTANT,
                content=full_response
            ))
            
            # Симуляция ответа кандидата
            candidate_responses = [
                "Да, готов! Расскажите, пожалуйста, что будет входить в мои обязанности?",
                "Я работаю с Python уже 3 года, также знаю Django, FastAPI, PostgreSQL. Недавно изучаю Docker и Kubernetes.",
                "В моем последнем проекте я разрабатывал REST API для системы управления заказами. Использовал FastAPI, PostgreSQL, Redis для кэширования.",
                "Да, сталкивался с проблемой N+1 запросов. Решил через select_related и prefetch_related в Django ORM.",
                "Спасибо за интервью! Было очень интересно пообщаться с AI-ассистентом."
            ]
            
            for i, candidate_response in enumerate(candidate_responses):
                print(f"\n\nКандидат: {candidate_response}")
                
                interview_log.append({
                    "speaker": "Кандидат",
                    "message": candidate_response,
                    "timestamp": asyncio.get_event_loop().time()
                })
                
                # Добавляем ответ кандидата в контекст
                messages.add_message(ChatMessage(
                    role=ChatRole.USER,
                    content=candidate_response
                ))
                
                # Получаем ответ от T-pro
                response_chunks = []
                async for chunk in self.llm.chat(messages):
                    response_chunks.append(chunk.content)
                    print(f"T-pro: {chunk.content}", end="", flush=True)
                
                full_response = "".join(response_chunks)
                
                interview_log.append({
                    "speaker": "T-pro",
                    "message": full_response,
                    "timestamp": asyncio.get_event_loop().time()
                })
                
                # Добавляем ответ в контекст
                messages.add_message(ChatMessage(
                    role=ChatRole.ASSISTANT,
                    content=full_response
                ))
                
                # Небольшая пауза между вопросами
                await asyncio.sleep(1)
            
            return interview_log
            
        except Exception as e:
            logger.error(f"Ошибка проведения интервью: {e}")
            raise
    
    async def test_technical_questions(self) -> List[str]:
        """Тестирование технических вопросов"""
        if not self.llm:
            await self.initialize()
        
        technical_questions = [
            "Расскажите о принципах SOLID в программировании",
            "В чем разница между REST и GraphQL?",
            "Объясните паттерн MVC",
            "Что такое микросервисная архитектура?",
            "Как работает кэширование в веб-приложениях?"
        ]
        
        responses = []
        
        for question in technical_questions:
            print(f"\n\nВопрос: {question}")
            
            messages = ChatContext()
            messages.add_message(ChatMessage(
                role=ChatRole.USER,
                content=f"Ответь на технический вопрос: {question}"
            ))
            
            response_chunks = []
            async for chunk in self.llm.chat(messages):
                response_chunks.append(chunk.content)
                print(f"T-pro: {chunk.content}", end="", flush=True)
            
            full_response = "".join(response_chunks)
            responses.append(full_response)
            
            await asyncio.sleep(0.5)
        
        return responses
    
    async def benchmark_comparison(self):
        """Сравнение с другими моделями"""
        benchmarks = get_tpro_benchmarks()
        
        print("\n=== Сравнение T-pro-it-1.0 с другими моделями ===\n")
        
        print("📊 Проприетарные модели:")
        for benchmark, results in benchmarks["proprietary_models"].items():
            print(f"\n{benchmark}:")
            for model, score in results.items():
                if model == "T-pro-it-1.0":
                    print(f"  🏆 {model}: {score}")
                else:
                    print(f"     {model}: {score}")
        
        print("\n📊 Open-source модели:")
        for benchmark, results in benchmarks["open_source_models"].items():
            print(f"\n{benchmark}:")
            for model, score in results.items():
                if model == "T-pro-it-1.0":
                    print(f"  🏆 {model}: {score}")
                else:
                    print(f"     {model}: {score}")
    
    async def cleanup(self):
        """Очистка ресурсов"""
        if self.llm:
            await self.llm.aclose()
            logger.info("T-pro ресурсы очищены")

async def main():
    """Основная функция для демонстрации"""
    logging.basicConfig(level=logging.INFO)
    
    # Создаем пример
    example = TProInterviewExample(use_vllm=False)  # Используем обычную версию
    
    try:
        # Инициализируем модель
        await example.initialize()
        
        # Показываем информацию о модели
        model_info = example.llm.get_model_info()
        print(f"\n=== Информация о модели ===")
        print(f"Название: {model_info['name']}")
        print(f"Провайдер: {model_info['provider']}")
        print(f"Язык: {model_info['language']}")
        print(f"Базовая модель: {model_info['base_model']}")
        print(f"Параметры: {model_info['parameters']}")
        print(f"Инициализирована: {model_info['initialized']}")
        
        # Проводим интервью
        print(f"\n=== Проведение интервью ===")
        interview_log = await example.conduct_interview("Алексей", "Python Developer")
        
        # Тестируем технические вопросы
        print(f"\n=== Технические вопросы ===")
        technical_responses = await example.test_technical_questions()
        
        # Показываем бенчмарки
        await example.benchmark_comparison()
        
        # Сохраняем лог интервью
        print(f"\n=== Лог интервью ===")
        for entry in interview_log:
            print(f"[{entry['timestamp']:.2f}] {entry['speaker']}: {entry['message'][:100]}...")
        
    except Exception as e:
        logger.error(f"Ошибка в демонстрации: {e}")
    finally:
        await example.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
