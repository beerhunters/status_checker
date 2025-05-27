# bot/monitoring.py
import time
from celery import shared_task
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from shared.db import SyncSessionFactory
from shared.logger_setup import logger
from shared.models import Site, User
from sqlalchemy.future import select
from shared.utils import check_website_sync, send_notification_sync  # Updated import


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def check_single_site(self, site_id: int, url: str, telegram_id: int):
    """Celery task to check a single site."""
    logger.debug(
        f"Running Celery task for site ID={site_id}, URL={url}, telegram_id={telegram_id}"
    )
    with SyncSessionFactory() as session:
        try:
            site = session.get(Site, site_id)
            if not site:
                logger.warning(f"Site ID={site_id} not found in Celery task.")
                return
            was_available = site.is_available
            is_available = check_website_sync(url)
            now = datetime.now(timezone.utc)
            logger.debug(
                f"Site ID={site_id}: was_available={was_available}, is_available={is_available}, last_notified={site.last_notified}"
            )
            send_alert = False
            if was_available and not is_available:
                send_alert = True
                logger.info(
                    f"Site {url} (ID={site_id}) became unavailable. Setting send_alert=True."
                )
                site.last_notified = now
            elif not is_available and (
                site.last_notified is None
                or (now - site.last_notified).total_seconds() > 900
            ):
                send_alert = True
                logger.info(
                    f"Site {url} (ID={site_id}) unavailable, and no notification sent or >15 min passed. Setting send_alert=True."
                )
                site.last_notified = now
            site.is_available = is_available
            site.last_checked = now
            session.commit()
            logger.debug(f"Site ID={site_id}: send_alert={send_alert}")
            if send_alert:
                logger.info(
                    f"Site {url} (ID={site_id}) unavailable. Sending notification to user {telegram_id}..."
                )
                send_notification_sync(
                    telegram_id, f"🚨 Внимание! Ваш сайт {url} недоступен!"
                )
            else:
                logger.debug(
                    f"No notification sent for site {url} (ID={site_id}): send_alert=False"
                )
        except requests.RequestException as exc:
            logger.warning(f"Network error checking {url}, retrying... ({exc})")
            raise self.retry(exc=exc)
        except Exception as e:
            logger.error(
                f"Unexpected error processing site {site_id}: {e}", exc_info=True
            )


@shared_task
def run_monitoring_check():
    """Task to run monitoring for all sites."""
    logger.info("Starting periodic task run_monitoring_check...")
    with SyncSessionFactory() as session:
        try:
            stmt = select(Site.id, Site.url, User.telegram_id).join(
                User, Site.user_id == User.id
            )
            sites = session.execute(stmt).fetchall()
            logger.info(f"Found {len(sites)} sites to check.")
            for site_id, url, telegram_id in sites:
                check_single_site.delay(site_id, url, telegram_id)
            logger.info("Site check tasks successfully queued.")
        except Exception as e:
            logger.error(
                f"Error fetching site list for monitoring: {e}",
                exc_info=True,
            )
