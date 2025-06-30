# from celery import Celery
# from shared.config import settings
# from shared.logger_setup import logger
# from shared.db import get_system_setting_sync
# from datetime import timedelta
# import os
# import shelve
#
# logger.debug("Инициализация Celery приложения...")
# celery_app = Celery(
#     "website_monitor",
#     broker=f"redis://{settings.redis_host}:{settings.redis_port}/0",
#     backend=f"redis://{settings.redis_host}:{settings.redis_port}/1",
#     include=["bot.monitoring", "bot.celery_app"],
#     broker_connection_retry_on_startup=True,
#     broker_connection_max_retries=15,
#     broker_connection_retry_delay=5,
# )
#
# celery_app.conf.update(
#     task_serializer="json",
#     accept_content=["json"],
#     result_serializer="json",
#     timezone="UTC",
#     enable_utc=True,
#     task_track_started=True,
#     task_time_limit=300,
#     task_soft_time_limit=270,
#     worker_concurrency=8,
#     broker_connection_retry_on_startup=True,
#     worker_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     task_log_format="%(asctime)s - %(name)s - %(levelname)s - Task %(task_name)s[%(task_id)s]: %(message)s",
#     worker_pool_restarts=True,
#     beat_scheduler="celery.beat:PersistentScheduler",
#     beat_schedule_filename="/app/celery_data/celerybeat-schedule",
#     beat_max_loop_interval=30,
#     beat_sync_every=1,
# )
#
# current_check_interval_minutes = None
#
#
# def set_beat_schedule(check_interval_minutes: int):
#     global current_check_interval_minutes
#     if check_interval_minutes == current_check_interval_minutes:
#         logger.debug(f"No change in check_interval_minutes: {check_interval_minutes}")
#         return
#     if check_interval_minutes < 1:
#         logger.error(
#             f"Invalid check_interval_minutes: {check_interval_minutes}. Must be >= 1"
#         )
#         return
#     check_interval = timedelta(minutes=check_interval_minutes)
#     celery_app.conf.beat_schedule = {
#         f"run-monitoring-check-every-{check_interval_minutes}-minutes": {
#             "task": "bot.monitoring.run_monitoring_check",
#             "schedule": check_interval,
#         },
#     }
#     current_check_interval_minutes = check_interval_minutes
#     logger.info(
#         f"Updated Celery Beat schedule with check_interval_minutes={check_interval_minutes}"
#     )
#     logger.debug(f"New Celery Beat schedule: {celery_app.conf.beat_schedule}")
#     # Ensure schedule file is initialized properly
#     schedule_file = celery_app.conf.beat_schedule_filename
#     try:
#         with shelve.open(schedule_file, "c") as db:
#             logger.debug(f"Initialized schedule file: {schedule_file}")
#     except Exception as e:
#         logger.error(
#             f"Failed to initialize schedule file {schedule_file}: {e}", exc_info=True
#         )
#
#
# def initialize_celery_schedule():
#     """Initialize the Celery Beat schedule after database is ready."""
#     logger.info("Initializing Celery schedule...")
#     check_interval_minutes = settings.check_interval_minutes
#     source = ".env"
#     try:
#         result = get_system_setting_sync("check_interval_minutes")
#         if result is not None:
#             check_interval_minutes = int(result)
#             source = "database"
#             logger.info(
#                 f"Fetched check_interval_minutes={check_interval_minutes} from database"
#             )
#         else:
#             logger.info(
#                 "No check_interval_minutes found in database. Using default from .env."
#             )
#     except Exception as e:
#         logger.error(
#             f"Failed to fetch check_interval_minutes from database: {e}", exc_info=True
#         )
#         logger.info(
#             f"Using default check_interval_minutes={check_interval_minutes} from .env"
#         )
#     logger.info(
#         f"Scheduled interval {check_interval_minutes} minute(s) (source: {source})"
#     )
#     set_beat_schedule(check_interval_minutes)
#
#
# @celery_app.task
# def update_check_interval(check_interval_minutes: int):
#     try:
#         logger.info(
#             f"Received task to update check_interval_minutes to {check_interval_minutes}"
#         )
#         set_beat_schedule(check_interval_minutes)
#     except Exception as e:
#         logger.error(f"Error updating check_interval_minutes: {e}", exc_info=True)
#
#
# # Initialize schedule on module load for Celery Beat
# if os.environ.get("RUN_CELERY_BEAT", "0") == "1":
#     logger.debug("Detected Celery Beat process, initializing schedule...")
#     initialize_celery_schedule()
from celery import Celery
from shared.config import settings
from shared.logger_setup import logger
from shared.db import get_system_setting_sync
from datetime import timedelta
import os
import shelve
import traceback
from typing import Optional

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
    beat_scheduler="celery.beat:PersistentScheduler",
    beat_schedule_filename="/app/celery_data/celerybeat-schedule",
    beat_max_loop_interval=30,
    beat_sync_every=1,
)

