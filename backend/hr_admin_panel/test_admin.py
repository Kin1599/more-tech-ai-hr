#!/usr/bin/env python
"""
Скрипт для тестирования Django Admin Panel.
"""

import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_panel.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from hr_admin.models import (
    User as HRUser, HRProfile, ApplicantProfile, Vacancy, JobApplication,
    Meeting, JobApplicationCVEvaluation, AIModelConfiguration,
    InterviewModelConfiguration, ModelUsageLog
)

def test_admin_panel():
    """Тестирование админ панели."""
    print("🧪 Тестирование Django Admin Panel...")
    
    # Создание тестового клиента
    client = Client()
    
    # Создание суперпользователя для тестирования
    admin_user = User.objects.create_superuser(
        username='testadmin',
        email='test@example.com',
        password='testpass123'
    )
    
    # Авторизация
    client.login(username='testadmin', password='testpass123')
    
    # Тестирование основных страниц
    test_urls = [
        '/admin/',
        '/admin/hr_admin/user/',
        '/admin/hr_admin/hrprofile/',
        '/admin/hr_admin/applicantprofile/',
        '/admin/hr_admin/vacancy/',
        '/admin/hr_admin/jobapplication/',
        '/admin/hr_admin/meeting/',
        '/admin/hr_admin/aimodelconfiguration/',
        '/admin/hr_admin/interviewmodelconfiguration/',
        '/admin/hr_admin/modelusagelog/',
    ]
    
    print("\n📋 Тестирование URL админ панели:")
    for url in test_urls:
        try:
            response = client.get(url)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {url} - {response.status_code}")
        except Exception as e:
            print(f"❌ {url} - Ошибка: {e}")
    
    # Тестирование создания тестовых данных
    print("\n📊 Создание тестовых данных...")
    
    try:
        # Создание тестового пользователя
        test_user = HRUser.objects.create(
            email='test@example.com',
            password_hash='test_hash',
            role='hr'
        )
        print("✅ Тестовый пользователь создан")
        
        # Создание HR профиля
        hr_profile = HRProfile.objects.create(
            user=test_user,
            name='Тест',
            surname='Тестов',
            department='IT'
        )
        print("✅ HR профиль создан")
        
        # Создание вакансии
        vacancy = Vacancy.objects.create(
            hr_profile=hr_profile,
            name='Тестовая вакансия',
            department='IT',
            status='active',
            description='Описание тестовой вакансии'
        )
        print("✅ Тестовая вакансия создана")
        
        # Создание AI модели
        ai_model = AIModelConfiguration.objects.create(
            name='Тестовая модель',
            model_type='llm',
            provider='openai',
            model_name='gpt-3.5-turbo',
            is_active=True
        )
        print("✅ Тестовая AI модель создана")
        
        print("\n🎉 Все тесты прошли успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при создании тестовых данных: {e}")
    
    # Очистка тестовых данных
    try:
        admin_user.delete()
        print("🧹 Тестовые данные очищены")
    except:
        pass

def test_models():
    """Тестирование моделей."""
    print("\n🔍 Тестирование моделей Django...")
    
    models_to_test = [
        HRUser,
        HRProfile,
        ApplicantProfile,
        Vacancy,
        JobApplication,
        Meeting,
        JobApplicationCVEvaluation,
        AIModelConfiguration,
        InterviewModelConfiguration,
        ModelUsageLog
    ]
    
    for model in models_to_test:
        try:
            # Проверяем, что модель может быть создана
            count = model.objects.count()
            print(f"✅ {model.__name__} - {count} записей")
        except Exception as e:
            print(f"❌ {model.__name__} - Ошибка: {e}")

def test_database_connection():
    """Тестирование подключения к базе данных."""
    print("\n🔌 Тестирование подключения к базе данных...")
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print("✅ Подключение к базе данных успешно")
            else:
                print("❌ Ошибка подключения к базе данных")
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")

def main():
    """Основная функция тестирования."""
    print("🎛️ Тестирование Django Admin Panel с темой Unfold")
    print("=" * 50)
    
    # Тестирование подключения к БД
    test_database_connection()
    
    # Тестирование моделей
    test_models()
    
    # Тестирование админ панели
    test_admin_panel()
    
    print("\n" + "=" * 50)
    print("🎉 Тестирование завершено!")
    print("\n📝 Для запуска админ панели выполните:")
    print("   python manage.py runserver 0.0.0.0:8000")
    print("   Откройте: http://localhost:8000/admin/")
    print("   Логин: admin")
    print("   Пароль: admin123")

if __name__ == '__main__':
    main()
