# bot/celery_app.py
# ВАЖНО: Патчинг должен быть выполнен ПЕРЕД импортом других библиотек!
import bot.patch_eventlet

from celery import Celery
from shared.config import settings
from shared.logger_setup import logger
from datetime import timedelta

logger.debug("Инициализация Celery приложения...")

celery_app = Celery(
    "website_monitor",
    broker=f"redis://{settings.redis_host}:{settings.redis_port}/0",
    backend=f"redis://{settings.redis_host}:{settings.redis_port}/1",  # Используем другую БД для результатов
    include=["bot.monitoring"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 минут - жесткий лимит
    task_soft_time_limit=270,  # 4.5 минуты - мягкий лимит
    # worker_concurrency=100, # Очень высокое значение, рекомендуется начать с меньшего (e.g., 10-20) и настроить
    worker_concurrency=20,  # Более разумное значение для начала
    broker_connection_retry_on_startup=True,
    worker_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    task_log_format="%(asctime)s - %(name)s - %(levelname)s - Task %(task_name)s[%(task_id)s]: %(message)s",
    # Важно для eventlet, чтобы избежать проблем с блокировкой
    worker_pool_restarts=True,
    # broker_transport_options = {'visibility_timeout': 3600}, # Можно увеличить таймаут видимости
)

# Используем timedelta для расписания
check_interval = timedelta(minutes=settings.check_interval_minutes)

celery_app.conf.beat_schedule = {
    f"run-monitoring-check-every-{settings.check_interval_minutes}-minutes": {
        "task": "bot.monitoring.run_monitoring_check",
        "schedule": check_interval,
    }
}

logger.info(
    f"Celery настроен. Интервал проверки: {settings.check_interval_minutes} минут."
)
logger.debug(f"Celery Beat schedule: {celery_app.conf.beat_schedule}")
