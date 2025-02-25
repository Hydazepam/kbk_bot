import os
from dotenv import load_dotenv

# Явно указываем путь к .env файлу
load_dotenv('/app/.env')  # Для Docker контейнера

TOKEN = os.environ.get('TELEGRAM_TOKEN')
DB_URL = os.environ.get('DATABASE_URL')
ADMIN_ID = int(os.environ.get('ADMIN_ID')) if os.environ.get('ADMIN_ID') else None

# Проверка обязательных переменных
assert TOKEN, "TELEGRAM_TOKEN не задан!"
assert DB_URL, "DATABASE_URL не задана!"
assert ADMIN_ID, "ADMIN_ID не задан!"