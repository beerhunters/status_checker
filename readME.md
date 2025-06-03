# Website Monitoring Bot

## 📌 Описание проекта

Приложение для мониторинга доступности веб-сайтов с уведомлениями через Telegram. Включает Telegram-бота для взаимодействия с пользователями, фоновую проверку сайтов через Celery и веб-панель администратора для управления пользователями и сайтами. Проект использует Docker для развертывания и PostgreSQL/Redis для хранения данных и управления задачами.

---

## 🧱 Архитектура

Проект состоит из следующих компонентов:

- **Telegram-бот (`bot/`)**: Обработка команд пользователей, добавление/удаление сайтов, отправка уведомлений.
- **Веб-панель администратора (`web/`)**: Интерфейс для управления пользователями, сайтами и настройками.
- **Celery**: Фоновая проверка доступности сайтов по расписанию.
- **PostgreSQL**: Хранение данных о пользователях, сайтах и системных настройках.
- **Redis**: Брокер сообщений для Celery и хранения расписания задач.

---

## ⚙️ Возможности

### Для пользователей (через Telegram):
- ➕ Добавление сайтов для мониторинга.
- ❌ Удаление сайтов.
- 📢 Уведомления об изменении статуса сайта (доступен/недоступен).
- Обработка ошибок с уведомлением пользователей и возвратом в главное меню.

### Для администратора (веб-интерфейс):
- 👤 Просмотр списка пользователей и их сайтов.
- 🌐 Управление сайтами: просмотр, обновление статуса, удаление.
- 🔄 Настройка интервала проверки сайтов.
- 📢 Отправка рассылки всем пользователям.
- Просмотр логов ошибок в `logs/bot_errors.log`.

### Обработка ошибок:
- Логирование ошибок в файл `logs/bot_errors.log` с подробной информацией (тип ошибки, сообщение, местоположение, трейсбек).
- Уведомление пользователей об ошибках с предложением попробовать позже.
- Уведомление администраторов через Telegram о критических ошибках.

---

## 🔄 Как это работает

1. Пользователь взаимодействует с Telegram-ботом через команды и кнопки:
   - `/start`: Запуск бота и отображение главного меню.
   - «➕ Добавить сайт»: Добавление URL для мониторинга.
   - «🌐 Мои сайты»: Просмотр и удаление сайтов.
2. Celery периодически (по умолчанию каждые 5 минут) проверяет доступность сайтов и обновляет их статус в базе данных.
3. При изменении статуса сайта (доступен → недоступен или наоборот) пользователю отправляется уведомление.
4. Веб-панель предоставляет администратору интерфейс для:
   - Аутентификации (логин/пароль, JWT).
   - Управления пользователями и сайтами.
   - Настройки интервала проверки.
   - Отправки массовых уведомлений.
5. Ошибки логируются в `logs/bot_errors.log`, пользователи получают уведомления об ошибках, а администраторы — детализированные сообщения в Telegram.

---

## 🛠️ Технологии

- **Python 3.10**
- **Aiogram 3.x**: Telegram-бот.
- **FastAPI**: Веб-панель администратора.
- **SQLAlchemy + asyncpg**: Асинхронная работа с PostgreSQL.
- **Celery + Redis**: Фоновые задачи и брокер сообщений.
- **aiohttp/requests**: Проверка доступности сайтов.
- **Jinja2**: Шаблоны для веб-интерфейса.
- **Docker / Docker Compose**: Контейнеризация.

---

## 🚀 Подготовка сервера и запуск

### 1. Подготовка сервера

#### Установка Docker
```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
```

#### Добавление GPG-ключа Docker
```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

#### Добавление репозитория Docker
```bash
echo \
  "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

#### Установка Docker
```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io
```

#### Установка Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

#### Вход в Docker (если требуется доступ к приватным образам)
```bash
docker login
```

### 2. Подготовка проекта

#### Клонирование репозитория
```bash
git clone https://github.com/your/project.git
cd project
```

#### Создание директории для логов
```bash
mkdir -p logs
```

#### Настройка `.env` файла
Создайте файл `.env` в корне проекта (рядом с `docker-compose.yml`):
```env
BOT_TOKEN=your_telegram_bot_token
DB_USER=postgres
DB_PASSWORD=mysecretpassword
DB_HOST=db
DB_PORT=5432
DB_NAME=monitoring_bot
REDIS_HOST=redis
REDIS_PORT=6379
CHECK_INTERVAL_MINUTES=5
ADMIN_USERNAME=admin
ADMIN_PASSWORD=strongpassword
ADMIN_CHAT_ID=your_admin_chat_id
JWT_SECRET_KEY=your-secure-random-key-here
LOG_LEVEL=INFO
```

**Примечание**: Замените `your_telegram_bot_token`, `your_admin_chat_id`, и `your-secure-random-key-here` на реальные значения. `ADMIN_CHAT_ID` — это Telegram ID чата для уведомлений об ошибках.

### 3. Запуск контейнеров
Из корня проекта выполните:
```bash
docker-compose up -d --build
```

