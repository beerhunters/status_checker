# # Новый файл: Настройка APScheduler для периодических проверок сайтов
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
# from shared.config import settings
# from bot.monitoring import check_all_sites_async
# from shared.db import sync_engine
# import logging
#
# logger = logging.getLogger("WebsiteMonitorBot")
#
#
# async def setup_scheduler(bot) -> None:
#     try:
#         # Настройка хранилища заданий в SQLite
#         job_stores = {
#             "default": SQLAlchemyJobStore(
#                 url=settings.database_url_sync, engine=sync_engine
#             )
#         }
#         scheduler = AsyncIOScheduler(jobstores=job_stores)
#         # Добавление задачи проверки сайтов
#         scheduler.add_job(
#             check_all_sites_async,
#             trigger="interval",
#             minutes=settings.check_interval_minutes,
#             id="site_check",
#             replace_existing=True,
#         )
#         scheduler.start()
#         logger.info(
#             "Scheduler started with interval %s minutes",
#             settings.check_interval_minutes,
#         )
#     except Exception as e:
#         logger.error(f"Error setting up scheduler: {str(e)}")
# Изменения: Добавлена периодическая проверка настройки check_interval_minutes и обновление расписания
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from shared.config import settings
from shared.db import sync_engine, get_system_setting, set_system_setting
from bot.monitoring import check_all_sites_async
import logging
import asyncio

logger = logging.getLogger("WebsiteMonitorBot")


async def update_schedule_interval(scheduler: AsyncIOScheduler) -> None:
    """Периодически проверяет настройку check_interval_minutes и обновляет расписание."""
    try:
        current_interval = await get_system_setting("check_interval_minutes")
        if not current_interval:
            current_interval = settings.check_interval_minutes
            await set_system_setting("check_interval_minutes", current_interval)

        job = scheduler.get_job("site_check")
        if job and job.trigger.interval.seconds != current_interval * 60:
            scheduler.reschedule_job(
                job_id="site_check", trigger="interval", minutes=current_interval
            )
            logger.info(f"Updated site_check interval to {current_interval} minutes")
    except Exception as e:
        logger.error(f"Error updating schedule interval: {str(e)}")


async def setup_scheduler(bot) -> None:
    try:
        # Настройка хранилища заданий в SQLite
        job_stores = {
            "default": SQLAlchemyJobStore(
                url=settings.database_url_sync, engine=sync_engine
            )
        }
        scheduler = AsyncIOScheduler(jobstores=job_stores)
        # Добавление задачи проверки сайтов
        scheduler.add_job(
            check_all_sites_async,
            trigger="interval",
            minutes=settings.check_interval_minutes,
            id="site_check",
            replace_existing=True,
        )
        # Добавление задачи проверки интервала
        scheduler.add_job(
            update_schedule_interval,
            trigger="interval",
            seconds=30,  # Проверять каждые 30 секунд
            args=[scheduler],
            id="interval_check",
            replace_existing=True,
        )
        scheduler.start()
        logger.info(
            "Scheduler started with site_check interval %s minutes",
            settings.check_interval_minutes,
        )
    except Exception as e:
        logger.error(f"Error setting up scheduler: {str(e)}")
