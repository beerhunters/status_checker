# bot/celery_app.py
import bot.patch_eventlet  # Must be first import
from celery import Celery
from shared.config import settings
from shared.logger_setup import logger
from shared.db import get_system_setting_sync
from datetime import timedelta

logger.debug("Инициализация Celery приложения...")
celery_app = Celery(
    "website_monitor",
    broker=f"redis://{settings.redis_host}:{settings.redis_port}/0",
    backend=f"redis://{settings.redis_host}:{settings.redis_port}/1",
    include=["bot.monitoring", "bot.celery_app"],  # Include this module for tasks
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
    worker_concurrency=20,
    broker_connection_retry_on_startup=True,
    worker_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    task_log_format="%(asctime)s - %(name)s - %(levelname)s - Task %(task_name)s[%(task_id)s]: %(message)s",
    worker_pool_restarts=True,
)

# Global variable to track current interval
current_check_interval_minutes = None


def set_beat_schedule(check_interval_minutes: int):
    """Sets the Celery Beat schedule based on check_interval_minutes."""
    global current_check_interval_minutes
    if check_interval_minutes == current_check_interval_minutes:
        logger.debug(f"No change in check_interval_minutes: {check_interval_minutes}")
        return
    check_interval = timedelta(minutes=check_interval_minutes)
    celery_app.conf.beat_schedule = {
        f"run-monitoring-check-every-{check_interval_minutes}-minutes": {
            "task": "bot.monitoring.run_monitoring_check",
            "schedule": check_interval,
        },
    }
    current_check_interval_minutes = check_interval_minutes
    logger.info(
        f"Updated Celery Beat schedule with check_interval_minutes={check_interval_minutes}"
    )
    logger.debug(f"New Celery Beat schedule: {celery_app.conf.beat_schedule}")


# Fetch initial check_interval_minutes from database
check_interval_minutes = settings.check_interval_minutes  # Default fallback
source = ".env"
try:
    result = get_system_setting_sync("check_interval_minutes")
    if result is not None:
        check_interval_minutes = result
        source = "database"
    else:
        logger.warning(
            "No check_interval_minutes found in database. Using default from .env."
        )
except Exception as e:
    logger.error(
        f"Failed to fetch check_interval_minutes from database: {e}", exc_info=True
    )
    logger.info(
        f"Using default check_interval_minutes={check_interval_minutes} from .env."
    )

logger.info(
    f"check_interval_minutes set to {check_interval_minutes} (source: {source})"
)
set_beat_schedule(check_interval_minutes)


@celery_app.task
def update_check_interval(check_interval_minutes: int):
    """Task to update check_interval_minutes in Celery Beat schedule."""
    try:
        logger.info(
            f"Received task to update check_interval_minutes to {check_interval_minutes}"
        )
        set_beat_schedule(check_interval_minutes)
    except Exception as e:
        logger.error(f"Error updating check_interval_minutes: {e}", exc_info=True)
