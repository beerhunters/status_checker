#!/bin/bash

# Настройки
CONTAINER_NAME="monitoring_db"  # имя твоего контейнера с PostgreSQL
DB_NAME="monitoring_bot"                 # имя целевой БД
DB_USER="postgres"                       # пользователь БД
DUMP_FILE="dump.sql"                     # путь к дампу

# Проверка, существует ли файл дампа
if [ ! -f "$DUMP_FILE" ]; then
  echo "❌ Файл дампа '$DUMP_FILE' не найден!"
  exit 1
fi

echo "🔄 Начинаем восстановление дампа в БД '$DB_NAME' внутри контейнера '$CONTAINER_NAME'..."

# Шаг 1: Очистка БД (удаление всех таблиц, последовательностей, индексов и т.д.)
echo "🧹 Очищаем целевую БД..."
docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" <<EOF
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
EOF

if [ $? -ne 0 ]; then
  echo "❌ Ошибка при очистке БД"
  exit 1
fi

# Шаг 2: Восстановление дампа
echo "📥 Выполняем импорт дампа в БД..."
docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" < "$DUMP_FILE"

if [ $? -eq 0 ]; then
  echo "✅ Дамп успешно загружен в БД '$DB_NAME'"
else
  echo "❌ Ошибка при импорте дампа"
  exit 1
fi