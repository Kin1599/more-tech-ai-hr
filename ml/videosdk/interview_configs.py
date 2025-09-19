"""
Конфигурации для различных типов интервью.
Поддерживает как статические конфигурации, так и динамическое получение из базы данных.
"""

from typing import Optional, Dict, Any
import logging
from .db_service import create_interview_config_from_db, InterviewDatabaseService

logger = logging.getLogger(__name__)

# Конфигурации для различных позиций
INTERVIEW_CONFIGS = {
    "python_developer": {
        "position": "Python Developer",
        "company": "TechCompany",
        "competencies": [
            "Python и его экосистема",
            "Веб-фреймворки (Django/FastAPI/Flask)",
            "Базы данных и ORM",
            "API разработка",
            "Тестирование",
            "Git и командная работа",
            "Архитектурное мышление"
        ],
        "job_description": """
        Мы ищем опытного Python разработчика для работы над веб-приложениями и API.
        
        Основные задачи:
        - Разработка веб-приложений на Django/FastAPI
        - Проектирование и разработка REST API
        - Работа с базами данных (PostgreSQL, Redis)
        - Написание тестов и поддержка CI/CD
        - Код-ревью и менторство
        
        Технологии: Python 3.8+, Django/FastAPI, PostgreSQL, Redis, Docker, Git
        """
    },
    
    "frontend_developer": {
        "position": "Frontend Developer",
        "company": "TechCompany",
        "competencies": [
            "JavaScript/TypeScript",
            "React/Vue/Angular",
            "HTML/CSS и современные подходы",
            "Состояние приложения (Redux/Vuex)",
            "Сборщики и инструменты (Webpack/Vite)",
            "Тестирование фронтенда",
            "UX/UI понимание"
        ],
        "job_description": """
        Ищем талантливого Frontend разработчика для создания современных веб-интерфейсов.
        
        Основные задачи:
        - Разработка пользовательских интерфейсов на React/Vue
        - Интеграция с REST API и GraphQL
        - Оптимизация производительности приложений
        - Кроссбраузерная совместимость
        - Работа с дизайнерами над UX/UI
        
        Технологии: JavaScript/TypeScript, React/Vue, HTML5/CSS3, Webpack/Vite
        """
    },
    
    "fullstack_developer": {
        "position": "Fullstack Developer",
        "company": "TechCompany",
        "competencies": [
            "Backend разработка (Python/Node.js)",
            "Frontend разработка (React/Vue)",
            "Базы данных и архитектура",
            "DevOps и деплой",
            "API дизайн",
            "Безопасность",
            "Системное мышление"
        ],
        "job_description": """
        Требуется универсальный Fullstack разработчик для работы над полным циклом разработки.
        
        Основные задачи:
        - Разработка backend на Python/Node.js
        - Создание frontend интерфейсов
        - Проектирование архитектуры приложений
        - Настройка CI/CD пайплайнов
        - Работа с облачными сервисами
        
        Технологии: Python/Node.js, React/Vue, PostgreSQL, Docker, AWS/GCP
        """
    },
    
    "data_scientist": {
        "position": "Data Scientist",
        "company": "DataCompany",
        "competencies": [
            "Python для анализа данных",
            "Машинное обучение",
            "Статистика и математика",
            "Pandas/NumPy/Scikit-learn",
            "Визуализация данных",
            "SQL и работа с БД",
            "Бизнес-понимание"
        ],
        "job_description": """
        Ищем Data Scientist для работы с большими данными и ML моделями.
        
        Основные задачи:
        - Анализ данных и выявление инсайтов
        - Построение ML моделей
        - A/B тестирование
        - Создание дашбордов и отчетов
        - Работа с продуктовой командой
        
        Технологии: Python, Pandas, Scikit-learn, TensorFlow/PyTorch, SQL, Tableau
        """
    },
    
    "devops_engineer": {
        "position": "DevOps Engineer",
        "company": "TechCompany",
        "competencies": [
            "Контейнеризация (Docker/Kubernetes)",
            "Облачные платформы (AWS/GCP/Azure)",
            "CI/CD пайплайны",
            "Инфраструктура как код",
            "Мониторинг и логирование",
            "Скриптинг (Bash/Python)",
            "Безопасность инфраструктуры"
        ],
        "job_description": """
        Требуется DevOps инженер для автоматизации и управления инфраструктурой.
        
        Основные задачи:
        - Настройка CI/CD пайплайнов
        - Управление Kubernetes кластерами
        - Автоматизация развертывания
        - Мониторинг и алертинг
        - Обеспечение безопасности
        
        Технологии: Docker, Kubernetes, AWS/GCP, Jenkins/GitLab CI, Terraform, Prometheus
        """
    }
}

