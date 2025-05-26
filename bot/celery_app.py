from celery import Celery
from shared.config import settings
from shared.logger_setup import logger

celery_app = Celery(
    "website_monitor",
    broker=f"redis://{settings.redis_host}:{settings.redis_port}/0",
    backend=f"redis://{settings.redis_host}:{settings.redis_port}/0",
    include=["bot.monitoring", "bot.bot_main"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "run-monitoring-check-every-5-minutes": {
        "task": "bot.monitoring.run_monitoring_check",
        "schedule": settings.check_interval_minutes * 60.0,
    }
}
