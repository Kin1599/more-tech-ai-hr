#!/usr/bin/env python3
"""
Простой тест для проверки работы модели T-pro-it-1.0.

Этот скрипт демонстрирует базовое использование T-pro модели без полной интеграции с VideoSDK.
"""

import asyncio
import logging
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_t_pro_basic():
    """Базовый тест T-pro модели"""
    try:
        # Импортируем необходимые модули
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
        
        logger.info("Загружаем модель T-pro-it-1.0...")
        
        # Загружаем токенизатор и модель
        model_name = "t-tech/T-pro-it-1.0"
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_name, 
            torch_dtype="auto",
            device_map="auto",
            trust_remote_code=True
        )
        
        logger.info("Модель успешно загружена!")
        
        # Устанавливаем seed для воспроизводимости
        torch.manual_seed(42)
        
        # Тестовый промпт
        prompt = "Напиши стих про машинное обучение"
        messages = [
            {"role": "system", "content": "Ты T-pro, виртуальный ассистент в Т-Технологии. Твоя задача - быть полезным диалоговым ассистентом."},
            {"role": "user", "content": prompt}
        ]
        
        # Применяем chat template
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        logger.info(f"Промпт: {prompt}")
        logger.info("Генерируем ответ...")
        
        # Токенизируем и генерируем
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=256,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Извлекаем только новые токены
        input_length = model_inputs.input_ids.shape[1]
        new_tokens = generated_ids[0][input_length:]
        
        # Декодируем ответ
        response = tokenizer.decode(new_tokens, skip_special_tokens=True)
        
        print("\n" + "="*50)
        print("ОТВЕТ T-PRO:")
        print("="*50)
        print(response)
        print("="*50)
        
        logger.info("Тест успешно завершен!")
        
        # Очищаем память
        del model
        del tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
    except ImportError as e:
        logger.error(f"Ошибка импорта: {e}")
        logger.error("Установите зависимости: pip install torch transformers")
        return False
    except Exception as e:
        logger.error(f"Ошибка тестирования: {e}")
        return False
    
    return True

async def test_t_pro_streaming():
    """Тест потокового режима T-pro"""
    try:
        logger.info("Тестируем потоковый режим...")
        
        # Импортируем наш модуль
        from t_pro_llm import TProLLM
        from videosdk.agents import ChatContext, ChatMessage, ChatRole
        
        # Создаем модель
        llm = TProLLM(
            model_name="t-tech/T-pro-it-1.0",
            temperature=0.7,
            max_new_tokens=256
        )
        
        # Устанавливаем системный промпт
        llm.set_system_prompt("""
        Ты T-pro, профессиональный HR-ассистент от Т-Технологии.
        Твоя задача - проводить технические интервью с кандидатами.
        Отвечай кратко и по делу.
        """)
        
        # Создаем контекст чата
        messages = ChatContext()
        messages.add_message(ChatMessage(
            role=ChatRole.USER,
            content="Начни интервью с кандидатом на позицию Python Developer. Задай первый вопрос."
        ))
        
        print("\n" + "="*50)
        print("ПОТОКОВЫЙ ОТВЕТ T-PRO:")
        print("="*50)
        
        # Получаем ответ потоково
        response_chunks = []
        async for chunk in llm.chat(messages):
            response_chunks.append(chunk.content)
            print(chunk.content, end="", flush=True)
        
        print("\n" + "="*50)
        
        # Очищаем ресурсы
        await llm.aclose()
        
        logger.info("Потоковый тест успешно завершен!")
        
    except ImportError as e:
        logger.error(f"Ошибка импорта VideoSDK: {e}")
        logger.error("Убедитесь, что VideoSDK установлен и настроен")
        return False
    except Exception as e:
        logger.error(f"Ошибка потокового тестирования: {e}")
        return False
    
    return True

async def test_benchmarks():
    """Показываем результаты бенчмарков"""
    try:
        from t_pro_llm import get_tpro_benchmarks
        
        benchmarks = get_tpro_benchmarks()
        
        print("\n" + "="*60)
        print("РЕЗУЛЬТАТЫ БЕНЧМАРКОВ T-PRO-IT-1.0")
        print("="*60)
        
        print("\n📊 Проприетарные модели:")
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
        
        print("\n" + "="*60)
        
    except Exception as e:
        logger.error(f"Ошибка получения бенчмарков: {e}")

async def main():
    """Основная функция тестирования"""
    print("🇷🇺 ТЕСТИРОВАНИЕ МОДЕЛИ T-PRO-IT-1.0")
    print("="*60)
    
    # Проверяем доступность CUDA
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA доступна: {torch.cuda.get_device_name()}")
        else:
            print("⚠️  CUDA недоступна, будет использоваться CPU")
    except ImportError:
        print("❌ PyTorch не установлен")
        return
    
    # Тест 1: Базовое использование
    print("\n🧪 Тест 1: Базовое использование модели")
    success1 = await test_t_pro_basic()
    
    if success1:
        # Тест 2: Потоковое получение
        print("\n🧪 Тест 2: Потоковое получение")
        success2 = await test_t_pro_streaming()
        
        # Тест 3: Бенчмарки
        print("\n🧪 Тест 3: Результаты бенчмарков")
        await test_benchmarks()
        
        if success2:
            print("\n✅ Все тесты успешно пройдены!")
            print("\n🎉 Модель T-pro-it-1.0 готова к использованию!")
        else:
            print("\n⚠️  Базовый тест прошел, но есть проблемы с VideoSDK интеграцией")
    else:
        print("\n❌ Базовый тест не прошел")
        print("\n💡 Убедитесь, что:")
        print("   - Установлен PyTorch: pip install torch")
        print("   - Установлен Transformers: pip install transformers")
        print("   - Доступен интернет для загрузки модели")
        print("   - Достаточно памяти для загрузки модели (32.8B параметров)")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        logger.exception("Детали ошибки:")
