import asyncio, os, signal
from videosdk.agents import Agent, AgentSession, CascadingPipeline, JobContext, RoomOptions, WorkerJob,ConversationFlow
from videosdk.plugins.silero import SileroVAD
from videosdk.plugins.turn_detector import TurnDetector, pre_download_model
from videosdk.plugins.openai import OpenAITTS
from videosdk.plugins.cartesia import CartesiaTTS, CartesiaSTT
from cartesia_safe_wrapper import SafeCartesiaTTSWrapper, SafeCartesiaSTTWrapper
from groq_stt import GroqSTT
from groq_llm import GroqLLM
from videosdk.agents import LLM, LLMResponse, ChatContext, ChatRole, ChatMessage
from groq_tts_fixed import GroqTTSFixed
from chatbot import LangChainGroqChatbot, build_interview_system_prompt
from interview_configs import (
    get_interview_config, 
    get_interview_config_with_fallback,
    get_interview_config_from_database,
    list_available_configs,
    validate_interview_config,
    create_interview_summary_for_db
)
from db_service import InterviewDatabaseService, get_interview_context_from_db, get_interview_models_config_from_db
from model_service import ModelConfigurationService, log_model_usage_simple
from model_factory import ModelFactory, create_interview_models, ModelCreationError
from typing import AsyncIterator, Optional, List
import logging
import json
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Включаем debug для Cartesia компонентов
logging.getLogger('cartesia_safe_wrapper').setLevel(logging.DEBUG)

# Pre-downloading the Turn Detector model
pre_download_model()

