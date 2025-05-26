# Website Monitoring Bot

## 📌 Описание проекта

Приложение для мониторинга доступности сайтов и отправки уведомлений в Telegram.  
Включает веб-панель администратора для просмотра пользователей и их сайтов.

---

## 🧱 Архитектура

Проект состоит из следующих компонентов:

- **Telegram-бот (`bot/`)** — команды от пользователей, добавление/удаление сайтов, уведомления.
- **Веб-панель администратора (`web/`)** — интерфейс для управления пользователями и сайтами.
- **PostgreSQL** — база данных пользователей и сайтов.
- **Redis** — брокер задач Celery.
- **Celery** — фоновая проверка сайтов по расписанию.

---

## ⚙️ Возможности

### Для пользователей (через Telegram):

- ➕ Добавление сайтов для мониторинга
- ❌ Удаление сайтов
- 📢 Получение уведомлений о недоступности

### Для администратора (веб-интерфейс):

- 👤 Просмотр всех пользователей
- 🌐 Просмотр сайтов конкретного пользователя
- 🔄 Обновление статуса сайта вручную
- 🗑 Удаление сайтов

---

## 🔄 Как это работает

1. Пользователь взаимодействует с Telegram-ботом с помощью кнопок:
   - `/start` — начать работу
   - «➕ Добавить сайт» — добавить новый сайт
   - «🌐 Мои сайты» — список и управление

2. Данные сохраняются в PostgreSQL через SQLAlchemy (async).

3. Задача Celery (`run_monitoring_check`) запускается каждые `CHECK_INTERVAL_MINUTES` минут и проверяет все сайты.

4. Если сайт недоступен — отправляется уведомление владельцу.

5. Веб-панель (`web/`) предоставляет:
   - 🔐 Аутентификацию по логину/паролю
   - ✅ JWT-авторизацию
   - 📄 Интерфейс для просмотра/удаления сайтов

---

## 🛠️ Технологии

- **Python 3.10**
- **Aiogram 3.x** — Telegram-бот
- **FastAPI** — веб-панель
- **SQLAlchemy + asyncpg** — работа с PostgreSQL
- **aiohttp** — проверка сайтов
- **Jinja2** — шаблоны
- **Celery + Redis** — фоновые задачи
- **Docker / Docker Compose** — контейнеризация

---

## 🚀 Настройка и запуск

### 1. Подготовка окружения

Создайте `.env` файл в корне проекта:

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
JWT_SECRET_KEY=your-secure-random-key-here
LOG_LEVEL=INFO
```

### 2. Запуск через Docker Compose

Убедитесь, что установлены:

- Docker
- Docker Compose

Запустите проект:

```bash
docker-compose up -d --build
```

После запуска:

- Бот начнет слушать сообщения.
- Фоновая проверка стартует каждые 5 минут.
- Веб-панель будет доступна по адресу: [http://localhost:8000/login](http://localhost:8000/login)

---

## 👥 Использование

### Для пользователей:

1. Откройте Telegram и начните чат с ботом.
2. Нажмите `/start`.
3. Используйте меню для добавления/удаления сайтов.

### Для администратора:

1. Перейдите по адресу: [http://localhost:8000/login](http://localhost:8000/login)
2. Введите логин/пароль из `.env`.
3. Просматривайте и управляйте пользователями и сайтами.

---

## 📁 Структура проекта

```
├── bot/
│   ├── bot_main.py         # Точка входа для бота
│   ├── celery_app.py       # Настройка Celery
│   ├── Dockerfile.bot      # Docker-файл для бота
│   ├── fsm.py              # FSM для добавления сайта
│   ├── handlers.py         # Логика обработки команд
│   ├── keyboards.py        # Inline-клавиатуры
│   ├── monitoring.py       # Фоновая проверка сайтов
│   └── requirements.bot.txt
├── shared/
│   ├── config.py           # Настройки приложения
│   ├── db.py               # Работа с базой данных
│   ├── logger_setup.py     # Логирование
│   ├── models.py           # Модели SQLAlchemy
│   └── monitoring.py       # Логика проверки доступности сайтов
├── web/
│   ├── templates/          # HTML-шаблоны
│   │   ├── base.html
│   │   ├── error.html
│   │   ├── login.html
│   │   ├── user_sites.html
│   │   └── users.html
│   ├── auth.py             # Авторизация
│   ├── Dockerfile.web      # Docker-файл для веб-приложения
│   ├── requirements.web.txt
│   ├── routers.py          # Роуты веб-панели
│   └── web_main.py         # Точка входа для веба
├── .gitignore
└── docker-compose.yml
```

---

## 🔗 Полезные ссылки

- [Aiogram Documentation](https://docs.aiogram.dev)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy Async Docs](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Celery Documentation](https://docs.celeryq.dev)
- [Docker Compose Reference](https://docs.docker.com/compose/)

---

## 📄 Лицензия

**MIT License** — см. файл [`LICENSE`](./LICENSE).

---

Если потребуется дополнительная документация, интеграции или доработка — дайте знать!