"""
Django Admin конфигурация с темой Unfold.
Неизменяемые модели для просмотра данных из FastAPI.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    User, HRProfile, ApplicantProfile, Vacancy, JobApplication,
    ApplicantResumeVersion, Meeting, JobApplicationCVEvaluation,
    AIModelConfiguration, InterviewModelConfiguration, ModelUsageLog
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Админ для пользователей."""
    list_display = ['id', 'email', 'role', 'created_at', 'has_hr_profile', 'has_applicant_profile']
    list_filter = ['role', 'created_at']
    search_fields = ['email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def has_hr_profile(self, obj):
        """Проверка наличия HR профиля."""
        return bool(obj.hr_profile)
    has_hr_profile.boolean = True
    has_hr_profile.short_description = 'HR профиль'

    def has_applicant_profile(self, obj):
        """Проверка наличия профиля кандидата."""
        return bool(obj.applicant_profile)
    has_applicant_profile.boolean = True
    has_applicant_profile.short_description = 'Профиль кандидата'

    def has_add_permission(self, request):
        """Запрет на добавление."""
        return False

    def has_change_permission(self, request, obj=None):
        """Запрет на изменение."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Запрет на удаление."""
        return False


@admin.register(HRProfile)
class HRProfileAdmin(admin.ModelAdmin):
    """Админ для HR профилей."""
    list_display = ['id', 'user_email', 'full_name', 'department', 'vacancies_count']
    list_filter = ['department']
    search_fields = ['name', 'surname', 'user__email']
    readonly_fields = ['id']
    raw_id_fields = ['user']

    def user_email(self, obj):
        """Email пользователя."""
        return obj.user.email
    user_email.short_description = 'Email'

    def full_name(self, obj):
        """Полное имя."""
        parts = [obj.surname, obj.name, obj.patronymic]
        return ' '.join(filter(None, parts)) or 'Не указано'
    full_name.short_description = 'ФИО'

    def vacancies_count(self, obj):
        """Количество вакансий."""
        count = obj.vacancies.count()
        if count > 0:
            url = reverse('admin:hr_admin_vacancy_changelist') + f'?hr_profile__id__exact={obj.id}'
            return format_html('<a href="{}">{} вакансий</a>', url, count)
        return '0 вакансий'
    vacancies_count.short_description = 'Вакансии'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ApplicantProfile)
