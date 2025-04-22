#!/usr/bin/env bash

# Определяем python
case "$OSTYPE" in
    msys*|cygwin*) python=python ;;
    *)             python=python3 ;;
esac

# Ищем первый manage.py в дереве проекта (исключаем venv)
PATH_TO_MANAGE_PY=$(find . -type f -name "manage.py" \
    -not -path "*/venv/*" \
    -not -path "*/env/*" | head -n 1)

if [[ -z "$PATH_TO_MANAGE_PY" ]]; then
    echo "Не найден файл manage.py — проверьте структуру проекта."
    exit 1
fi

BASE_DIR=$(dirname "$PATH_TO_MANAGE_PY")
cd "$BASE_DIR" || {
    echo "Не удалось перейти в каталог $BASE_DIR"
    exit 1
}

# Очищаем тестовых пользователей
echo "Удаляю тестовые аккаунты из БД..."
$python manage.py shell <<'PYCODE'
from django.contrib.auth import get_user_model
User = get_user_model()
usernames_list = [
    'vasya.ivanov', 'second-user', 'third-user-username',
    'NoEmail', 'NoFirstName', 'NoLastName', 'NoPassword',
    'TooLongEmail',
    'the-username-that-is-150-characters-long-and-should-not-pass-validation-if-the-serializer-is-configured-correctly-otherwise-the-current-test-will-fail-',
    'TooLongFirstName', 'TooLongLastName', 'InvalidU$ername', 'EmailInUse'
]
deleted, _ = User.objects.filter(username__in=usernames_list).delete()
if deleted:
    print("Тестовые пользователи удалены.")
    exit(0)
else:
    print("Тестовых записей не найдено или уже удалены.")
    exit(1)
PYCODE

status=$?
if [ $status -ne 0 ]; then
    echo "Ошибка при очистке БД: объекты отсутствуют либо произошёл сбой."
    exit $status
fi

echo "База данных очищена."
