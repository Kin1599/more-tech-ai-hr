"""
Сервис для работы с базой данных в контексте видеособеседований.
Предоставляет функции для получения данных о вакансиях, резюме кандидатов и заявках.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging

# Импортируем модели из основного приложения
try:
    from ...models.models import (
        Vacancy, 
        ApplicantProfile, 
        JobApplication, 
        HRProfile,
        User,
        ApplicantResumeVersion
    )
    from ...core.database import get_session
except ImportError as e:
    logging.warning(f"Cannot import database models: {e}")
    # Fallback для случаев когда модуль используется независимо
    Vacancy = None
    ApplicantProfile = None
    JobApplication = None
    HRProfile = None
    User = None
    ApplicantResumeVersion = None
    get_session = None

logger = logging.getLogger(__name__)


class InterviewDatabaseService:
    """Сервис для работы с базой данных в контексте интервью."""
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Инициализация сервиса.
        
        Args:
            db_session: Сессия базы данных. Если не передана, будет создана новая.
        """
        self.db_session = db_session
        self._external_session = db_session is not None
    
    def _get_session(self) -> Session:
        """Получить сессию базы данных."""
        if self.db_session:
            return self.db_session
        elif get_session:
            return next(get_session())
        else:
            raise RuntimeError("Database session not available")
    
    def get_vacancy_by_id(self, vacancy_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о вакансии по ID.
        
        Args:
            vacancy_id: ID вакансии
            
        Returns:
            Словарь с данными вакансии или None, если не найдена
        """
        if not Vacancy:
            logger.warning("Vacancy model not available")
            return None
            
        try:
            db = self._get_session()
            vacancy = db.query(Vacancy).filter_by(id=vacancy_id).first()
            
            if not vacancy:
                logger.warning(f"Vacancy with ID {vacancy_id} not found")
                return None
            
            # Получаем информацию о HR
            hr_info = None
            if vacancy.hr_profile:
                hr_info = {
                    "name": vacancy.hr_profile.name,
                    "surname": vacancy.hr_profile.surname,
                    "patronymic": vacancy.hr_profile.patronymic,
                    "department": vacancy.hr_profile.department,
                    "contacts": vacancy.hr_profile.contacts
                }
            
            return {
                "id": vacancy.id,
                "name": vacancy.name,
                "description": vacancy.description,
                "department": vacancy.department,
                "region": vacancy.region,
                "city": vacancy.city,
                "address": vacancy.address,
                "salary_min": float(vacancy.salaryMin) if vacancy.salaryMin else None,
                "salary_max": float(vacancy.salaryMax) if vacancy.salaryMax else None,
                "experience_years": vacancy.exp,
                "degree_required": vacancy.degree,
                "special_software": vacancy.specialSoftware,
                "computer_skills": vacancy.computerSkills,
                "foreign_languages": vacancy.foreignLanguages,
                "language_level": vacancy.languageLevel,
                "business_trips": vacancy.businessTrips,
                "offer_type": vacancy.offerType.value if hasattr(vacancy.offerType, 'value') else vacancy.offerType,
                "busy_type": vacancy.busyType.value if hasattr(vacancy.busyType, 'value') else vacancy.busyType,
                "graph": vacancy.graph,
                "annual_bonus": float(vacancy.annualBonus) if vacancy.annualBonus else None,
                "bonus_type": vacancy.bonusType,
                "prompt": vacancy.prompt,  # AI HR указания
                "hr_profile": hr_info,
                "status": vacancy.status.value if hasattr(vacancy.status, 'value') else vacancy.status,
                "created_date": vacancy.date
            }
            
        except Exception as e:
            logger.error(f"Error fetching vacancy {vacancy_id}: {e}")
            return None
    
    def get_applicant_by_id(self, applicant_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о кандидате по ID.
        
        Args:
            applicant_id: ID кандидата (ApplicantProfile)
            
        Returns:
            Словарь с данными кандидата или None, если не найден
        """
        if not ApplicantProfile:
            logger.warning("ApplicantProfile model not available")
            return None
            
        try:
            db = self._get_session()
            applicant = db.query(ApplicantProfile).filter_by(id=applicant_id).first()
            
            if not applicant:
                logger.warning(f"Applicant with ID {applicant_id} not found")
                return None
            
            # Получаем последнюю версию резюме
            latest_resume = None
            if applicant.resume_versions:
                latest_resume_version = (
                    db.query(ApplicantResumeVersion)
                    .filter_by(applicant_id=applicant_id)
                    .order_by(desc(ApplicantResumeVersion.created_at))
                    .first()
                )
                if latest_resume_version:
                    latest_resume = {
                        "storage_path": latest_resume_version.storage_path,
                        "text_hash": latest_resume_version.text_hash,
                        "is_current": latest_resume_version.is_current,
                        "created_at": latest_resume_version.created_at
                    }
            
            return {
                "id": applicant.id,
                "name": applicant.name,
                "surname": applicant.surname,
                "patronymic": applicant.patronymic,
                "full_name": " ".join(filter(None, [applicant.name, applicant.patronymic, applicant.surname])),
                "contacts": applicant.contacts,
                "cv_text": applicant.cv,  # Основное резюме в текстовом формате
                "summary": applicant.summary,
                "user_id": applicant.user_id,
                "latest_resume": latest_resume
            }
            
        except Exception as e:
            logger.error(f"Error fetching applicant {applicant_id}: {e}")
            return None
    
    def get_job_application(self, applicant_id: int, vacancy_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить заявку кандидата на вакансию.
        
        Args:
            applicant_id: ID кандидата
            vacancy_id: ID вакансии
            
        Returns:
            Словарь с данными заявки или None, если не найдена
        """
        if not JobApplication:
            logger.warning("JobApplication model not available")
            return None
            
        try:
            db = self._get_session()
            application = (
                db.query(JobApplication)
                .filter_by(applicant_id=applicant_id, vacancy_id=vacancy_id)
                .first()
            )
            
            if not application:
                logger.warning(f"Job application not found for applicant {applicant_id} and vacancy {vacancy_id}")
                return None
            
            return {
                "id": application.id,
                "applicant_id": application.applicant_id,
                "vacancy_id": application.vacancy_id,
                "resume_version_id": application.resume_version_id,
                "status": application.status.value if hasattr(application.status, 'value') else application.status,
                "contacts": application.contacts,
                "created_at": application.created_at,
                "updated_at": application.updated_at
            }
            
        except Exception as e:
            logger.error(f"Error fetching job application: {e}")
            return None
    
    def get_interview_context(self, applicant_id: int, vacancy_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить полный контекст для проведения интервью.
        
        Args:
            applicant_id: ID кандидата
            vacancy_id: ID вакансии
            
        Returns:
            Словарь с полным контекстом интервью или None
        """
        try:
            # Получаем данные о вакансии
            vacancy_data = self.get_vacancy_by_id(vacancy_id)
            if not vacancy_data:
                return None
            
            # Получаем данные о кандидате
            applicant_data = self.get_applicant_by_id(applicant_id)
            if not applicant_data:
                return None
            
            # Получаем заявку
            application_data = self.get_job_application(applicant_id, vacancy_id)
            
            # Формируем контекст интервью
            context = {
                "vacancy": vacancy_data,
                "applicant": applicant_data,
                "application": application_data,
                "interview_config": {
                    "position": vacancy_data["name"],
                    "company": vacancy_data.get("hr_profile", {}).get("department", "Компания"),
                    "job_description": vacancy_data["description"],
                    "competencies": self._extract_competencies_from_vacancy(vacancy_data),
                    "candidate_resume": applicant_data["cv_text"],
                    "ai_hr_instructions": vacancy_data.get("prompt", ""),
                    "experience_required": vacancy_data.get("experience_years", 0),
                    "degree_required": vacancy_data.get("degree_required", False),
                    "special_requirements": {
                        "special_software": vacancy_data.get("special_software"),
                        "computer_skills": vacancy_data.get("computer_skills"),
                        "foreign_languages": vacancy_data.get("foreign_languages"),
                        "language_level": vacancy_data.get("language_level"),
                        "business_trips": vacancy_data.get("business_trips", False)
                    }
                }
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error building interview context: {e}")
            return None
    
    def _extract_competencies_from_vacancy(self, vacancy_data: Dict[str, Any]) -> List[str]:
        """
        Извлечь ключевые компетенции из данных вакансии.
        
        Args:
            vacancy_data: Данные вакансии
            
        Returns:
            Список компетенций
        """
        competencies = []
        
        # Добавляем компетенции на основе специальных навыков
        if vacancy_data.get("special_software"):
            competencies.append(f"Специализированное ПО: {vacancy_data['special_software']}")
        
        if vacancy_data.get("computer_skills"):
            competencies.append(f"Компьютерные навыки: {vacancy_data['computer_skills']}")
        
        if vacancy_data.get("foreign_languages"):
            lang_level = vacancy_data.get("language_level", "")
            competencies.append(f"Иностранные языки: {vacancy_data['foreign_languages']} ({lang_level})")
        
        # Добавляем общие компетенции на основе описания
        description = vacancy_data.get("description", "").lower()
        
        # Технические компетенции (можно расширить)
        tech_keywords = {
            "python": "Программирование на Python",
            "javascript": "Программирование на JavaScript", 
            "react": "React разработка",
            "django": "Django фреймворк",
            "fastapi": "FastAPI фреймворк",
            "postgresql": "Работа с PostgreSQL",
            "docker": "Контейнеризация (Docker)",
            "git": "Система контроля версий Git",
            "api": "Разработка API",
            "sql": "Работа с SQL",
            "машинное обучение": "Машинное обучение",
            "data science": "Анализ данных",
            "devops": "DevOps практики",
            "kubernetes": "Оркестрация контейнеров (Kubernetes)"
        }
        
        for keyword, competency in tech_keywords.items():
            if keyword in description:
                competencies.append(competency)
        
        # Если компетенций мало, добавляем общие
        if len(competencies) < 3:
            competencies.extend([
                "Аналитическое мышление",
                "Командная работа", 
                "Решение проблем",
                "Коммуникативные навыки"
            ])
        
        return competencies[:7]  # Ограничиваем до 7 компетенций
    
    def close(self):
        """Закрыть сессию базы данных, если она была создана внутри сервиса."""
        if self.db_session and not self._external_session:
            self.db_session.close()


def get_interview_context_from_db(
    applicant_id: int, 
    vacancy_id: int, 
    db_session: Optional[Session] = None
) -> Optional[Dict[str, Any]]:
    """
    Удобная функция для получения контекста интервью из базы данных.
    
    Args:
        applicant_id: ID кандидата
        vacancy_id: ID вакансии
        db_session: Опциональная сессия БД
        
    Returns:
        Контекст интервью или None
    """
    service = InterviewDatabaseService(db_session)
    try:
        return service.get_interview_context(applicant_id, vacancy_id)
    finally:
        service.close()


def get_interview_models_config_from_db(
    vacancy_id: int, 
    db_session: Optional[Session] = None
) -> Optional[Dict[str, Any]]:
    """
    Удобная функция для получения конфигурации AI моделей из базы данных.
    
    Args:
        vacancy_id: ID вакансии
        db_session: Опциональная сессия БД
        
    Returns:
        Конфигурация AI моделей или None
    """
    try:
        # Используем модельный сервис для получения конфигурации
        from .model_service import ModelConfigurationService
        
        model_service = ModelConfigurationService(db_session)
        try:
            config = model_service.get_interview_models_config(vacancy_id)
            
            if config:
                logger.info(f"Loaded AI models configuration for vacancy {vacancy_id}")
                return config
            else:
                logger.warning(f"No AI models configuration found for vacancy {vacancy_id}, using defaults")
                return model_service._get_default_models_config()
                
        finally:
            model_service.close()
            
    except Exception as e:
        logger.error(f"Error loading AI models configuration for vacancy {vacancy_id}: {e}")
        return None


def create_interview_config_from_db(
    applicant_id: int,
    vacancy_id: int,
    db_session: Optional[Session] = None
) -> Optional[Dict[str, Any]]:
    """
    Создать конфигурацию интервью на основе данных из БД.
    
    Args:
        applicant_id: ID кандидата
        vacancy_id: ID вакансии
        db_session: Опциональная сессия БД
        
    Returns:
        Конфигурация интервью в формате, совместимом с InterviewAgent
    """
    context = get_interview_context_from_db(applicant_id, vacancy_id, db_session)
    
    if not context:
        return None
    
    interview_config = context["interview_config"]
    
    return {
        "job_description": interview_config["job_description"] or "Описание вакансии не указано",
        "position": interview_config["position"] or "Не указано",
        "company": interview_config["company"] or "Компания",
        "competencies": interview_config["competencies"],
        "candidate_resume": interview_config["candidate_resume"],
        "ai_hr_instructions": interview_config["ai_hr_instructions"],
        "experience_required": interview_config["experience_required"],
        "degree_required": interview_config["degree_required"],
        "special_requirements": interview_config["special_requirements"],
        "applicant_name": context["applicant"]["full_name"],
        "applicant_id": applicant_id,
        "vacancy_id": vacancy_id
    }