class ApplicantProfileAdmin(admin.ModelAdmin):
    """Админ для профилей кандидатов."""
    list_display = ['id', 'user_email', 'full_name', 'applications_count', 'resume_versions_count']
    search_fields = ['name', 'surname', 'user__email']
    readonly_fields = ['id', 'cv_preview']
    raw_id_fields = ['user']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    def full_name(self, obj):
        parts = [obj.surname, obj.name, obj.patronymic]
        return ' '.join(filter(None, parts)) or 'Не указано'
    full_name.short_description = 'ФИО'

    def applications_count(self, obj):
        count = obj.job_applications.count()
        if count > 0:
            url = reverse('admin:hr_admin_jobapplication_changelist') + f'?applicant_profile__id__exact={obj.id}'
            return format_html('<a href="{}">{} откликов</a>', url, count)
        return '0 откликов'
    applications_count.short_description = 'Отклики'

    def resume_versions_count(self, obj):
        count = obj.resume_versions.count()
        if count > 0:
            url = reverse('admin:hr_admin_applicantresumeversion_changelist') + f'?applicant__id__exact={obj.id}'
            return format_html('<a href="{}">{} версий</a>', url, count)
        return '0 версий'
    resume_versions_count.short_description = 'Версии резюме'

    def cv_preview(self, obj):
        """Превью резюме."""
        if obj.cv:
            preview = obj.cv[:200] + '...' if len(obj.cv) > 200 else obj.cv
            return format_html('<div style="max-height: 200px; overflow-y: auto; border: 1px solid #ddd; padding: 10px;">{}</div>', preview)
        return 'Резюме не загружено'
    cv_preview.short_description = 'Превью резюме'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    """Админ для вакансий."""
    list_display = ['id', 'name', 'hr_profile', 'department', 'status', 'salary_range', 'applications_count', 'created_date']
    list_filter = ['status', 'department', 'offer_type', 'busy_type', 'degree', 'business_trips']
    search_fields = ['name', 'department', 'description']
    readonly_fields = ['id', 'description_preview', 'prompt_preview']
    raw_id_fields = ['hr_profile']

    def salary_range(self, obj):
        """Диапазон зарплаты."""
        if obj.salary_min and obj.salary_max:
            return f"{obj.salary_min:,.0f} - {obj.salary_max:,.0f} ₽"
        elif obj.salary_min:
            return f"от {obj.salary_min:,.0f} ₽"
        elif obj.salary_max:
            return f"до {obj.salary_max:,.0f} ₽"
        return 'Не указано'
    salary_range.short_description = 'Зарплата'

    def applications_count(self, obj):
        count = obj.job_applications.count()
        if count > 0:
            url = reverse('admin:hr_admin_jobapplication_changelist') + f'?vacancy__id__exact={obj.id}'
            return format_html('<a href="{}">{} откликов</a>', url, count)
        return '0 откликов'
    applications_count.short_description = 'Отклики'

    def created_date(self, obj):
        return obj.date.strftime('%d.%m.%Y') if obj.date else 'Не указана'
    created_date.short_description = 'Дата создания'

    def description_preview(self, obj):
        """Превью описания."""
        if obj.description:
            preview = obj.description[:300] + '...' if len(obj.description) > 300 else obj.description
            return format_html('<div style="max-height: 200px; overflow-y: auto; border: 1px solid #ddd; padding: 10px;">{}</div>', preview)
        return 'Описание не указано'
    description_preview.short_description = 'Превью описания'

    def prompt_preview(self, obj):
        """Превью AI HR указаний."""
        if obj.prompt:
            preview = obj.prompt[:300] + '...' if len(obj.prompt) > 300 else obj.prompt
            return format_html('<div style="max-height: 200px; overflow-y: auto; border: 1px solid #ddd; padding: 10px;">{}</div>', preview)
        return 'AI HR указания не заданы'
    prompt_preview.short_description = 'AI HR указания'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    """Админ для откликов на вакансии."""
    list_display = ['id', 'applicant_profile', 'vacancy', 'status', 'created_at', 'has_evaluation']
    list_filter = ['status', 'created_at', 'vacancy__department']
    search_fields = ['applicant_profile__name', 'applicant_profile__surname', 'vacancy__name']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['vacancy', 'applicant_profile']

    def has_evaluation(self, obj):
        """Проверка наличия оценки."""
        return bool(obj.cv_evaluation)
    has_evaluation.boolean = True
    has_evaluation.short_description = 'Есть оценка'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ApplicantResumeVersion)
