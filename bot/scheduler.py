import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from shared.config import settings
from shared.db import get_system_setting
from bot.monitoring import check_all_sites_async

logger = logging.getLogger("WebsiteMonitorBot")


async def update_schedule_interval(scheduler: AsyncIOScheduler) -> None:
    current_interval = await get_system_setting("check_interval_minutes")
    if not current_interval:
        current_interval = settings.check_interval_minutes
    job = scheduler.get_job("site_check")
    if job:
        scheduler.reschedule_job(
            "site_check", trigger="interval", minutes=current_interval
        )
        logger.info(
            f"Rescheduled site_check job to run every {current_interval} minutes"
        )
    else:
        logger.warning("No site_check job found to reschedule")


async def setup_scheduler(bot) -> None:
    job_stores = {"default": {"type": "memory"}}
    scheduler = AsyncIOScheduler(jobstores=job_stores)
    scheduler.add_job(
        check_all_sites_async,
        "interval",
        minutes=settings.check_interval_minutes,
        id="site_check",
        kwargs={"bot": bot},
    )
    scheduler.start()
    logger.info("Scheduler started with site_check job")
