# import asyncio
# from celery import shared_task
#
# from shared.db import get_all_sites_with_users
# from shared.logger_setup import logger
# from shared.monitoring import update_site_availability
#
#
# @shared_task
# def run_monitoring_check():
#     """Fetches all sites, checks their status, updates is_available, and notifies on failure."""
#     logger.info("Starting monitoring check run...")
#
#     async def run():
#         try:
#             sites = await get_all_sites_with_users()
#         except Exception as e:
#             logger.error(f"Failed to fetch sites for monitoring: {e}")
#             return
#
#         async with get_all_sites_with_users.session_factory() as session:
#             for site in sites:
#                 if not site.user:
#                     logger.error(
#                         f"Site {site.id} ({site.url}) has no associated user, skipping."
#                     )
#                     continue
#
#                 is_available = await update_site_availability(
#                     session, site.id, site.url
#                 )
#                 if not is_available:
#                     logger.warning(
#                         f"Site {site.url} (User: {site.user.telegram_id}) is DOWN!"
#                     )
#                     from bot.bot_main import send_notification
#
#                     await send_notification(
#                         site.user.telegram_id,
#                         f"🚨 Внимание! Ваш сайт {site.url} недоступен!",
#                     )
#
#         logger.info("Monitoring check run finished.")
#
#     # Запускаем асинхронную задачу в Celery
#     asyncio.run(run())
from celery import shared_task
from shared.db import get_all_sites_with_users, AsyncSessionFactory
from shared.logger_setup import logger
from shared.monitoring import update_site_availability


@shared_task(bind=True)
async def run_monitoring_check(self):
    """Fetches all sites, checks their status, updates is_available, and notifies on failure."""
    logger.info("Starting monitoring check run...")

    async with AsyncSessionFactory() as session:
        try:
            sites = await get_all_sites_with_users()
            logger.debug(f"Fetched {len(sites)} sites for monitoring")
        except Exception as e:
            logger.error(f"Failed to fetch sites for monitoring: {e}")
            return

        for site in sites:
            if not site.user:
                logger.error(
                    f"Site {site.id} ({site.url}) has no associated user, skipping."
                )
                continue

            try:
                is_available = await update_site_availability(
                    session, site.id, site.url
                )
                logger.debug(
                    f"Checked site {site.id} ({site.url}): {'available' if is_available else 'unavailable'}"
                )
                if not is_available:
                    logger.warning(
                        f"Site {site.url} (User: {site.user.telegram_id}) is DOWN!"
                    )
                    from bot.bot_main import send_notification

                    try:
                        await send_notification(
                            site.user.telegram_id,
                            f"🚨 Внимание! Ваш сайт {site.url} недоступен!",
                        )
                        logger.info(
                            f"Sent notification to user {site.user.telegram_id} for site {site.url}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to send notification for site {site.url}: {e}"
                        )
            except Exception as e:
                logger.error(f"Error processing site {site.id} ({site.url}): {e}")

    logger.info("Monitoring check run finished.")
