from shared.models import User, Site
from shared.db import AsyncSessionFactory, get_user_sites, get_all_telegram_ids
from shared.monitoring import check_website_async
from shared.utils import send_notification_async
import logging

logger = logging.getLogger("WebsiteMonitorBot")


async def check_all_sites_async() -> None:
    async with AsyncSessionFactory() as session:
        try:
            telegram_ids = await get_all_telegram_ids()
            for user_id in telegram_ids:
                sites = await get_user_sites(user_id)
                for site in sites:
                    is_available = await check_website_async(site.url)
                    if site.is_available != is_available:
                        site.is_available = is_available
                        site.last_notified = None  # Сброс для уведомления
                        status_text = "доступен" if is_available else "недоступен"
                        status_tag = "✅" if is_available else "❌"
                        message = f"{status_tag} Статус сайта <b>{site.url}</b> изменился: теперь <b>{status_text}</b>."
                        await send_notification_async(user_id, message)
                        await session.commit()
        except Exception as e:
            logger.error(f"Error in check_all_sites_async: {str(e)}")
