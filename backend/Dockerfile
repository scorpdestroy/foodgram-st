# foodgram-st/backend/Dockerfile
FROM python:3.11-slim

# Не пишем .pyc, не буферизуем вывод
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копируем всё остальное приложение
COPY . .

# По умолчанию миграции и старт Gunicorn
CMD ["sh", "-c", "\
    python manage.py migrate && \
    python manage.py collectstatic --noinput && \
    gunicorn foodgram_backend.wsgi:application --bind 0.0.0.0:8000 \
"]
