"""
Dashboard callback для Unfold theme.
"""

from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Count, Q
from .models import (
    User, HRProfile, ApplicantProfile, Vacancy, JobApplication,
    Meeting, JobApplicationCVEvaluation, AIModelConfiguration,
    InterviewModelConfiguration, ModelUsageLog
)


def dashboard_callback(request):
    """Callback для dashboard с статистикой."""
    
    # Статистика пользователей
    total_users = User.objects.count()
    hr_users = User.objects.filter(role='hr').count()
    applicant_users = User.objects.filter(role='applicant').count()
    
    # Статистика вакансий
    total_vacancies = Vacancy.objects.count()
    active_vacancies = Vacancy.objects.filter(status='active').count()
    closed_vacancies = Vacancy.objects.filter(status='closed').count()
    
    # Статистика откликов
    total_applications = JobApplication.objects.count()
    pending_applications = JobApplication.objects.filter(status='cvReview').count()
    interview_applications = JobApplication.objects.filter(status='interview').count()
    approved_applications = JobApplication.objects.filter(status='approved').count()
    
    # Статистика AI моделей
    total_models = AIModelConfiguration.objects.count()
    active_models = AIModelConfiguration.objects.filter(is_active=True).count()
    llm_models = AIModelConfiguration.objects.filter(model_type='llm').count()
    stt_models = AIModelConfiguration.objects.filter(model_type='stt').count()
    tts_models = AIModelConfiguration.objects.filter(model_type='tts').count()
    
    # Статистика встреч
    total_meetings = Meeting.objects.count()
    pending_meetings = Meeting.objects.filter(status='waitMeeting').count()
    
    # Статистика оценок
    total_evaluations = JobApplicationCVEvaluation.objects.count()
    
    dashboard_html = f"""
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <!-- Пользователи -->
        <div class="bg-white rounded-lg shadow p-6">
            <div class="flex items-center">
                <div class="p-3 rounded-full bg-blue-100 text-blue-600">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
                    </svg>
                </div>
                <div class="ml-4">
                    <h3 class="text-lg font-semibold text-gray-900">Пользователи</h3>
                    <p class="text-3xl font-bold text-blue-600">{total_users}</p>
                    <p class="text-sm text-gray-500">HR: {hr_users}, Кандидаты: {applicant_users}</p>
                </div>
            </div>
        </div>
        
        <!-- Вакансии -->
        <div class="bg-white rounded-lg shadow p-6">
            <div class="flex items-center">
                <div class="p-3 rounded-full bg-green-100 text-green-600">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V8a2 2 0 012-2V6"></path>
                    </svg>
                </div>
                <div class="ml-4">
                    <h3 class="text-lg font-semibold text-gray-900">Вакансии</h3>
                    <p class="text-3xl font-bold text-green-600">{total_vacancies}</p>
                    <p class="text-sm text-gray-500">Активные: {active_vacancies}, Закрытые: {closed_vacancies}</p>
                </div>
            </div>
        </div>
        
        <!-- Отклики -->
        <div class="bg-white rounded-lg shadow p-6">
            <div class="flex items-center">
                <div class="p-3 rounded-full bg-yellow-100 text-yellow-600">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                </div>
                <div class="ml-4">
                    <h3 class="text-lg font-semibold text-gray-900">Отклики</h3>
                    <p class="text-3xl font-bold text-yellow-600">{total_applications}</p>
                    <p class="text-sm text-gray-500">На рассмотрении: {pending_applications}, Интервью: {interview_applications}</p>
                </div>
            </div>
        </div>
        
        <!-- AI Модели -->
        <div class="bg-white rounded-lg shadow p-6">
            <div class="flex items-center">
                <div class="p-3 rounded-full bg-purple-100 text-purple-600">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                    </svg>
                </div>
                <div class="ml-4">
                    <h3 class="text-lg font-semibold text-gray-900">AI Модели</h3>
                    <p class="text-3xl font-bold text-purple-600">{total_models}</p>
                    <p class="text-sm text-gray-500">Активные: {active_models}, LLM: {llm_models}, STT: {stt_models}, TTS: {tts_models}</p>
                </div>
            </div>
        </div>
        
        <!-- Встречи -->
        <div class="bg-white rounded-lg shadow p-6">
            <div class="flex items-center">
                <div class="p-3 rounded-full bg-red-100 text-red-600">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                    </svg>
                </div>
                <div class="ml-4">
                    <h3 class="text-lg font-semibold text-gray-900">Встречи</h3>
                    <p class="text-3xl font-bold text-red-600">{total_meetings}</p>
                    <p class="text-sm text-gray-500">Ожидают: {pending_meetings}</p>
                </div>
            </div>
        </div>
        
        <!-- Оценки -->
        <div class="bg-white rounded-lg shadow p-6">
            <div class="flex items-center">
                <div class="p-3 rounded-full bg-indigo-100 text-indigo-600">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"></path>
                    </svg>
                </div>
                <div class="ml-4">
                    <h3 class="text-lg font-semibold text-gray-900">Оценки</h3>
                    <p class="text-3xl font-bold text-indigo-600">{total_evaluations}</p>
                    <p class="text-sm text-gray-500">Оценок резюме</p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Быстрые ссылки -->
    <div class="bg-white rounded-lg shadow p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Быстрые ссылки</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <a href="{reverse('admin:hr_admin_vacancy_changelist')}" class="flex items-center p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors">
                <svg class="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V8a2 2 0 012-2V6"></path>
                </svg>
                <span class="text-blue-600 font-medium">Вакансии</span>
            </a>
            
            <a href="{reverse('admin:hr_admin_jobapplication_changelist')}" class="flex items-center p-3 bg-green-50 rounded-lg hover:bg-green-100 transition-colors">
                <svg class="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                <span class="text-green-600 font-medium">Отклики</span>
            </a>
            
            <a href="{reverse('admin:hr_admin_aimodelconfiguration_changelist')}" class="flex items-center p-3 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors">
                <svg class="w-5 h-5 text-purple-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                </svg>
                <span class="text-purple-600 font-medium">AI Модели</span>
            </a>
            
            <a href="{reverse('admin:hr_admin_meeting_changelist')}" class="flex items-center p-3 bg-red-50 rounded-lg hover:bg-red-100 transition-colors">
                <svg class="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                </svg>
                <span class="text-red-600 font-medium">Встречи</span>
            </a>
        </div>
    </div>
    """
    
    return dashboard_html
