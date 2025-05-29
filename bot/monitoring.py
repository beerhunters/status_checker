# bot/monitoring.py
from shared.models import Site, User
from shared.utils import check_website_sync, send_notification_sync
from shared.config import settings
from shared.logger_setup import logger
from bot.celery_app import celery_app
from sqlalchemy import update, func
from sqlalchemy.future import select
from celery import shared_task


def check_single_site_sync(site: Site, user: User) -> bool:
    logger.debug(f"Checking site: {site.url} for user: {user.telegram_id}")
    is_available = check_website_sync(site.url)
    from sqlalchemy.orm import Session
    from shared.db import SyncSessionFactory

    with SyncSessionFactory() as session:
        session.execute(
            update(Site)
            .where(Site.id == site.id, Site.user_id == user.id)
            .values(is_available=is_available, last_checked=func.now())
        )
        session.commit()
    if site.is_available != is_available:
        status_text = "доступен" if is_available else "недоступен"
        status_tag = "✅" if is_available else "❌"
        message = f"{status_tag} Статус сайта <b>{site.url}</b> изменился: теперь <b>{status_text}</b>."
        send_notification_sync(user.telegram_id, message)
    return is_available


def check_all_sites_sync():
    logger.debug("Starting check for all sites...")
    from sqlalchemy.orm import Session
    from shared.db import SyncSessionFactory

    with SyncSessionFactory() as session:
        stmt = select(User.telegram_id)
        result = session.execute(stmt)
        user_ids = [row for row in result.scalars().all()]
    if not user_ids:
        logger.info("No users found for monitoring")
        return
    with SyncSessionFactory() as session:
        for user_id in user_ids:
            stmt = select(User).filter(User.telegram_id == user_id)
            result = session.execute(stmt)
            user = result.scalars().first()
            if not user:
                logger.warning(f"User {user_id} not found, skipping.")
                continue
            stmt = (
                select(Site)
                .join(User)
                .filter(User.telegram_id == user_id)
                .order_by(Site.id)
            )
            result = session.execute(stmt)
            sites = result.scalars().all()
            for site in sites:
                try:
                    is_available = check_single_site_sync(site, user)
                    logger.debug(
                        f"Site {site.url} for user {user_id} is "
                        f"{'available' if is_available else 'unavailable'}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error checking site {site.url} for user {user_id}: {e}",
                        exc_info=True,
                    )


@shared_task
@celery_app.task
def run_monitoring_check():
    logger.info("Running scheduled monitoring check...")
    try:
        check_all_sites_sync()
        logger.info("Completed scheduled monitoring check")
    except Exception as e:
        logger.error(f"Error in run_monitoring_check: {e}", exc_info=True)
        raise
