#!/bin/bash

# Название папки проекта
PROJECT_NAME="weather_bot"
PROJECT_PATH="/root/$PROJECT_NAME"

echo "🚀 Начинаю деплой бота..."

# 1. Переходим в папку (или клонируем, если её нет)
if [ ! -d "$PROJECT_PATH" ]; then
    echo "📂 Клонирую репозиторий..."
    git clone https://github.com/S-Zaur/weather-bot.git $PROJECT_PATH
    cd $PROJECT_PATH
else
    echo "🔄 Обновляю код из Git..."
    cd $PROJECT_PATH
    git pull origin main
fi

# 2. Создаем виртуальное окружение, если его нет
if [ ! -d "venv" ]; then
    echo "📦 Создаю виртуальное окружение..."
    python3 -m venv venv
fi

# 3. Устанавливаем/обновляем зависимости
echo "🛠 Устанавливаю зависимости..."
source /root/$PROJECT_NAME/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Настраиваем системный сервис
echo "⚙️ Настраиваю systemd сервис..."
# Копируем файл сервиса в систему
cp bot.service /etc/systemd/system/weather_bot.service

# Перезагружаем демона и запускаем бота
systemctl daemon-reload
systemctl enable weather_bot
systemctl restart weather_bot

echo "✅ Деплой успешно завершен! Бот запущен."
echo "📜 Чекнуть логи: journalctl -u weather_bot -f"