#!/bin/bash

# Название выходного файла
OUTPUT_FILE="structure.txt"

# Очищаем/создаём файл
> "$OUTPUT_FILE"

# Функция для рекурсивного обхода
print_tree() {
    local dir="$1"
    local prefix="$2"

    # Получаем список файлов и директорий, отсортированный
    local entries=()
    while IFS= read -r entry; do
        entries+=("$entry")
    done < <(ls -1A "$dir" | sort)

    local total=${#entries[@]}
    local count=0

    for entry in "${entries[@]}"; do
        count=$((count+1))
        local path="$dir/$entry"
        local connector="├──"

        if [ "$count" -eq "$total" ]; then
            connector="└──"
        fi

        echo "${prefix}${connector} $entry" >> "$OUTPUT_FILE"

        if [ -d "$path" ]; then
            local new_prefix="$prefix"
            if [ "$count" -eq "$total" ]; then
                new_prefix="${prefix}    "
            else
                new_prefix="${prefix}│   "
            fi
            print_tree "$path" "$new_prefix"
        fi
    done
}

# Начинаем с текущей директории
echo "." >> "$OUTPUT_FILE"
print_tree "." ""

echo "Готово! Структура сохранена в $OUTPUT_FILE"
