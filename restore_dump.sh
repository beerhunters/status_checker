
#!/bin/bash
DB_NAME="data/monitoring_bot.db"
DUMP_FILE="dump.sql"
ADAPTED_DUMP="adapted_dump.sql"

if [ ! -f "$DUMP_FILE" ]; then
  echo "❌ Файл дампа '$DUMP_FILE' не найден!"
  exit 1
fi

echo "🔄 Начинаем восстановление дампа в БД '$DB_NAME'..."
echo "🧹 Очищаем целевую БД..."

# Создаем директорию для БД, если не существует
mkdir -p data
chmod -R 777 data

# Удаляем старую БД, если существует
rm -f "$DB_NAME"

# Создаем адаптированный дамп для SQLite
echo "🔧 Адаптируем дамп для SQLite..."
cat "$DUMP_FILE" | \
  # Удаляем команды SET
  grep -v '^SET ' | \
  # Удаляем команды OWNER
  grep -v ' OWNER TO ' | \
  # Удаляем команды SEQUENCE
  grep -v '^CREATE SEQUENCE ' | \
  grep -v '^ALTER SEQUENCE ' | \
  # Удаляем команды pg_catalog
  grep -v 'pg_catalog' | \
  # Удаляем схему public
  sed 's/public\.//g' | \
  # Заменяем SERIAL на INTEGER PRIMARY KEY AUTOINCREMENT
  sed 's/SERIAL/INTEGER PRIMARY KEY AUTOINCREMENT/g' | \
  # Заменяем id integer NOT NULL на id INTEGER PRIMARY KEY AUTOINCREMENT
  sed 's/id integer NOT NULL/id INTEGER PRIMARY KEY AUTOINCREMENT/g' | \
  # Заменяем character varying (с или без длины) на TEXT
  sed 's/character varying$$ [0-9]* $$\?$$ [ ,)] $$/TEXT\2/g' | \
  # Заменяем bigint на INTEGER
  sed 's/bigint/INTEGER/g' | \
  # Заменяем timestamp with time zone на DATETIME
  sed 's/timestamp with time zone/DATETIME/g' | \
  # Удаляем команды ALTER TABLE ... SET DEFAULT nextval
  grep -v 'ALTER TABLE ONLY.*SET DEFAULT nextval' | \
  # Преобразуем команды создания индексов
  sed 's/CREATE INDEX $$ [a-z_][a-z_]* $$ ON public\.$$ [a-z_][a-z_]* $$/CREATE INDEX \1 ON \2/g' | \
  # Преобразуем команды добавления ограничений
  sed 's/ALTER TABLE ONLY $$ [a-z_][a-z_]* $$/ALTER TABLE \1/g' | \
  # Удаляем команды, которые не нужны для SQLite
  grep -v 'CREATE SCHEMA' | \
  grep -v 'SET default_tablespace' | \
  grep -v 'SET default_table_access_method' | \
  # Удаляем комментарии PostgreSQL
  grep -v '^--' > "$ADAPTED_DUMP"

# Выводим содержимое адаптированного дампа для отладки
echo "📜 Содержимое адаптированного дампа:"
cat "$ADAPTED_DUMP"

# Создаем новую БД и импортируем адаптированный дамп
echo "📥 Выполняем импорт дампа в БД..."
sqlite3 "$DB_NAME" < "$ADAPTED_DUMP"

if [ $? -eq 0 ]; then
  echo "✅ Таблицы и данные успешно импортированы в БД '$DB_NAME'"
  # Проверяем, созданы ли таблицы
  echo "🔍 Проверяем созданные таблицы..."
  sqlite3 "$DB_NAME" ".tables"
  # Проверяем наличие таблиц
  tables=$(sqlite3 "$DB_NAME" ".tables")
  if [[ "$tables" == *"users"* && "$tables" == *"sites"* && "$tables" == *"system_settings"* ]]; then
    echo "✅ Таблицы users, sites, system_settings созданы"
    # Добавляем команды для автоинкремента
    echo "🔧 Устанавливаем начальные значения автоинкремента..."
    sqlite3 "$DB_NAME" <<EOF
INSERT INTO sqlite_sequence (name, seq) VALUES ('users', 41);
INSERT INTO sqlite_sequence (name, seq) VALUES ('sites', 76);
INSERT INTO sqlite_sequence (name, seq) VALUES ('system_settings', 1);
EOF
    if [ $? -eq 0 ]; then
      echo "✅ Начальные значения автоинкремента установлены"
      echo "🔍 Проверяем таблицу sqlite_sequence..."
      sqlite3 "$DB_NAME" "SELECT * FROM sqlite_sequence;"
    else
      echo "❌ Ошибка при установке начальных значений автоинкремента"
      cat "$ADAPTED_DUMP"
      exit 1
    fi
  else
    echo "❌ Таблицы не созданы или созданы некорректно: $tables"
    cat "$ADAPTED_DUMP"
    exit 1
  fi
else
  echo "❌ Ошибка при импорте дампа"
  cat "$ADAPTED_DUMP"
  exit 1
fi

# Очищаем временный файл
rm -f "$ADAPTED_DUMP"