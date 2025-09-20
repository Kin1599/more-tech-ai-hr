#!/bin/bash

# Скрипт для запуска Django Admin Panel

echo "🎛️ Запуск Django Admin Panel с темой Unfold..."

# Проверка наличия Python
if ! command -v python &> /dev/null; then
    echo "❌ Python не найден. Установите Python 3.11+"
    exit 1
fi

# Проверка наличия pip
if ! command -v pip &> /dev/null; then
    echo "❌ pip не найден. Установите pip"
    exit 1
fi

# Установка зависимостей
echo "📦 Установка зависимостей..."
pip install -r requirements.txt

# Проверка подключения к базе данных
echo "🔍 Проверка подключения к базе данных..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_panel.settings')
django.setup()
from django.db import connection
try:
    connection.ensure_connection()
    print('✅ Подключение к базе данных успешно')
except Exception as e:
    print(f'❌ Ошибка подключения к базе данных: {e}')
    exit(1)
"

# Создание миграций
echo "📝 Создание миграций..."
python manage.py makemigrations hr_admin

# Применение миграций
echo "🔄 Применение миграций..."
python manage.py migrate

# Создание суперпользователя
echo "👤 Создание суперпользователя..."
python create_admin.py

# Сбор статических файлов
echo "📁 Сбор статических файлов..."
python manage.py collectstatic --noinput

# Запуск сервера
echo "🚀 Запуск сервера..."
echo "🌐 Админ панель будет доступна по адресу: http://localhost:8000/admin/"
echo "👤 Логин: admin"
echo "🔑 Пароль: admin123"
echo ""
echo "Нажмите Ctrl+C для остановки сервера"

python manage.py runserver 0.0.0.0:8000