current_check_interval_minutes = None


class ErrorInfo:
    def __init__(self, exception: Exception, task_name: Optional[str] = None):
        self.exception = exception
        self.exception_name = type(exception).__name__
        self.exception_message = str(exception)
        self.error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.traceback_info = traceback.format_exc()
        self.traceback_snippet = self._format_traceback()
        self.error_location = self._get_error_location()
        self.task_name = task_name

    def _get_error_location(self) -> str:
        if not hasattr(self.exception, "__traceback__"):
            return "❓ Неизвестное местоположение"
        tb = traceback.extract_tb(self.exception.__traceback__)
        if not tb:
            return "❓ Неизвестное местоположение"
        last_call = tb[-1]
        filename = last_call.filename
        line = last_call.lineno
        func = last_call.name
        code_line = last_call.line.strip() if last_call.line else "???"
        return (
            f"📂 <b>Файл:</b> {filename}\n"
            f"📌 <b>Строка:</b> {line}\n"
            f"🔹 <b>Функция:</b> {func}\n"
            f"🖥 <b>Код:</b> <pre>{code_line}</pre>"
        )

    def _format_traceback(self, max_length: int = 2000) -> str:
        tb_lines = self.traceback_info.splitlines()
        snippet = (
            "\n".join(tb_lines[-4:]) if len(tb_lines) >= 4 else self.traceback_info
        )
        if len(snippet) > max_length:
            return snippet[:max_length] + "\n...[сокращено]"
        return snippet


def set_beat_schedule(check_interval_minutes: int):
    global current_check_interval_minutes
    if check_interval_minutes == current_check_interval_minutes:
        logger.debug(f"No change in check_interval_minutes: {check_interval_minutes}")
        return
    if check_interval_minutes < 1:
        logger.error(
            f"Invalid check_interval_minutes: {check_interval_minutes}. Must be >= 1"
        )
        return
    try:
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
        schedule_file = celery_app.conf.beat_schedule_filename
        with shelve.open(schedule_file, "c") as db:
            logger.debug(f"Initialized schedule file: {schedule_file}")
    except Exception as e:
        error_info = ErrorInfo(e, task_name="set_beat_schedule")
        logger.error(
            "Ошибка %s: %s\nМестоположение: %s\nTraceback: %s",
            error_info.exception_name,
            error_info.exception_message,
            error_info.error_location.replace("\n", " | "),
            error_info.traceback_snippet,
        )


def initialize_celery_schedule():
    logger.info("Initializing Celery schedule...")
    check_interval_minutes = settings.check_interval_minutes
    source = ".env"
    try:
        result = get_system_setting_sync("check_interval_minutes")
        if result is not None:
            check_interval_minutes = int(result)
            source = "database"
            logger.info(
                f"Fetched check_interval_minutes={check_interval_minutes} from database"
            )
        else:
            logger.info(
                "No check_interval_minutes found in database. Using default from .env."
            )
        set_beat_schedule(check_interval_minutes)
    except Exception as e:
        error_info = ErrorInfo(e, task_name="initialize_celery_schedule")
        logger.error(
            "Ошибка %s: %s\nМестоположение: %s\nTraceback: %s",
            error_info.exception_name,
            error_info.exception_message,
            error_info.error_location.replace("\n", " | "),
            error_info.traceback_snippet,
        )


@celery_app.task
def update_check_interval(check_interval_minutes: int):
    try:
        logger.info(
            f"Received task to update check_interval_minutes to {check_interval_minutes}"
        )
        set_beat_schedule(check_interval_minutes)
    except Exception as e:
        error_info = ErrorInfo(e, task_name="update_check_interval")
        logger.error(
            "Ошибка %s: %s\nМестоположение: %s\nTraceback: %s",
            error_info.exception_name,
            error_info.exception_message,
            error_info.error_location.replace("\n", " | "),
            error_info.traceback_snippet,
        )


@celery_app.task
def run_monitoring_check():
    logger.info("Running scheduled monitoring check...")
    try:
        from bot.monitoring import check_all_sites_sync

        check_all_sites_sync()
        logger.info("Completed scheduled monitoring check")
    except Exception as e:
        error_info = ErrorInfo(e, task_name="run_monitoring_check")
        logger.error(
            "Ошибка %s: %s\nМестоположение: %s\nTraceback: %s",
            error_info.exception_name,
            error_info.exception_message,
            error_info.error_location.replace("\n", " | "),
            error_info.traceback_snippet,
        )
        raise


if os.environ.get("RUN_CELERY_BEAT", "0") == "1":
    logger.debug("Detected Celery Beat process, initializing schedule...")
    initialize_celery_schedule()
