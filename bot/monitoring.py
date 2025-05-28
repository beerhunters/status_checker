# bot/monitoring.py
import asyncio
from typing import List, Optional
from shared.db import (
    AsyncSessionFactory,
    get_all_telegram_ids,  # Заменено
    get_user_sites,
    update_site_status,
    get_user_by_id,
)
from shared.models import Site, User
from shared.utils import check_website_sync, send_notification_sync
from shared.config import settings
from shared.logger_setup import logger
from bot.celery_app import celery_app  # Исправленный импорт


async def check_single_site(site: Site, user: User) -> bool:
    logger.debug(f"Checking site: {site.url} for user: {user.telegram_id}")
    is_available = check_website_sync(site.url)
    async with AsyncSessionFactory() as session:
        await update_site_status(
            session,
            site_id=site.id,
            is_available=is_available,
            user_id=user.telegram_id,
        )
    if site.is_available != is_available:
        status_text = "доступен" if is_available else "недоступен"
        message = (
            f"Статус сайта <b>{site.url}</b> изменился: теперь <b>{status_text}</b>."
        )
        send_notification_sync(user.telegram_id, message)
    return is_available


async def check_all_sites():
    logger.debug("Starting check for all sites...")
    async with AsyncSessionFactory() as session:
        user_ids = await get_all_telegram_ids(session)  # Заменено
        for user_id in user_ids:
            user = await get_user_by_id(session, user_id)
            if not user:
                logger.warning(f"User {user_id} not found, skipping.")
                continue
            sites = await get_user_sites(session, user_id)
            tasks = [check_single_site(site, user) for site in sites]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for site, result in zip(sites, results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Error checking site {site.url} for user {user_id}: {result}",
                        exc_info=True,
                    )
                else:
                    logger.debug(
                        f"Site {site.url} for user {user_id} is "
                        f"{'available' if result else 'unavailable'}"
                    )


@celery_app.task
def run_monitoring_check():
    logger.info("Running scheduled monitoring check...")
    try:
        asyncio.run(check_all_sites())
    except Exception as e:
        logger.error(f"Error in run_monitoring_check: {e}", exc_info=True)
