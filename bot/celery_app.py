from celery import Celery
from shared.config import settings

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
    beat_schedule={
        "run-monitoring-check": {
            "task": "bot.monitoring.run_monitoring_check",
            "schedule": settings.check_interval_minutes * 60,  # В секундах
        },
    },
)

# Автообнаружение задач
celery_app.autodiscover_tasks(["bot"])
