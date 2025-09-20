"""
Django модели для админ панели.
Неизменяемые модели для отображения данных из FastAPI.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(models.Model):
    """Пользователи системы."""
    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=254, unique=True)
    password_hash = models.CharField(max_length=128)
    role = models.CharField(max_length=20, choices=[
        ('hr', 'HR'),
        ('applicant', 'Кандидат')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.email} ({self.role})"


class HRProfile(models.Model):
    """Профили HR специалистов."""
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='hr_profile')
    name = models.CharField(max_length=100, blank=True, null=True)
    surname = models.CharField(max_length=100, blank=True, null=True)
    patronymic = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=200, blank=True, null=True)
    contacts = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'hr_profiles'
        verbose_name = 'HR Профиль'
        verbose_name_plural = 'HR Профили'

    def __str__(self):
        return f"{self.surname} {self.name}" if self.name else f"HR #{self.id}"


class ApplicantProfile(models.Model):
    """Профили кандидатов."""
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='applicant_profile')
    name = models.CharField(max_length=100, blank=True, null=True)
    surname = models.CharField(max_length=100, blank=True, null=True)
    patronymic = models.CharField(max_length=100, blank=True, null=True)
    contacts = models.TextField(blank=True, null=True)
    cv = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'applicant_profiles'
        verbose_name = 'Профиль кандидата'
        verbose_name_plural = 'Профили кандидатов'

    def __str__(self):
        return f"{self.surname} {self.name}" if self.name else f"Кандидат #{self.id}"


class Vacancy(models.Model):
    """Вакансии."""
    STATUS_CHOICES = [
        ('active', 'Активная'),
        ('closed', 'Закрыта'),
        ('stopped', 'Приостановлена')
    ]
    
    OFFER_TYPE_CHOICES = [
        ('TK', 'Трудовой контракт'),
        ('GPH', 'ГПХ'),
        ('IP', 'ИП')
    ]
    
    BUSY_TYPE_CHOICES = [
        ('allTime', 'Полная занятость'),
        ('projectTime', 'Проектная занятость')
    ]

    id = models.AutoField(primary_key=True)
    hr_profile = models.ForeignKey(HRProfile, on_delete=models.CASCADE, related_name='vacancies')
    name = models.CharField(max_length=200)
    department = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    date = models.DateTimeField(blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=300, blank=True, null=True)
    offer_type = models.CharField(max_length=10, choices=OFFER_TYPE_CHOICES, blank=True, null=True)
    busy_type = models.CharField(max_length=20, choices=BUSY_TYPE_CHOICES, blank=True, null=True)
    graph = models.CharField(max_length=100, blank=True, null=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    annual_bonus = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    bonus_type = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    prompt = models.TextField(blank=True, null=True, verbose_name="AI HR указания")
    exp = models.IntegerField(blank=True, null=True, verbose_name="Требуемый опыт (лет)")
    degree = models.BooleanField(default=False, verbose_name="Требуется высшее образование")
    special_software = models.CharField(max_length=500, blank=True, null=True)
    computer_skills = models.CharField(max_length=500, blank=True, null=True)
    foreign_languages = models.CharField(max_length=300, blank=True, null=True)
    language_level = models.CharField(max_length=100, blank=True, null=True)
    business_trips = models.BooleanField(default=False)

    class Meta:
        db_table = 'vacancies'
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Вакансии'

    def __str__(self):
        return f"{self.name} ({self.department})"


class JobApplication(models.Model):
    """Отклики на вакансии."""
    STATUS_CHOICES = [
        ('cvReview', 'Просмотр резюме'),
        ('interview', 'Интервью'),
        ('waitResult', 'Ожидание результата'),
        ('rejected', 'Отклонено'),
        ('approved', 'Одобрено')
    ]

    id = models.AutoField(primary_key=True)
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='job_applications')
    applicant_profile = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='job_applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='cvReview')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'job_applications'
        verbose_name = 'Отклик на вакансию'
        verbose_name_plural = 'Отклики на вакансии'

    def __str__(self):
        return f"{self.applicant_profile} -> {self.vacancy.name}"


class ApplicantResumeVersion(models.Model):
    """Версии резюме кандидатов."""
    id = models.AutoField(primary_key=True)
    applicant = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='resume_versions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'applicant_resume_versions'
        verbose_name = 'Версия резюме'
        verbose_name_plural = 'Версии резюме'

    def __str__(self):
        return f"Резюме {self.applicant} от {self.created_at.strftime('%d.%m.%Y')}"


class Meeting(models.Model):
    """Встречи/интервью."""
    STATUS_CHOICES = [
        ('cvReview', 'Просмотр резюме'),
        ('waitPickTime', 'Ожидание выбора времени'),
        ('waitMeeting', 'Ожидание встречи'),
        ('waitResult', 'Ожидание результата'),
        ('rejected', 'Отклонено'),
        ('approved', 'Одобрено')
    ]

    id = models.AutoField(primary_key=True)
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='meetings')
    applicant_profile = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='meetings')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='cvReview')
    room_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'meetings'
        verbose_name = 'Встреча'
        verbose_name_plural = 'Встречи'

    def __str__(self):
        return f"Встреча {self.applicant_profile} по вакансии {self.vacancy.name}"


class JobApplicationCVEvaluation(models.Model):
    """Оценки резюме."""
    id = models.AutoField(primary_key=True)
    job_application = models.OneToOneField(JobApplication, on_delete=models.CASCADE, related_name='cv_evaluation')
    name = models.CharField(max_length=200)
    score = models.IntegerField()
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)

    class Meta:
        db_table = 'job_application_cv_evaluations'
        verbose_name = 'Оценка резюме'
        verbose_name_plural = 'Оценки резюме'

    def __str__(self):
        return f"Оценка резюме {self.job_application} - {self.score}%"


# AI Models
class AIModelConfiguration(models.Model):
    """Конфигурации AI моделей."""
    MODEL_TYPE_CHOICES = [
        ('llm', 'LLM'),
        ('stt', 'STT'),
        ('tts', 'TTS'),
        ('avatar', 'Avatar'),
        ('vision', 'Vision')
    ]
    
    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('groq', 'Groq'),
        ('anthropic', 'Anthropic'),
        ('cartesia', 'Cartesia'),
        ('huggingface', 'HuggingFace'),
        ('replicate', 'Replicate'),
        ('cohere', 'Cohere'),
        ('local_oollama', 'Local Ollama'),
        ('local_whisper', 'Local Whisper'),
        ('local_coqui', 'Local Coqui'),
        ('local_bark', 'Local Bark'),
        ('local_vllm', 'Local vLLM'),
        ('local_ollamacpp', 'Local OllamaCPP'),
        ('local_transformers', 'Local Transformers'),
        ('local_onnx', 'Local ONNX'),
        ('local_tensorrt', 'Local TensorRT'),
        ('simli', 'Simli'),
        ('google_gemini', 'Google Gemini'),
        ('openai_vision', 'OpenAI Vision'),
        ('anthropic_vision', 'Anthropic Vision'),
        ('azure_vision', 'Azure Vision'),
        ('local_llava', 'Local LLaVA'),
        ('local_cogvlm', 'Local CogVLM'),
        ('local_blip2', 'Local BLIP2'),
        ('local_instructblip', 'Local InstructBLIP'),
        ('local_minigpt4', 'Local MiniGPT4'),
        ('local_qwen_vl', 'Local Qwen-VL'),
        ('local_internvl', 'Local InternVL'),
        ('local_moondream', 'Local MoonDream'),
        ('local_bakllava', 'Local BakLLaVA'),
        ('custom_endpoint', 'Custom Endpoint'),
        ('custom_local', 'Custom Local'),
        ('openai_compatible', 'OpenAI Compatible')
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    model_type = models.CharField(max_length=20, choices=MODEL_TYPE_CHOICES, verbose_name="Тип модели")
    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES, verbose_name="Провайдер")
    model_name = models.CharField(max_length=200, verbose_name="Название модели")
    endpoint_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL endpoint")
    api_key_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Название API ключа")
    model_path = models.CharField(max_length=500, blank=True, null=True, verbose_name="Путь к модели")
    engine_path = models.CharField(max_length=500, blank=True, null=True, verbose_name="Путь к engine")
    context_length = models.IntegerField(blank=True, null=True, verbose_name="Длина контекста")
    face_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID лица")
    max_session_length = models.IntegerField(blank=True, null=True, verbose_name="Макс. длительность сессии")
    max_idle_time = models.IntegerField(blank=True, null=True, verbose_name="Макс. время бездействия")
    temperature = models.FloatField(default=0.7, verbose_name="Температура")
    max_tokens = models.IntegerField(blank=True, null=True, verbose_name="Макс. токены")
    top_p = models.FloatField(blank=True, null=True, verbose_name="Top P")
    frequency_penalty = models.FloatField(blank=True, null=True, verbose_name="Frequency Penalty")
    presence_penalty = models.FloatField(blank=True, null=True, verbose_name="Presence Penalty")
    custom_parameters = models.JSONField(default=dict, blank=True, verbose_name="Кастомные параметры")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_model_configurations'
        verbose_name = 'Конфигурация AI модели'
        verbose_name_plural = 'Конфигурации AI моделей'

    def __str__(self):
        return f"{self.name} ({self.provider})"


class InterviewModelConfiguration(models.Model):
    """Конфигурации моделей для интервью."""
    id = models.AutoField(primary_key=True)
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='model_configurations')
    llm_model = models.ForeignKey(AIModelConfiguration, on_delete=models.CASCADE, related_name='llm_interviews', blank=True, null=True)
    stt_model = models.ForeignKey(AIModelConfiguration, on_delete=models.CASCADE, related_name='stt_interviews', blank=True, null=True)
    tts_model = models.ForeignKey(AIModelConfiguration, on_delete=models.CASCADE, related_name='tts_interviews', blank=True, null=True)
    avatar_model = models.ForeignKey(AIModelConfiguration, on_delete=models.CASCADE, related_name='avatar_interviews', blank=True, null=True)
    vision_model = models.ForeignKey(AIModelConfiguration, on_delete=models.CASCADE, related_name='vision_interviews', blank=True, null=True)
    max_questions = models.IntegerField(default=12, verbose_name="Макс. вопросов")
    vad_threshold = models.FloatField(default=0.5, verbose_name="VAD порог")
    vad_duration = models.FloatField(default=0.5, verbose_name="VAD длительность")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'interview_model_configurations'
        verbose_name = 'Конфигурация моделей интервью'
        verbose_name_plural = 'Конфигурации моделей интервью'

    def __str__(self):
        return f"Конфигурация для {self.vacancy.name}"


class ModelUsageLog(models.Model):
    """Логи использования моделей."""
    id = models.AutoField(primary_key=True)
    model_configuration = models.ForeignKey(AIModelConfiguration, on_delete=models.CASCADE, related_name='usage_logs')
    interview_configuration = models.ForeignKey(InterviewModelConfiguration, on_delete=models.CASCADE, related_name='usage_logs', blank=True, null=True)
    session_id = models.CharField(max_length=100, verbose_name="ID сессии")
    tokens_used = models.IntegerField(blank=True, null=True, verbose_name="Использовано токенов")
    duration_seconds = models.FloatField(blank=True, null=True, verbose_name="Длительность (сек)")
    cost_usd = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Стоимость (USD)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'model_usage_logs'
        verbose_name = 'Лог использования модели'
        verbose_name_plural = 'Логи использования моделей'

    def __str__(self):
        return f"Использование {self.model_configuration.name} в сессии {self.session_id}"