def get_interview_config(config_name: str) -> dict:
    """
    Получить конфигурацию интервью по названию
    
    Args:
        config_name: Название конфигурации
        
    Returns:
        Словарь с параметрами интервью
    """
    return INTERVIEW_CONFIGS.get(config_name, INTERVIEW_CONFIGS["python_developer"])


def get_interview_config_from_database(
    applicant_id: int, 
    vacancy_id: int, 
    db_session: Optional[Any] = None
) -> Optional[Dict[str, Any]]:
    """
    Получить конфигурацию интервью из базы данных.
    
    Args:
        applicant_id: ID кандидата
        vacancy_id: ID вакансии
        db_session: Опциональная сессия базы данных
        
    Returns:
        Конфигурация интервью из БД или None в случае ошибки
    """
    try:
        config = create_interview_config_from_db(applicant_id, vacancy_id, db_session)
        if config:
            logger.info(f"Successfully loaded interview config from DB for applicant {applicant_id}, vacancy {vacancy_id}")
            return config
        else:
            logger.warning(f"Could not load interview config from DB for applicant {applicant_id}, vacancy {vacancy_id}")
            return None
    except Exception as e:
        logger.error(f"Error loading interview config from database: {e}")
        return None


def get_interview_config_with_fallback(
    applicant_id: Optional[int] = None,
    vacancy_id: Optional[int] = None,
    config_name: str = "python_developer",
    db_session: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Получить конфигурацию интервью с fallback на статические конфигурации.
    
    Сначала пытается загрузить из БД, если не получается - использует статическую конфигурацию.
    
    Args:
        applicant_id: ID кандидата (для загрузки из БД)
        vacancy_id: ID вакансии (для загрузки из БД)
        config_name: Название статической конфигурации (fallback)
        db_session: Опциональная сессия базы данных
        
    Returns:
        Конфигурация интервью
    """
    # Пытаемся загрузить из БД, если есть необходимые параметры
    if applicant_id and vacancy_id:
        db_config = get_interview_config_from_database(applicant_id, vacancy_id, db_session)
        if db_config:
            return db_config
        else:
            logger.info(f"Falling back to static config '{config_name}' for applicant {applicant_id}, vacancy {vacancy_id}")
    
    # Fallback на статическую конфигурацию
    static_config = get_interview_config(config_name)
    
    # Добавляем дополнительные поля для совместимости с БД конфигурацией
    enhanced_config = static_config.copy()
    enhanced_config.update({
        "candidate_resume": None,
        "ai_hr_instructions": "",
        "experience_required": 0,
        "degree_required": False,
        "special_requirements": {},
        "applicant_name": "Кандидат",
        "applicant_id": applicant_id,
        "vacancy_id": vacancy_id,
        "source": "static_config"
    })
    
    return enhanced_config


def create_interview_summary_for_db(
    applicant_id: int,
    vacancy_id: int, 
    interview_results: Dict[str, Any],
    db_session: Optional[Any] = None
) -> bool:
    """
    Сохранить результаты интервью в базу данных.
    
    Args:
        applicant_id: ID кандидата
        vacancy_id: ID вакансии
        interview_results: Результаты интервью
        db_session: Опциональная сессия базы данных
        
    Returns:
        True если успешно сохранено, False в противном случае
    """
    try:
        # Здесь можно добавить логику сохранения результатов интервью в БД
        # Пока что просто логируем
        logger.info(f"Interview results for applicant {applicant_id}, vacancy {vacancy_id}: {interview_results}")
        
        # TODO: Реализовать сохранение в таблицу интервью
        # Например, создать запись в таблице interviews или обновить job_application
        
        return True
    except Exception as e:
        logger.error(f"Error saving interview results to database: {e}")
        return False


def list_available_configs() -> list:
    """
    Получить список доступных статических конфигураций
    
    Returns:
        Список названий конфигураций
    """
    return list(INTERVIEW_CONFIGS.keys())


def validate_interview_config(config: Dict[str, Any]) -> bool:
    """
    Проверить валидность конфигурации интервью.
    
    Args:
        config: Конфигурация для проверки
        
    Returns:
        True если конфигурация валидна
    """
    required_fields = ["position", "company", "job_description", "competencies"]
    
    for field in required_fields:
        if field not in config:
            logger.error(f"Missing required field in interview config: {field}")
            return False
    
    if not isinstance(config["competencies"], list):
        logger.error("Competencies must be a list")
        return False
    
    return True