class ApplicantResumeVersionAdmin(admin.ModelAdmin):
    """Админ для версий резюме."""
    list_display = ['id', 'applicant', 'created_at']
    list_filter = ['created_at']
    search_fields = ['applicant__name', 'applicant__surname']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['applicant']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    """Админ для встреч."""
    list_display = ['id', 'applicant_profile', 'vacancy', 'status', 'room_id', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['applicant_profile__name', 'applicant_profile__surname', 'vacancy__name']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['vacancy', 'applicant_profile']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(JobApplicationCVEvaluation)
class JobApplicationCVEvaluationAdmin(admin.ModelAdmin):
    """Админ для оценок резюме."""
    list_display = ['id', 'job_application', 'name', 'score', 'strengths_count', 'weaknesses_count']
    search_fields = ['job_application__applicant_profile__name', 'job_application__vacancy__name']
    readonly_fields = ['id', 'strengths_display', 'weaknesses_display']
    raw_id_fields = ['job_application']

    def strengths_count(self, obj):
        return len(obj.strengths) if obj.strengths else 0
    strengths_count.short_description = 'Сильные стороны'

    def weaknesses_count(self, obj):
        return len(obj.weaknesses) if obj.weaknesses else 0
    weaknesses_count.short_description = 'Слабые стороны'

    def strengths_display(self, obj):
        """Отображение сильных сторон."""
        if obj.strengths:
            items = ''.join([f'<li>{strength}</li>' for strength in obj.strengths])
            return format_html('<ul>{}</ul>', items)
        return 'Не указаны'
    strengths_display.short_description = 'Сильные стороны'

    def weaknesses_display(self, obj):
        """Отображение слабых сторон."""
        if obj.weaknesses:
            items = ''.join([f'<li>{weakness}</li>' for weakness in obj.weaknesses])
            return format_html('<ul>{}</ul>', items)
        return 'Не указаны'
    weaknesses_display.short_description = 'Слабые стороны'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AIModelConfiguration)
class AIModelConfigurationAdmin(admin.ModelAdmin):
    """Админ для конфигураций AI моделей."""
    list_display = ['id', 'name', 'model_type', 'provider', 'model_name', 'is_active', 'created_at']
    list_filter = ['model_type', 'provider', 'is_active', 'created_at']
    search_fields = ['name', 'model_name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'model_type', 'provider', 'is_active')
        }),
        ('Параметры модели', {
            'fields': ('model_name', 'endpoint_url', 'api_key_name', 'model_path', 'engine_path', 'context_length')
        }),
        ('Avatar параметры', {
            'fields': ('face_id', 'max_session_length', 'max_idle_time'),
            'classes': ('collapse',)
        }),
        ('Параметры генерации', {
            'fields': ('temperature', 'max_tokens', 'top_p', 'frequency_penalty', 'presence_penalty'),
            'classes': ('collapse',)
        }),
        ('Кастомные параметры', {
            'fields': ('custom_parameters',),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(InterviewModelConfiguration)
class InterviewModelConfigurationAdmin(admin.ModelAdmin):
    """Админ для конфигураций моделей интервью."""
    list_display = ['id', 'vacancy', 'has_llm', 'has_stt', 'has_tts', 'has_avatar', 'has_vision', 'max_questions']
    search_fields = ['vacancy__name', 'vacancy__department']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['vacancy', 'llm_model', 'stt_model', 'tts_model', 'avatar_model', 'vision_model']

    def has_llm(self, obj):
        return bool(obj.llm_model)
    has_llm.boolean = True
    has_llm.short_description = 'LLM'

    def has_stt(self, obj):
        return bool(obj.stt_model)
    has_stt.boolean = True
    has_stt.short_description = 'STT'

    def has_tts(self, obj):
        return bool(obj.tts_model)
    has_tts.boolean = True
    has_tts.short_description = 'TTS'

    def has_avatar(self, obj):
        return bool(obj.avatar_model)
    has_avatar.boolean = True
    has_avatar.short_description = 'Avatar'

    def has_vision(self, obj):
        return bool(obj.vision_model)
    has_vision.boolean = True
    has_vision.short_description = 'Vision'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ModelUsageLog)
class ModelUsageLogAdmin(admin.ModelAdmin):
    """Админ для логов использования моделей."""
    list_display = ['id', 'model_configuration', 'session_id', 'tokens_used', 'duration_seconds', 'cost_usd', 'created_at']
    list_filter = ['model_configuration__model_type', 'model_configuration__provider', 'created_at']
    search_fields = ['session_id', 'model_configuration__name']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['model_configuration', 'interview_configuration']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Настройка админ панели
admin.site.site_header = "HR AI Admin Panel"
admin.site.site_title = "HR AI Admin"
admin.site.index_title = "Управление HR AI системой"
