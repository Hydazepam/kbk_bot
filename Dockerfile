FROM python:3.11-slim

WORKDIR /app

# Сначала копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Затем копируем ВСЕ файлы
COPY . .

CMD ["python", "-m", "bot.main"]