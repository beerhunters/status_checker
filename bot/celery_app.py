# bot/celery_app.py

import bot.patch_eventlet  # Патчим eventlet первым
from celery import Celery
from shared.config import settings
from shared.logger_setup import logger

logger.debug("Инициализация Celery приложения")

celery_app = Celery(
    "website_monitor",
    broker=f"redis://{settings.redis_host}:{settings.redis_port}/0",
    backend=f"redis://{settings.redis_host}:{settings.redis_port}/0",
    include=["bot.monitoring"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=270,
    worker_concurrency=100,
    broker_connection_retry_on_startup=True,
    worker_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    task_log_format="%(asctime)s - %(name)s - %(levelname)s - Task %(task_name)s[%(task_id)s]: %(message)s",
)

celery_app.conf.beat_schedule = {
    "run-monitoring-check-every-5-minutes": {
        "task": "bot.monitoring.run_monitoring_check",
        "schedule": settings.check_interval_minutes * 60.0,
    }
}

logger.debug("Celery настроен")
