#!/usr/bin/env python
"""
Скрипт для создания суперпользователя Django админ панели.
"""

import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_panel.settings')
django.setup()

from django.contrib.auth.models import User

def create_superuser():
    """Создание суперпользователя."""
    username = 'admin'
    email = 'admin@hr-ai.com'
    password = 'admin123'
    
    if User.objects.filter(username=username).exists():
        print(f"Суперпользователь {username} уже существует!")
        return
    
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    
    print(f"Суперпользователь создан:")
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"URL: http://localhost:8000/admin/")

if __name__ == '__main__':
    create_superuser()
