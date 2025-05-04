#!/bin/bash

# Остановить выполнение при ошибке
set -e

# Перейти в папку проекта, если скрипт запускается не из неё
cd "$(dirname "$0")"

# Выполнить очистку БД
echo "==> Очистка базы данных..."
bash ./../postman_collection/clear_db.sh

# Перейти в infra и запустить docker-compose
echo "==> Запуск docker-compose с пересборкой..."
cd ../infra
docker compose up -d --build

echo "==> Готово!"