class InterviewAgent(Agent):
    def __init__(
        self,
        # Обязательные параметры для работы с БД
        applicant_id: int,
        vacancy_id: int,
        # Параметры для fallback (если БД недоступна)
        job_description: str = "Разработчик Python",
        position: str = "Middle Python Developer", 
        company: str = "TechCompany",
        competencies: Optional[List[str]] = None,
        candidate_resume: Optional[str] = None,
        # Настройки интервью
        max_questions: int = 12,
        auto_save_results: bool = True,
        save_directory: str = "./interview_results",
        # Дополнительные параметры БД
        db_session: Optional[any] = None,
        config_name: str = "python_developer",
        use_database: bool = True
    ):
        """
        Интервью-агент для автоматического проведения технических интервью.
        Автоматически загружает конфигурацию из базы данных на основе ID кандидата и вакансии.
        
        Args:
            applicant_id: ID кандидата в базе данных (обязательный)
            vacancy_id: ID вакансии в базе данных (обязательный)
            job_description: Описание вакансии (fallback, если БД недоступна)
            position: Название позиции (fallback, если БД недоступна)
            company: Название компании (fallback, если БД недоступна)
            competencies: Список ключевых компетенций (fallback, если БД недоступна)
            candidate_resume: Резюме кандидата (fallback, если БД недоступна)
            max_questions: Максимальное количество основных вопросов
            auto_save_results: Автоматически сохранять результаты интервью
            save_directory: Директория для сохранения результатов
            db_session: Сессия базы данных (опционально)
            config_name: Имя статической конфигурации (только для крайнего fallback)
            use_database: Использовать данные из базы данных (по умолчанию True)
        """
        # Валидация обязательных параметров
        if not applicant_id or not vacancy_id:
            raise ValueError(f"Обязательные параметры отсутствуют: applicant_id={applicant_id}, vacancy_id={vacancy_id}")
        
        # Сохраняем параметры БД для последующего использования
        self.applicant_id = applicant_id
        self.vacancy_id = vacancy_id
        self.db_session = db_session
        self.use_database = use_database
        
        # Загружаем конфигурацию AI моделей
        self.models_config = None
        self.custom_models = None
        try:
            self.models_config = get_interview_models_config_from_db(vacancy_id, db_session)
            if self.models_config:
                logger.info(f"Загружена конфигурация AI моделей для вакансии {vacancy_id}")
                # Создаем модели на основе конфигурации
                self.custom_models = create_interview_models(vacancy_id, db_session)
                # Извлекаем Avatar модель для использования в пайплайне
                self.avatar = self.custom_models.get("avatar") if self.custom_models else None
                # Извлекаем Vision модель для анализа экрана
                self.vision_model = self.custom_models.get("vision") if self.custom_models else None
            else:
                logger.warning(f"Конфигурация AI моделей не найдена для вакансии {vacancy_id}, используем значения по умолчанию")
                self.avatar = None
                self.vision_model = None
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации AI моделей: {e}")
            logger.info("Будут использованы модели по умолчанию")
            self.avatar = None
            self.vision_model = None
        
        # Загружаем конфигурацию из БД (обязательно)
        try:
            db_config = get_interview_config_with_fallback(
                applicant_id=applicant_id,
                vacancy_id=vacancy_id,
                config_name=config_name,
                db_session=db_session
            )
            
            if not db_config:
                raise RuntimeError("Не удалось загрузить конфигурацию интервью")
                
            config_source = db_config.get('source', 'database')
            if config_source == 'static_config':
                logger.warning(f"Используется статическая конфигурация как fallback для applicant {applicant_id}, vacancy {vacancy_id}")
            else:
                logger.info(f"Загружена конфигурация из БД для applicant {applicant_id}, vacancy {vacancy_id}")
                
        except Exception as e:
            logger.error(f"Критическая ошибка загрузки конфигурации из БД: {e}")
            raise RuntimeError(f"Не удалось инициализировать интервью для applicant {applicant_id}, vacancy {vacancy_id}") from e
        
        # Всегда используем данные из конфигурации (БД или fallback)
        job_description = db_config.get("job_description", job_description)
        position = db_config.get("position", position)
        company = db_config.get("company", company)
        competencies = db_config.get("competencies", competencies)
        candidate_resume = db_config.get("candidate_resume", candidate_resume)
        
        # Сохраняем дополнительную информацию из БД
        self.ai_hr_instructions = db_config.get("ai_hr_instructions", "")
        self.applicant_name = db_config.get("applicant_name", "Кандидат")
        self.experience_required = db_config.get("experience_required", 0)
        self.degree_required = db_config.get("degree_required", False)
        self.special_requirements = db_config.get("special_requirements", {})
        
        # Устанавливаем компетенции по умолчанию для Python разработчика, если не указаны
        if competencies is None:
            competencies = [
                "Python и его экосистема",
                "Веб-фреймворки (Django/FastAPI/Flask)",
                "Базы данных и ORM",
                "API разработка",
                "Тестирование",
                "Git и командная работа",
                "Архитектурное мышление"
            ]
        
        # Создаем расширенный системный промпт для интервью с учетом данных из БД
        enhanced_job_description = job_description
        if self.ai_hr_instructions:
            enhanced_job_description += f"\n\nДополнительные указания от HR:\n{self.ai_hr_instructions}"
        
        if self.special_requirements:
            special_req_text = "\n\nСпециальные требования:"
            for key, value in self.special_requirements.items():
                if value:
                    special_req_text += f"\n- {key}: {value}"
            enhanced_job_description += special_req_text
        
        system_prompt = build_interview_system_prompt(
            job_description=enhanced_job_description,
            position=position,
            company=company,
            competencies=competencies,
            candidate_resume=candidate_resume,
            language="ru",
            max_questions=max_questions,
            end_marker="__END_INTERVIEW__",
            include_end_marker_instruction=True
        )
        
        # Инициализируем Screen Analysis Tool для Vision анализа
        try:
            from .screen_analysis_tool import create_screen_analysis_tool
            self.screen_tool = create_screen_analysis_tool(self.vision_model)
            if self.vision_model:
                logger.info(f"Screen Analysis Tool инициализирован с Vision моделью")
            else:
                logger.info("Screen Analysis Tool инициализирован без Vision модели")
        except Exception as e:
            logger.error(f"Ошибка инициализации Screen Analysis Tool: {e}")
            self.screen_tool = None
        
        # Инициализируем Face Tracking для мониторинга поведения
        try:
            from .face_tracking import create_face_tracker
            face_tracking_config = self.db_config.get("face_tracking_config", {})
            self.face_tracker = create_face_tracker(face_tracking_config)
            logger.info("Face Tracker инициализирован для мониторинга поведения")
        except Exception as e:
            logger.error(f"Ошибка инициализации Face Tracker: {e}")
            self.face_tracker = None

        # Инициализируем базовый агент
        super().__init__(instructions=system_prompt)
        
        # Инициализируем чатбота для интервью с настраиваемой LLM моделью
        llm_model = None
        model_name = "ollama-3.1-8b-instant"  # Модель по умолчанию
        
        if self.custom_models and self.custom_models.get("llm"):
            # Используем настраиваемую LLM модель
            llm_model = self.custom_models["llm"]
            logger.info(f"Используется настраиваемая LLM модель: {self.models_config.get('llm_model', {}).get('name', 'Unknown')}")
        else:
            logger.info(f"Используется LLM модель по умолчанию: {model_name}")
        
        # Инициализируем Dynamic Model Switcher для умного переключения между моделями
        try:
            from .dynamic_model_switcher import create_dynamic_model_switcher, ModelMode
            
            # Создаем базовый текстовый чатбот
            text_chatbot = LangChainGroqChatbot(
                system_prompt=system_prompt,
                model=model_name if not llm_model else None,
                temperature=0.7,
                custom_llm=llm_model
            )
            
            # Создаем Vision чатбот если есть Vision модель
            vision_chatbot = None
            if self.vision_model:
                vision_chatbot = LangChainGroqChatbot(
                    system_prompt=system_prompt + "\n\nДоступен анализ экрана через Vision модель.",
                    model=model_name if not llm_model else None,
                    temperature=0.7,
                    custom_llm=llm_model,
                    screen_analysis_tool=self.screen_tool
                )
                logger.info("Vision чатбот создан для мультимодального режима")
            
            # Создаем Dynamic Model Switcher
            self.model_switcher = create_dynamic_model_switcher(
                text_llm=text_chatbot,
                vision_llm=vision_chatbot,
                screen_analysis_tool=self.screen_tool,
                mode=ModelMode.HYBRID  # Автоматическое переключение
            )
            
            # Основной чатбот теперь это switcher
            self.chatbot = self.model_switcher
            
            logger.info("Dynamic Model Switcher инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации Dynamic Model Switcher: {e}")
            # Fallback к обычному чатботу
            self.chatbot = LangChainGroqChatbot(
                system_prompt=system_prompt,
                model=model_name if not llm_model else None,
                temperature=0.7,
                custom_llm=llm_model,
                screen_analysis_tool=self.screen_tool
            )
            self.model_switcher = None
        
        # Включаем автоматическое завершение интервью
        if auto_save_results:
            os.makedirs(save_directory, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(save_directory, f"interview_{timestamp}.json")
            self.chatbot.enable_auto_finalize(
                end_marker="__END_INTERVIEW__",
                save_path=save_path
            )
        
        # Сохраняем параметры
        self.job_description = job_description
        self.position = position
        self.company = company
        self.competencies = competencies
        self.candidate_resume = candidate_resume
        self.max_questions = max_questions
        self.auto_save_results = auto_save_results
        self.save_directory = save_directory
        
        logger.info(f"Инициализирован InterviewAgent для позиции: {position} в {company}")
    
    def save_interview_results_to_db(self, interview_results: Dict[str, Any]) -> bool:
        """
        Сохранить результаты интервью в базу данных.
        
        Args:
            interview_results: Результаты интервью
            
        Returns:
            True если успешно сохранено
        """
        if not self.use_database or not self.applicant_id or not self.vacancy_id:
            logger.info("Database saving disabled or missing applicant/vacancy IDs")
            return False
            
        try:
            # Получаем данные face tracking
            face_tracking_data = self.get_face_tracking_stats()
            behavioral_insights = self.get_behavioral_insights()
            
            # Обогащаем результаты дополнительной информацией
            enhanced_results = {
                **interview_results,
                "applicant_id": self.applicant_id,
                "vacancy_id": self.vacancy_id,
                "applicant_name": self.applicant_name,
                "position": self.position,
                "company": self.company,
                "interview_date": datetime.now().isoformat(),
                "competencies_evaluated": self.competencies,
                "ai_hr_instructions_used": self.ai_hr_instructions,
                "experience_required": self.experience_required,
                "degree_required": self.degree_required,
                "special_requirements": self.special_requirements,
                
                # Face tracking и поведенческие данные
                "face_tracking_stats": face_tracking_data.get("stats") if face_tracking_data.get("available") else None,
                "behavioral_insights": behavioral_insights.get("insights") if behavioral_insights.get("available") else None,
                "engagement_summary": behavioral_insights.get("summary") if behavioral_insights.get("available") else None,
                "attention_metrics": {
                    "face_presence_ratio": face_tracking_data.get("stats", {}).get("face_presence_ratio"),
                    "attention_ratio": face_tracking_data.get("stats", {}).get("attention_ratio"),
                    "distraction_frequency": face_tracking_data.get("stats", {}).get("distraction_frequency"),
                    "overall_engagement": behavioral_insights.get("summary", {}).get("overall_engagement")
                } if face_tracking_data.get("available") else None
            }
            
            # Используем функцию из interview_configs для сохранения
            success = create_interview_summary_for_db(
                applicant_id=self.applicant_id,
                vacancy_id=self.vacancy_id,
                interview_results=enhanced_results,
                db_session=self.db_session
            )
            
            if success:
                logger.info(f"Interview results saved to database for applicant {self.applicant_id}, vacancy {self.vacancy_id}")
            else:
                logger.error("Failed to save interview results to database")
                
            return success
            
        except Exception as e:
            logger.error(f"Error saving interview results to database: {e}")
            return False
    
    async def on_enter(self):
        """Приветствие при входе в интервью"""
        greeting = await self._get_chatbot_response(
            "Начни интервью с короткого приветствия и уточни готовность кандидата."
        )
        await self.session.say(greeting)
    
    def on_screenshare_enabled(self, participant_id: str) -> None:
        """Обработчик включения демонстрации экрана."""
        logger.info(f"Участник {participant_id} включил демонстрацию экрана")
        
        # Активируем Screen Analysis Tool
        if hasattr(self, 'screen_tool') and self.screen_tool:
            self.screen_tool.set_screenshare_status(True)
            logger.info("Screen Analysis Tool активирован")
        
        # Переключаем модель на Vision режим
        if hasattr(self, 'model_switcher') and self.model_switcher:
            self.model_switcher.set_screenshare_status(True)
            logger.info("🔄 Модель переключена в мультимодальный режим")
            
            # Уведомляем пользователя о доступности анализа экрана
            asyncio.create_task(self._notify_vision_mode_enabled())
    
    def on_screenshare_disabled(self, participant_id: str) -> None:
        """Обработчик отключения демонстрации экрана."""
        logger.info(f"Участник {participant_id} отключил демонстрацию экрана")
        
        # Деактивируем Screen Analysis Tool
        if hasattr(self, 'screen_tool') and self.screen_tool:
            self.screen_tool.set_screenshare_status(False)
            logger.info("Screen Analysis Tool деактивирован")
        
        # Переключаем модель обратно на текстовый режим
        if hasattr(self, 'model_switcher') and self.model_switcher:
            self.model_switcher.set_screenshare_status(False)
            logger.info("🔄 Модель переключена обратно в текстовый режим")
            
            # Уведомляем пользователя об отключении анализа экрана
            asyncio.create_task(self._notify_vision_mode_disabled())
    
    def on_screenshare_frame(self, frame) -> None:
        """Обработчик нового кадра демонстрации экрана."""
        if hasattr(self, 'screen_tool') and self.screen_tool:
            self.screen_tool.update_frame(frame)
    
    async def _notify_vision_mode_enabled(self) -> None:
        """Уведомить пользователя о включении Vision режима."""
        try:
            message = (
                "👁️ Отлично! Теперь я могу видеть ваш экран и помогать с анализом "
                "кода, интерфейсов, документов и диагностикой ошибок. "
                "Просто спрашивайте о том, что показываете!"
            )
            await self.session.say(message)
        except Exception as e:
            logger.error(f"Error notifying vision mode enabled: {e}")
    
    async def _notify_vision_mode_disabled(self) -> None:
        """Уведомить пользователя об отключении Vision режима."""
        try:
            message = (
                "📺 Демонстрация экрана завершена. Продолжим обычное интервью. "
                "Если понадобится снова показать что-то на экране - включайте демонстрацию!"
            )
            await self.session.say(message)
        except Exception as e:
            logger.error(f"Error notifying vision mode disabled: {e}")
    
    def get_face_tracking_stats(self, start_time=None, end_time=None):
        """Получить статистику face tracking за период."""
        if not self.face_tracker:
            return {
                "available": False,
                "error": "Face tracking не инициализирован"
            }
        
        try:
            stats = self.face_tracker.get_attention_stats(start_time, end_time)
            current_status = self.face_tracker.get_current_status()
            
            return {
                "available": True,
                "stats": {
                    "total_duration": stats.total_duration,
                    "face_presence_ratio": stats.face_presence_ratio,
                    "attention_ratio": stats.attention_ratio,
                    "distraction_frequency": stats.distraction_frequency,
                    "blink_count": stats.blink_count,
                    "distraction_events": len(stats.distraction_events)
                },
                "current_status": current_status,
                "detailed_events": stats.distraction_events
            }
        except Exception as e:
            logger.error(f"Ошибка получения face tracking статистики: {e}")
            return {
                "available": False,
                "error": str(e)
            }
    
    def reset_face_tracking_stats(self):
        """Сброс статистики face tracking."""
        if self.face_tracker:
            self.face_tracker.reset_stats()
            logger.info("Face tracking статистика сброшена")
            return True
        return False
    
    def process_video_stream(self, track):
        """Обработка видео потока с face tracking."""
        try:
            if self.face_tracker:
                # Создаем video track с face tracking
                from .face_tracking import create_face_tracking_video_track
                face_tracking_track = create_face_tracking_video_track(track, self.face_tracker)
                
                # Добавляем в meeting
                if hasattr(self, 'session') and hasattr(self.session, 'meeting'):
                    self.session.meeting.add_custom_video_track(track=face_tracking_track)
                    logger.info("Face tracking video track добавлен")
                else:
                    logger.warning("Не удалось добавить face tracking video track")
            else:
                logger.info("Face tracking недоступен, используем обычный video track")
        except Exception as e:
            logger.error(f"Ошибка обработки video stream с face tracking: {e}")
    
    def get_behavioral_insights(self):
        """Получить поведенческие инсайты на основе face tracking."""
        if not self.face_tracker:
            return {"available": False, "message": "Face tracking недоступен"}
        
        try:
            stats = self.face_tracker.get_attention_stats()
            current_status = self.face_tracker.get_current_status()
            
            insights = []
            
            # Анализ присутствия в кадре
            if stats.face_presence_ratio < 0.8:
                insights.append({
                    "type": "presence",
                    "level": "warning",
                    "message": f"Кандидат был вне кадра {(1-stats.face_presence_ratio)*100:.1f}% времени",
                    "recommendation": "Убедитесь в стабильности видеосвязи и правильном позиционировании камеры"
                })
            
            # Анализ внимательности
            if stats.attention_ratio < 0.7:
                insights.append({
                    "type": "attention",
                    "level": "warning",
                    "message": f"Уровень внимательности: {stats.attention_ratio*100:.1f}%",
                    "recommendation": "Кандидат часто отвлекался или смотрел в сторону"
                })
            elif stats.attention_ratio > 0.9:
                insights.append({
                    "type": "attention",
                    "level": "positive",
                    "message": f"Высокий уровень внимательности: {stats.attention_ratio*100:.1f}%",
                    "recommendation": "Кандидат демонстрировал отличную концентрацию"
                })
            
            # Анализ частоты отвлечений
            if stats.distraction_frequency > 2:
                insights.append({
                    "type": "distraction",
                    "level": "warning",
                    "message": f"Частые отвлечения: {stats.distraction_frequency:.1f} раз в минуту",
                    "recommendation": "Высокая частота отвлечений может указывать на нервозность или невнимательность"
                })
            
            # Анализ моргания (может указывать на стресс)
            if stats.total_duration > 0:
                blinks_per_minute = (stats.blink_count / stats.total_duration) * 60
                if blinks_per_minute > 30:
                    insights.append({
                        "type": "stress",
                        "level": "info",
                        "message": f"Повышенная частота моргания: {blinks_per_minute:.1f} раз в минуту",
                        "recommendation": "Может указывать на волнение или стресс"
                    })
            
            return {
                "available": True,
                "insights": insights,
                "summary": {
                    "overall_engagement": "high" if stats.attention_ratio > 0.8 else "medium" if stats.attention_ratio > 0.6 else "low",
                    "presence_quality": "good" if stats.face_presence_ratio > 0.9 else "acceptable" if stats.face_presence_ratio > 0.7 else "poor",
                    "distraction_level": "low" if stats.distraction_frequency < 1 else "medium" if stats.distraction_frequency < 3 else "high"
                }
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа поведенческих инсайтов: {e}")
            return {"available": False, "error": str(e)}
    
    async def on_exit(self):
        """Завершение интервью"""
        if not self.chatbot.is_finished():
            # Если интервью не завершилось автоматически, генерируем финальную обратную связь
            try:
                feedback = self.chatbot.end_interview()
                farewell = "Спасибо за интервью! Мы свяжемся с вами в ближайшее время."
                await self.session.say(farewell)
                logger.info(f"Интервью завершено. Вердикт: {feedback.get('verdict', 'unknown')}")
                
                # Сохраняем результаты в БД
                if feedback:
                    self.save_interview_results_to_db(feedback)
                    
            except Exception as e:
                logger.error(f"Ошибка при завершении интервью: {e}")
                await self.session.say("Спасибо за интервью!")
        else:
            # Если интервью уже завершилось, также пытаемся сохранить результаты
            feedback = self.chatbot.get_final_feedback()
            if feedback:
                self.save_interview_results_to_db(feedback)
            await self.session.say("Спасибо за интервью! Удачи!")
    
    async def _get_chatbot_response(self, message: str) -> str:
        """Получить ответ от чатбота с поддержкой Dynamic Model Switcher"""
        try:
            # Проверяем, используется ли Dynamic Model Switcher
            if hasattr(self, 'model_switcher') and self.model_switcher:
                # Используем switcher для обработки сообщения
                response = await self.model_switcher.process_message(message)
                
                # Получаем текущую модель для проверки завершения интервью
                current_model = self.model_switcher.get_current_model()
                
                # Проверяем, не закончилось ли интервью
                if hasattr(current_model, 'is_finished') and current_model.is_finished():
                    # Генерируем финальную обратную связь
                    if hasattr(current_model, 'get_final_feedback'):
                        feedback = current_model.get_final_feedback()
                        if feedback:
                            logger.info(f"Интервью автоматически завершено. Вердикт: {feedback.get('verdict', 'unknown')}")
                            # Сохраняем результаты в базу данных
                            self.save_interview_results_to_db(feedback)
                
            else:
                # Fallback к обычному чатботу
                response = self.chatbot.ask(message)
                
                # Проверяем, завершилось ли интервью
                if hasattr(self.chatbot, 'is_finished') and self.chatbot.is_finished():
                    feedback = self.chatbot.get_final_feedback()
                    if feedback:
                        logger.info(f"Интервью автоматически завершено. Вердикт: {feedback.get('verdict', 'unknown')}")
                        # Сохраняем результаты в БД при автоматическом завершении
                        self.save_interview_results_to_db(feedback)
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка при получении ответа от чатбота: {e}")
            return "Извините, произошла техническая ошибка. Можете повторить вопрос?"
    
    def get_interview_status(self) -> dict:
        """Получить текущий статус интервью с информацией о Dynamic Model Switcher"""
        base_status = {
            "position": self.position,
            "company": self.company,
            "applicant_name": getattr(self, 'applicant_name', 'Unknown')
        }
        
        # Проверяем, используется ли Dynamic Model Switcher
        if hasattr(self, 'model_switcher') and self.model_switcher:
            current_model = self.model_switcher.get_current_model()
            
            base_status.update({
                "is_finished": current_model.is_finished() if hasattr(current_model, 'is_finished') else False,
                "messages_count": len(current_model.get_history()) if hasattr(current_model, 'get_history') else 0,
                "final_feedback": current_model.get_final_feedback() if hasattr(current_model, 'get_final_feedback') else None,
                "model_switcher_stats": self.model_switcher.get_statistics(),
                "current_mode": "vision" if self.model_switcher.is_vision_mode() else "text",
                "screenshare_active": self.model_switcher.is_screenshare_active,
                "vision_available": self.model_switcher.vision_llm is not None
            })
        else:
            # Fallback к обычному чатботу
            base_status.update({
                "is_finished": self.chatbot.is_finished() if hasattr(self.chatbot, 'is_finished') else False,
                "messages_count": len(self.chatbot.get_history()) if hasattr(self.chatbot, 'get_history') else 0,
                "final_feedback": self.chatbot.get_final_feedback() if hasattr(self.chatbot, 'get_final_feedback') else None,
                "model_switcher_stats": None,
                "current_mode": "text",
                "screenshare_active": False,
                "vision_available": False
            })
        
        # Добавляем данные face tracking
        if hasattr(self, 'face_tracker') and self.face_tracker:
            face_tracking_status = self.get_face_tracking_stats()
            base_status.update({
                "face_tracking": face_tracking_status,
                "behavioral_insights": self.get_behavioral_insights()
            })
        else:
            base_status.update({
                "face_tracking": {"available": False, "message": "Face tracking не инициализирован"},
                "behavioral_insights": {"available": False, "message": "Face tracking недоступен"}
            })
        
        return base_status

class InterviewChatbotLLM(LLM):
    """
    Кастомный LLM компонент, который использует LangChainGroqChatbot для интервью
    """
    def __init__(self, chatbot: LangChainGroqChatbot):
        super().__init__()
        self.chatbot = chatbot
        self._cancelled = False
    
    async def chat(
        self,
        messages: ChatContext,
        tools: Optional[List] = None,
        **kwargs
    ) -> AsyncIterator[LLMResponse]:
        """
        Обрабатывает сообщения через интервью чатбота
        """
        self._cancelled = False
        
        # Получаем последнее сообщение пользователя
        user_messages = [msg for msg in messages.items if isinstance(msg, ChatMessage) and msg.role == ChatRole.USER]
        if not user_messages:
            return
        
        last_message = user_messages[-1].content
        if isinstance(last_message, list):
            # Если контент - список, извлекаем текстовую часть
            text_content = ""
            for part in last_message:
                if isinstance(part, str):
                    text_content += part
                elif hasattr(part, 'text'):
                    text_content += part.text
            last_message = text_content
        
        try:
            # Используем стриминг для более естественного диалога
            response_text = ""
            for token in self.chatbot.ask_stream(last_message):
                if self._cancelled:
                    break
                if token:
                    response_text += token
                    yield LLMResponse(
                        content=token,
                        role=ChatRole.ASSISTANT,
                        metadata={"provider": "interview_chatbot"}
                    )
            
            # Проверяем, завершилось ли интервью
            if self.chatbot.is_finished():
                feedback = self.chatbot.get_final_feedback()
                if feedback:
                    logger.info(f"Интервью завершено автоматически. Вердикт: {feedback.get('verdict', 'unknown')}")
                    # Сохраняем результаты в БД при автоматическом завершении
                    self.save_interview_results_to_db(feedback)
        
        except Exception as e:
            logger.error(f"Ошибка в InterviewChatbotLLM: {e}")
            yield LLMResponse(
                content="Извините, произошла техническая ошибка. Можете повторить?",
                role=ChatRole.ASSISTANT,
                metadata={"provider": "interview_chatbot", "error": str(e)}
            )
    
    async def cancel_current_generation(self):
        """Отменить текущую генерацию"""
        self._cancelled = True
    
    async def aclose(self):
        """Очистка ресурсов"""
        await self.cancel_current_generation()

def create_interview_agent_from_metadata(room_metadata: dict) -> InterviewAgent:
    """
    Создает InterviewAgent на основе метаданных комнаты.
    
    Args:
        room_metadata: Метаданные комнаты VideoSDK
        
    Returns:
        Настроенный InterviewAgent
        
    Raises:
        ValueError: Если отсутствуют обязательные параметры
        RuntimeError: Если не удалось загрузить конфигурацию
    """
    # Получаем обязательные параметры
    applicant_id = room_metadata.get('applicant_id')
    vacancy_id = room_metadata.get('vacancy_id')
    
    if not applicant_id or not vacancy_id:
        raise ValueError(f"Отсутствуют обязательные параметры в metadata: applicant_id={applicant_id}, vacancy_id={vacancy_id}")
    
    # Конвертируем в int
    try:
        applicant_id = int(applicant_id)
        vacancy_id = int(vacancy_id)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Неверный формат ID: applicant_id={applicant_id}, vacancy_id={vacancy_id}") from e
    
    # Получаем дополнительные параметры из metadata
    max_questions = int(room_metadata.get('max_questions', 12))
    
    logger.info(f"Создание InterviewAgent для applicant_id={applicant_id}, vacancy_id={vacancy_id}")
    
    return InterviewAgent(
        applicant_id=applicant_id,
        vacancy_id=vacancy_id,
        max_questions=max_questions,
        auto_save_results=True,
        save_directory='./interview_results'
    )


class MyVoiceAgent(Agent):
    def __init__(self):
        super().__init__(instructions="Ты - полезный ассистент.")
    async def on_enter(self): await self.session.say("Привет! Как могу помочь?")
    async def on_exit(self): await self.session.say("Пока!")

async def start_session(context: JobContext):
    """
    Запускает сессию интервью на основе метаданных комнаты.
    Все данные автоматически загружаются из базы данных.
    """
    logger.info("Запуск сессии видеособеседования")
    
    try:
        # Создаем агента на основе метаданных комнаты
        agent = create_interview_agent_from_metadata(context.room.metadata)
        logger.info(f"Интервью-агент успешно создан для кандидата {agent.applicant_name}")
        
    except (ValueError, RuntimeError) as e:
        logger.error(f"Ошибка создания интервью-агента: {e}")
        # В случае критической ошибки, можно создать fallback агента
        logger.info("Создание fallback агента...")
        agent = MyVoiceAgent()
        logger.warning("Используется базовый агент вместо интервью-агента")
    
    conversation_flow = ConversationFlow(agent)

    # Создаем STT и TTS компоненты на основе конфигурации агента
    stt_component = None
    tts_component = None
    
    if hasattr(agent, 'custom_models') and agent.custom_models:
        # Используем настраиваемые модели из конфигурации
        logger.info("Используются настраиваемые AI модели из конфигурации")
        
        # STT модель
        if agent.custom_models.get("stt"):
            stt_component = agent.custom_models["stt"]
            logger.info(f"Используется настраиваемая STT модель: {agent.models_config.get('stt_model', {}).get('name', 'Unknown')}")
        
        # TTS модель  
        if agent.custom_models.get("tts"):
            tts_component = agent.custom_models["tts"]
            logger.info(f"Используется настраиваемая TTS модель: {agent.models_config.get('tts_model', {}).get('name', 'Unknown')}")
    
    # Fallback на модели по умолчанию, если настраиваемые недоступны
    if not stt_component:
        logger.info("Используются STT модели по умолчанию")
        use_cartesia_stt = os.getenv('USE_CARTESIA_STT', 'true').lower() == 'true'
    
    if use_cartesia_stt:
        # Используем безопасную обертку Cartesia STT
        try:
            stt_component = SafeCartesiaSTTWrapper(
                model=os.getenv('CARTESIA_STT_MODEL', 'ink-whisper'),
                language=os.getenv('CARTESIA_STT_LANGUAGE', 'ru')
            )
            logger.info("Используется безопасная Cartesia STT")
        except Exception as e:
            logger.error(f"Ошибка инициализации Cartesia STT: {e}")
            logger.info("Переключаемся на Groq STT")
            stt_component = GroqSTT(
                model="whisper-large-v3-turbo",
                silence_threshold=0.05,
                silence_duration=1.2,
            )
    else:
        # Используем Groq STT
        stt_component = GroqSTT(
            model="whisper-large-v3-turbo",
            silence_threshold=0.05,
            silence_duration=1.2,
        )
        logger.info("Используется Groq STT")

    # Создаем TTS компонент (если не создан из настраиваемых моделей)
    if not tts_component:
        logger.info("Используются TTS модели по умолчанию")
        use_cartesia_tts = os.getenv('USE_CARTESIA_TTS', 'true').lower() == 'true'
    
    if use_cartesia_tts:
        # Используем безопасную обертку Cartesia TTS
        try:
            tts_component = SafeCartesiaTTSWrapper(
                model=os.getenv('CARTESIA_MODEL', 'sonic-2'),
                voice_id="2b3bb17d-26b9-421f-b8ca-1dd92332279f",  # Multilingual female voice
                language=os.getenv('CARTESIA_LANGUAGE', 'ru')
            )
            logger.info("Используется безопасная Cartesia TTS")
        except Exception as e:
            logger.error(f"Ошибка инициализации Cartesia TTS: {e}")
            logger.info("Переключаемся на Groq TTS")
            tts_component = GroqTTSFixed(model="playai-tts")
    else:
        # Используем Groq TTS
        tts_component = GroqTTSFixed(model="playai-tts")
        logger.info("Используется Groq TTS")

    # Создаем LLM компонент в зависимости от режима
    if use_interview_mode and isinstance(agent, InterviewAgent):
        # В режиме интервью используем наш кастомный LLM с чатботом
        llm_component = InterviewChatbotLLM(agent.chatbot)
        logger.info("Используется InterviewChatbotLLM для интервью")
    else:
        # В обычном режиме используем стандартный GroqLLM
        llm_component = GroqLLM(model="ollama-3.1-8b-instant")
        logger.info("Используется стандартный GroqLLM")

    # Получаем Avatar компонент из agent если доступен
    avatar_component = None
    if hasattr(agent, 'avatar') and agent.avatar:
        avatar_component = agent.avatar
        logger.info("Используется кастомный Avatar из конфигурации")
    
    # Create pipeline с настройками для хорошего перебивания
    pipeline_kwargs = {
        "stt": stt_component,
        "llm": llm_component,
        "tts": tts_component,
        "vad": SileroVAD(
            threshold=0.3,  # Более чувствительный VAD для лучшего обнаружения речи
            min_speech_duration=0.3,  # Более быстрая реакция на речь
            min_silence_duration=0.8,  # Меньше ждем тишины для обработки
        ),
        "turn_detector": TurnDetector(
            threshold=0.5,  # Более чувствительный детектор поворотов для лучшего перебивания
        )
    }
    
    # Добавляем Avatar если доступен
    if avatar_component:
        pipeline_kwargs["avatar"] = avatar_component
        logger.info("Avatar добавлен в пайплайн")
    
    pipeline = CascadingPipeline(**pipeline_kwargs)

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
        room_id="pmfi-h2m4-1790",
     #  room_id="YOUR_MEETING_ID",  # Set to join a pre-created room; omit to auto-create
        name="VideoSDK Cascaded Agent",
        playground=True
    )

    return JobContext(room_options=room_options)

if __name__ == "__main__":
    job = WorkerJob(entrypoint=start_session, jobctx=make_context)
    job.start()