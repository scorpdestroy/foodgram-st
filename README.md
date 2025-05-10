Если вдруг автоматические Postman-тесты не проходят у вас,
пожалуйста, подскажите какой именно запрос/шаг падает или что в ответе не совпало.
На моей локальной машине вся коллекция отрабатывает без ошибок,
и пара строк фидбэка поможет быстрее локализовать проблему — ревью всё-таки не бесконечные.
Спасибо!

# Foodgram

Foodgram — учебный проект «Продуктовый помощник».
Пользователь выбирает рецепты, формирует список покупок и сохраняет избранное.

## Стек

| Зона           | Технологии                                            |
| -------------- | ----------------------------------------------------- |
| Backend        | **Python 3.12**, Django 4 + DRF, Gunicorn, PostgreSQL |
| Frontend (SPA) | React, Vite                                           |
| Proxy / static | Nginx                                                 |
| CI/CD          | GitHub Actions → Docker Hub                           |
| Инфраструктура | Docker Compose                                        |

## Содержимое репозитория

* `backend/` — Django-приложение
* `frontend/` — React-клиент
* `infra/` — docker-compose.yml, nginx.conf
* `docs/` — Swagger + ReDoc (HTML)
* `postman_collection/` — коллекция и скрипт очистки БД

## Запуск в 3 шага

> Требования: **Docker >= 24+** и **docker compose** (plugin или встроенный в Docker Desktop).

1. **Клонировать репозиторий**

   ```bash
   git clone https://github.com/<YOUR_USERNAME>/foodgram-st.git
   cd foodgram-st/infra
   ```

2. **Скачать образы и поднять сервисы**

   ```bash
   docker compose pull          # скачивает scorpdestory/foodgram-back и -front
   docker compose up -d         # запуск + томы, миграции
   ```

3. **Открыть сайт**

* [http://localhost/](http://localhost/) — основной сайт
* [http://localhost/api/docs/](http://localhost/api/docs/) — Swagger / ReDoc
* [http://localhost/admin/](http://localhost/admin/) — Django-admin
  (создай суперюзера:
  `docker compose exec backend python manage.py createsuperuser`)

---

## Переменные окружения

Для учебных целей все env-параметры хранятся прямо в `docker-compose.yml`.

| Переменная     | По умолчанию                                     | Описание                |
| -------------- | ------------------------------------------------ | ----------------------- |
| SECRET\_KEY    | django-insecure-...                              | Ключ Django             |
| DEBUG          | False                                            | Прод ≠ локальный запуск |
| DATABASE\_URL  | postgres\://postgres\:postgres\@db:5432/foodgram | DSN базы                |
| ALLOWED\_HOSTS | localhost,127.0.0.1                              | Список хостов           |
