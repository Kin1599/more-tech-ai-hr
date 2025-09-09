"""
Конфигурации для различных типов интервью
"""

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

def list_available_configs() -> list:
    """
    Получить список доступных конфигураций
    
    Returns:
        Список названий конфигураций
    """
    return list(INTERVIEW_CONFIGS.keys())
