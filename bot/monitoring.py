# import asyncio
# import aiohttp
# from typing import Callable
#
# from shared.db import get_all_sites_with_users
# from shared.logger_setup import logger
#
#
# async def check_website(url: str) -> bool:
#     """Checks if a website returns a 2xx status code."""
#     try:
#         # Устанавливаем User-Agent, чтобы избежать блокировок
#         headers = {"User-Agent": "WebsiteMonitorBot/1.0 (+https://yourbot.info)"}
#         async with aiohttp.ClientSession(
#             timeout=aiohttp.ClientTimeout(total=15), headers=headers
#         ) as session:
#             async with session.get(
#                 url, allow_redirects=True, ssl=False
#             ) as response:  # ssl=False - может помочь с некоторыми сайтами
#                 logger.debug(f"Checked {url}, status: {response.status}")
#                 return 200 <= response.status < 300
#     except aiohttp.ClientConnectorError as e:
#         logger.warning(f"Connection error checking {url}: {e}")
#         return False
#     except aiohttp.ClientError as e:
#         logger.warning(f"Client error checking {url}: {e}")
#         return False
#     except asyncio.TimeoutError:
#         logger.warning(f"Timeout checking {url}")
#         return False
#     except Exception as e:
#         logger.error(f"Unexpected error checking {url}: {type(e).__name__} - {e}")
#         return False
#
#
# async def run_monitoring_check(notify_callback: Callable):
#     """Fetches all sites and checks their status, calling notify_callback on failure."""
#     logger.info("Starting monitoring check run...")
#     try:
#         sites = await get_all_sites_with_users()
#     except Exception as e:
#         logger.error(f"Failed to fetch sites for monitoring: {e}")
#         return
#
#     tasks = []
#
#     async def check_and_notify(site):
#         # Проверяем, что у сайта есть пользователь (на всякий случай)
#         if not site.user:
#             logger.error(
#                 f"Site {site.id} ({site.url}) has no associated user, skipping."
#             )
#             return
#
#         is_ok = await check_website(site.url)
#         if not is_ok:
#             logger.warning(f"Site {site.url} (User: {site.user.telegram_id}) is DOWN!")
#             await notify_callback(
#                 site.user.telegram_id, f"🚨 Внимание! Ваш сайт {site.url} недоступен!"
#             )
#
#     for site in sites:
#         tasks.append(check_and_notify(site))
#
#     await asyncio.gather(
#         *tasks, return_exceptions=True
#     )  # Собираем ошибки, чтобы не прерывать все
#     logger.info("Monitoring check run finished.")
import asyncio
import aiohttp
from typing import Callable
from celery import shared_task

from shared.db import get_all_sites_with_users
from shared.logger_setup import logger


async def check_website(url: str) -> bool:
    """Checks if a website returns a 2xx status code."""
    try:
        headers = {"User-Agent": "WebsiteMonitorBot/1.0 (+https://yourbot.info)"}
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15), headers=headers
        ) as session:
            async with session.get(url, allow_redirects=True, ssl=False) as response:
                logger.debug(f"Checked {url}, status: {response.status}")
                return 200 <= response.status < 300
    except aiohttp.ClientConnectorError as e:
        logger.warning(f"Connection error checking {url}: {e}")
        return False
    except aiohttp.ClientError as e:
        logger.warning(f"Client error checking {url}: {e}")
        return False
    except asyncio.TimeoutError:
        logger.warning(f"Timeout checking {url}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking {url}: {type(e).__name__} - {e}")
        return False


@shared_task
def run_monitoring_check():
    """Fetches all sites and checks their status, calling notify_callback on failure."""
    logger.info("Starting monitoring check run...")

    async def run():
        try:
            sites = await get_all_sites_with_users()
        except Exception as e:
            logger.error(f"Failed to fetch sites for monitoring: {e}")
            return

        tasks = []

        async def check_and_notify(site):
            if not site.user:
                logger.error(
                    f"Site {site.id} ({site.url}) has no associated user, skipping."
                )
                return

            is_ok = await check_website(site.url)
            if not is_ok:
                logger.warning(
                    f"Site {site.url} (User: {site.user.telegram_id}) is DOWN!"
                )
                from bot.bot_main import send_notification

                await send_notification(
                    site.user.telegram_id,
                    f"🚨 Внимание! Ваш сайт {site.url} недоступен!",
                )

        for site in sites:
            tasks.append(check_and_notify(site))

        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Monitoring check run finished.")

    # Запускаем асинхронную задачу в Celery
    asyncio.run(run())