**Флаги**:
- `-d`: Запуск в фоновом режиме.
- `--build`: Пересборка Docker-образов.

После запуска:
- Telegram-бот начнет принимать команды.
- Celery будет проверять сайты каждые `CHECK_INTERVAL_MINUTES` минут.
- Веб-панель доступна по адресу: `http://localhost:8000/login`.
- Логи ошибок сохраняются в `logs/bot_errors.log`.

---

## 👥 Использование

### Для пользователей (Telegram):
1. Откройте Telegram и начните чат с ботом.
2. Отправьте команду `/start`.
3. Используйте кнопки в главном меню:
   - «➕ Добавить сайт»: Введите URL (например, `https://example.com`).
   - «🌐 Мои сайты»: Просмотр и удаление сайтов.
4. При ошибке вы получите сообщение с предложением попробовать позже.

### Для администратора (веб-панель):
1. Перейдите по адресу: `http://localhost:8000/login`.
2. Введите логин и пароль из `.env` (`ADMIN_USERNAME` и `ADMIN_PASSWORD`).
3. Используйте меню для:
   - Просмотра списка пользователей и их сайтов.
   - Обновления статуса или удаления сайтов.
   - Настройки интервала проверки (`/settings`).
   - Отправки рассылки всем пользователям (`/broadcast`).
4. Просматривайте логи ошибок в `logs/bot_errors.log` или получайте уведомления в Telegram (в чат `ADMIN_CHAT_ID`).

---

## 📁 Структура проекта

```
├── bot/
│   ├── bot_main.py         # Точка входа для Telegram-бота
│   ├── celery_app.py       # Настройка и задачи Celery
│   ├── Dockerfile.bot      # Docker-файл для бота
│   ├── fsm.py              # Состояния для добавления сайтов
│   ├── handlers.py         # Обработчики команд и ошибок
│   ├── keyboards.py        # Inline-клавиатуры
│   ├── monitoring.py       # Проверка доступности сайтов
│   └── requirements.bot.txt # Зависимости бота
├── shared/
│   ├── config.py           # Конфигурация приложения
│   ├── db.py               # Работа с базой данных
│   ├── logger_setup.py     # Настройка логирования
│   ├── models.py           # Модели SQLAlchemy
│   ├── monitoring.py       # Логика асинхронной проверки сайтов
│   ├── schemas.py          # Pydantic-схемы
│   └── utils.py            # Утилиты (синхронная проверка, уведомления)
├── web/
│   ├── templates/          # HTML-шаблоны
│   │   ├── base.html       # Базовый шаблон
│   │   ├── broadcast.html  # Страница рассылки
│   │   ├── dashboard.html  # Главная панель
│   │   ├── error.html      # Страница ошибок
│   │   ├── login.html      # Страница входа
│   │   ├── settings.html   # Страница настроек
│   │   ├── user_sites.html # Сайты пользователя
│   │   └── users.html      # Список пользователей
│   ├── auth.py             # Аутентификация и JWT
│   ├── Dockerfile.web      # Docker-файл для веб-приложения
│   ├── requirements.web.txt # Зависимости веб-приложения
│   ├── routers.py          # Маршруты FastAPI
│   └── web_main.py         # Точка входа для веб-приложения
├── logs/
│   └── bot_errors.log      # Логи ошибок
├── .gitignore
├── docker-compose.yml
└── readME.md
```

---

## 🔗 Полезные ссылки

- [Aiogram Documentation](https://docs.aiogram.dev)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy Async Docs](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Celery Documentation](https://docs.celeryq.dev)
- [Docker Compose Reference](https://docs.docker.com/compose/)

---

## 📜 Лицензия

**MIT License** — см. файл [`LICENSE`](./LICENSE).

---

## 🛠️ Устранение неполадок

- **Ошибки бота**: Проверьте `logs/bot_errors.log` для деталей. Администраторы получают уведомления в Telegram.
- **Проблемы с базой данных**: Убедитесь, что `DB_HOST`, `DB_USER`, `DB_PASSWORD` в `.env` совпадают с настройками PostgreSQL.
- **Проблемы с Celery/Redis**: Проверьте доступность Redis (`redis-cli -h redis ping`) и правильность `REDIS_HOST`/`REDIS_PORT`.
- **Веб-панель недоступна**: Убедитесь, что порт 8000 открыт и `docker-compose.yml` настроен корректно.

Для дополнительной помощи свяжитесь с администратором через Telegram (ID из `ADMIN_CHAT_ID`) или создайте issue в репозитории.

## Чтобы скрипт self_destruct.sh работал из контейнера, нужно обеспечить его доступность и права на выполнение.

Размещение скрипта:
```
sudo mkdir -p /home/ubuntu/app/scripts
```
Сохраните self_destruct.sh в /home/ubuntu/app/scripts/self_destruct.sh.
Убедитесь, что скрипт исполняемый:
```
sudo chown 1000:1000 /home/ubuntu/app/scripts/self_destruct.sh
sudo chmod +x /home/ubuntu/app/scripts/self_destruct.sh
```