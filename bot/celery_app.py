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
    include=["bot.monitoring", "bot.celery_app"],
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=15,
    broker_connection_retry_delay=5,
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
    worker_concurrency=8,
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
    if check_interval_minutes < 1:
        logger.error(
            f"Invalid check_interval_minutes: {check_interval_minutes}. Must be >= 1"
        )
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
check_interval_minutes = settings.check_interval_minutes
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


# from celery import Celery
# from celery.schedules import crontab
# from shared.config import settings
# from shared.logger_setup import logger
# from shared.db import get_system_setting_sync
#
# logger.info("Initializing Celery app...")
# celery_app = Celery(
#     "monitoring_bot",
#     broker=settings.redis_url,
#     backend=settings.redis_url,
#     include=["bot.monitoring", "bot.celery_app"],
# )
#
# celery_app.conf.update(
#     task_serializer="json",
#     accept_content=["json"],
#     result_serializer="json",
#     timezone="UTC",
#     enable_utc=True,
#     task_track_started=True,
#     task_create_missing_queues=True,
#     task_default_queue="monitoring_queue",
#     task_always_eager=False,
#     task_ignore_result=False,
#     task_store_errors_even_if_ignored=True,
# )
#
#
# def configure_beat_schedule():
#     """Configure Celery Beat schedule based on system settings."""
#     check_interval = get_system_setting_sync("check_interval_minutes")
#     if check_interval is None:
#         check_interval = settings.check_interval_minutes
#         logger.warning(
#             f"No check_interval_minutes found in database. Using default from .env: {check_interval}"
#         )
#     else:
#         logger.info(
#             f"check_interval_minutes set to {check_interval} (source: database)"
#         )
#
#     celery_app.conf.beat_schedule = {
#         f"run-monitoring-check-every-{check_interval}-minutes": {
#             "task": "bot.monitoring.run_monitoring_check",
#             "schedule": crontab(minute=f"*/{check_interval}"),
#         }
#     }
#     logger.info(
#         f"Updated Celery Beat schedule with check_interval_minutes={check_interval}"
#     )
#
#
# logger.info("Celery app initialized.")
#
# # Вызываем configure_beat_schedule при инициализации для beat
# if celery_app.conf.get("CELERY_BEAT_SCHEDULE") is None:
#     configure_beat_schedule()
#
#
# @celery_app.task
# def update_check_interval(minutes: int):
#     from shared.db import get_system_setting_sync, set_system_setting
#     from celery.schedules import crontab
#
#     logger.info(f"Received task to update_check_interval_minutes to {minutes}")
#     try:
#         current_interval = get_system_setting_sync("check_interval_minutes")
#         if current_interval != minutes:
#             logger.info(
#                 f"Updating check_interval_minutes from {current_interval} to {minutes}"
#             )
#             set_system_setting("check_interval_minutes", minutes)
#             celery_app.conf.beat_schedule = {
#                 f"run-monitoring-check-every-{minutes}-minutes": {
#                     "task": "bot.monitoring.run_monitoring_check",
#                     "schedule": crontab(minute=f"*/{minutes}"),
#                 }
#             }
#             logger.info(
#                 f"Updated Celery Beat schedule with check_interval_minutes={minutes}"
#             )
#         else:
#             logger.info(
#                 f"check_interval_minutes is already {minutes}, no update needed"
#             )
#     except Exception as e:
#         logger.error(f"Error updating check interval: {e}", exc_info=True)
#         raise
