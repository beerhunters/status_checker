# # # bot/monitoring.py
# # from shared.models import Site, User
# # from shared.utils import check_website_sync, send_notification_sync
# # from shared.config import settings
# # from shared.logger_setup import logger
# # from bot.celery_app import celery_app
# # from sqlalchemy import update, func
# # from sqlalchemy.future import select
# # from celery import shared_task
# #
# #
# # def check_single_site_sync(site: Site, user: User) -> bool:
# #     logger.debug(f"Checking site: {site.url} for user: {user.telegram_id}")
# #     is_available = check_website_sync(site.url)
# #     from sqlalchemy.orm import Session
# #     from shared.db import SyncSessionFactory
# #
# #     with SyncSessionFactory() as session:
# #         session.execute(
# #             update(Site)
# #             .where(Site.id == site.id, Site.user_id == user.id)
# #             .values(is_available=is_available, last_checked=func.now())
# #         )
# #         session.commit()
# #     if site.is_available != is_available:
# #         status_text = "доступен" if is_available else "недоступен"
# #         status_tag = "✅" if is_available else "❌"
# #         message = f"{status_tag} Статус сайта <b>{site.url}</b> изменился: теперь <b>{status_text}</b>."
# #         send_notification_sync(user.telegram_id, message)
# #     return is_available
# #
# #
# # def check_all_sites_sync():
# #     logger.debug("Starting check for all sites...")
# #     from sqlalchemy.orm import Session
# #     from shared.db import SyncSessionFactory
# #
# #     with SyncSessionFactory() as session:
# #         stmt = select(User.telegram_id)
# #         result = session.execute(stmt)
# #         user_ids = [row for row in result.scalars().all()]
# #     if not user_ids:
# #         logger.info("No users found for monitoring")
# #         return
# #     with SyncSessionFactory() as session:
# #         for user_id in user_ids:
# #             stmt = select(User).filter(User.telegram_id == user_id)
# #             result = session.execute(stmt)
# #             user = result.scalars().first()
# #             if not user:
# #                 logger.warning(f"User {user_id} not found, skipping.")
# #                 continue
# #             stmt = (
# #                 select(Site)
# #                 .join(User)
# #                 .filter(User.telegram_id == user_id)
# #                 .order_by(Site.id)
# #             )
# #             result = session.execute(stmt)
# #             sites = result.scalars().all()
# #             for site in sites:
# #                 try:
# #                     is_available = check_single_site_sync(site, user)
# #                     logger.debug(
# #                         f"Site {site.url} for user {user_id} is "
# #                         f"{'available' if is_available else 'unavailable'}"
# #                     )
# #                 except Exception as e:
# #                     logger.error(
# #                         f"Error checking site {site.url} for user {user_id}: {e}",
# #                         exc_info=True,
# #                     )
# #
# #
# # @shared_task
# # @celery_app.task
# # def run_monitoring_check():
# #     logger.info("Running scheduled monitoring check...")
# #     try:
# #         check_all_sites_sync()
# #         logger.info("Completed scheduled monitoring check")
# #     except Exception as e:
# #         logger.error(f"Error in run_monitoring_check: {e}", exc_info=True)
# #         raise
# import logging
# from typing import List
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
# from shared.db import AsyncSessionFactory
# from shared.models import User, Site
# from shared.monitoring import check_website_async
# from shared.utils import send_notification_async
# from bot.celery_app import celery_app, ErrorInfo
# from sqlalchemy import update, func
# from sqlalchemy.future import select
# from celery import shared_task
#
# logger = logging.getLogger("WebsiteMonitorBot")
#
#
# async def check_single_site_async(
#     site: Site, user: User, session: AsyncSession
# ) -> bool:
#     """
#     Проверяет доступность одного сайта асинхронно и отправляет уведомление, если статус изменился.
#
#     Args:
#         site: Объект сайта из базы данных.
#         user: Объект пользователя из базы данных.
#         session: Асинхронная сессия SQLAlchemy.
#
#     Returns:
#         bool: True, если сайт доступен, иначе False.
#     """
#     try:
#         is_available = await check_website_async(site.url)
#         if site.is_available != is_available:
#             site.is_available = is_available
#             status_text = "доступен" if is_available else "недоступен"
#             status_tag = "✅" if is_available else "❌"
#             message = f"{status_tag} Статус сайта <b>{site.url}</b> изменился: теперь <b>{status_text}</b>."
#             await send_notification_async(user.telegram_id, message)
#             logger.info(
#                 f"Site {site.url} status changed to {status_text} for user {user.telegram_id}"
#             )
#         return is_available
#     except Exception as e:
#         logger.error(f"Error checking site {site.url}: {str(e)}")
#         return False
#
#
# async def check_all_sites_async() -> None:
#     """
#     Проверяет доступность всех сайтов для всех пользователей асинхронно.
#     """
#     async with AsyncSessionFactory() as session:
#         try:
#             stmt = select(User.telegram_id)
#             result = await session.execute(stmt)
#             user_ids = [row for row in result.scalars().all()]
#
#             for user_id in user_ids:
#                 stmt = select(User).filter(User.telegram_id == user_id)
#                 result = await session.execute(stmt)
#                 user = result.scalars().first()
#                 if not user:
#                     logger.warning(f"User with telegram_id {user_id} not found")
#                     continue
#
#                 stmt = select(Site).filter(Site.user_id == user.id)
#                 result = await session.execute(stmt)
#                 sites = result.scalars().all()
#
#                 for site in sites:
#                     await check_single_site_async(site, user, session)
#
#                 # Фиксация изменений для каждого пользователя
#                 await session.commit()
#         except Exception as e:
#             logger.error(f"Error in check_all_sites_async: {str(e)}")
#             await session.rollback()
#
#
# @shared_task
# @celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
# async def run_monitoring_check(self) -> None:
#     """
#     Celery-задача для периодической проверки всех сайтов.
#
#     Args:
#         self: Экземпляр задачи Celery (для поддержки ретраев).
#     """
#     try:
#         await check_all_sites_async()
#     except Exception as e:
#         logger.error(f"Error in run_monitoring_check: {str(e)}")
#         error_info = ErrorInfo(e, task_name="run_monitoring_check")
#         logger.error(error_info._format_traceback())
#         raise self.retry(exc=e)  # Повтор при ошибке
# Изменения: Переход на APScheduler, убраны ссылки на Celery
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
