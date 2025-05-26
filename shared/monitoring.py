# import aiohttp
# import asyncio
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.sql import text  # Явный импорт text
# from shared.logger_setup import logger
#
#
# async def check_website(url: str) -> bool:
#     """Checks if a website returns a 2xx status code."""
#     try:
#         headers = {"User-Agent": "WebsiteMonitorBot/1.0 (+https://yourbot.info)"}
#         async with aiohttp.ClientSession(
#             timeout=aiohttp.ClientTimeout(total=15), headers=headers
#         ) as session:
#             async with session.get(url, allow_redirects=True, ssl=False) as response:
#                 is_available = 200 <= response.status < 300
#                 logger.debug(
#                     f"Checked {url}, status: {response.status}, available: {is_available}"
#                 )
#                 return is_available
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
# async def update_site_availability(
#     session: AsyncSession, site_id: int, url: str
# ) -> bool:
#     """Обновляет статус доступности сайта в базе данных."""
#     is_available = await check_website(url)
#     try:
#         result = await session.execute(
#             text(
#                 "UPDATE sites SET is_available = :is_available WHERE id = :site_id RETURNING id"
#             ),
#             {"is_available": is_available, "site_id": site_id},
#         )
#         await session.commit()
#         if result.scalars().first():
#             logger.info(
#                 f"Updated availability for site {site_id}: {'available' if is_available else 'unavailable'}"
#             )
#             return is_available
#         else:
#             logger.warning(f"Site {site_id} not found during availability update")
#             return False
#     except Exception as e:
#         logger.error(f"Failed to update availability for site {site_id}: {e}")
#         await session.rollback()
#         return False
import aiohttp
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from shared.logger_setup import logger


async def check_website(url: str, retries: int = 2) -> bool:
    """Checks if a website returns a 2xx status code with retries."""
    for attempt in range(retries):
        try:
            headers = {"User-Agent": "WebsiteMonitorBot/1.0 (+https://yourbot.info)"}
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10), headers=headers
            ) as session:
                async with session.get(url, allow_redirects=True) as response:
                    is_available = 200 <= response.status < 300
                    logger.debug(
                        f"Attempt {attempt + 1}: {url}, status: {response.status}, available: {is_available}, headers: {response.headers}"
                    )
                    return is_available
        except aiohttp.ClientConnectorError as e:
            logger.warning(
                f"Attempt {attempt + 1} connection error checking {url}: {e}"
            )
            if attempt == retries - 1:
                return False
        except aiohttp.ClientSSLError as e:
            logger.warning(f"Attempt {attempt + 1} SSL error checking {url}: {e}")
            if attempt == retries - 1:
                return False
        except aiohttp.ClientError as e:
            logger.warning(f"Attempt {attempt + 1} client error checking {url}: {e}")
            if attempt == retries - 1:
                return False
        except asyncio.TimeoutError:
            logger.warning(f"Attempt {attempt + 1} timeout checking {url}")
            if attempt == retries - 1:
                return False
        except Exception as e:
            logger.error(
                f"Attempt {attempt + 1} unexpected error checking {url}: {type(e).__name__} - {e}"
            )
            if attempt == retries - 1:
                return False
        await asyncio.sleep(1)
    return False


async def update_site_availability(
    session: AsyncSession, site_id: int, url: str
) -> bool:
    """Updates the availability status of a site in the database."""
    is_available = await check_website(url)
    try:
        result = await session.execute(
            text(
                "UPDATE sites SET is_available = :is_available WHERE id = :site_id RETURNING id"
            ),
            {"is_available": is_available, "site_id": site_id},
        )
        await session.commit()
        if result.scalars().first():
            logger.info(
                f"Updated availability for site {site_id}: {'available' if is_available else 'unavailable'}"
            )
            return is_available
        else:
            logger.warning(f"Site {site_id} not found during availability update")
            return False
    except Exception as e:
        logger.error(f"Failed to update availability for site {site_id}: {e}")
        await session.rollback()
        return False
