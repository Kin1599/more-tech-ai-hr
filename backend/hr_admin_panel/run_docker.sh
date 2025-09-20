#!/bin/bash

# Скрипт для запуска Django Admin Panel через Docker

echo "🐳 Запуск Django Admin Panel через Docker..."

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не найден. Установите Docker"
    exit 1
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не найден. Установите Docker Compose"
    exit 1
fi

# Остановка существующих контейнеров
echo "🛑 Остановка существующих контейнеров..."
docker-compose -f docker-compose.admin.yml down

# Сборка и запуск контейнеров
echo "🔨 Сборка и запуск контейнеров..."
docker-compose -f docker-compose.admin.yml up --build -d

# Ожидание запуска базы данных
echo "⏳ Ожидание запуска базы данных..."
sleep 10

# Создание суперпользователя
echo "👤 Создание суперпользователя..."
docker-compose -f docker-compose.admin.yml exec admin-panel python create_admin.py

# Показ статуса
echo "📊 Статус контейнеров:"
docker-compose -f docker-compose.admin.yml ps

echo ""
echo "🎉 Django Admin Panel запущена!"
echo "🌐 Админ панель доступна по адресу: http://localhost:8000/admin/"
echo "👤 Логин: admin"
echo "🔑 Пароль: admin123"
echo ""
echo "📋 Полезные команды:"
echo "  Просмотр логов: docker-compose -f docker-compose.admin.yml logs -f"
echo "  Остановка: docker-compose -f docker-compose.admin.yml down"
echo "  Перезапуск: docker-compose -f docker-compose.admin.yml restart"
echo ""
echo "Нажмите Ctrl+C для остановки просмотра логов (контейнеры продолжат работать)"

# Показ логов
docker-compose -f docker-compose.admin.yml logs -f
