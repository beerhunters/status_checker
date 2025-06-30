# shared/monitoring.py
import aiohttp
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from shared.logger_setup import logger
from shared.models import Site
from sqlalchemy.sql import text


async def check_website_async(url: str, retries: int = 2) -> bool:
    """Проверяет доступность сайта асинхронно."""
    logger.debug(f"Начинаем асинхронную проверку сайта: {url}")
    headers = {"User-Agent": "WebsiteMonitorBot/1.0 (Async Check)"}
    # Устанавливаем таймаут для всех операций
    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            for attempt in range(retries):
                try:
                    async with session.get(url, allow_redirects=True) as response:
                        is_available = (
                            200 <= response.status < 400
                        )  # Считаем редиректы (3xx) успешными
                        logger.info(
                            f"{url} — {'доступен' if is_available else 'недоступен'} "
                            f"(статус: {response.status}, асинхронная попытка {attempt + 1})"
                        )
                        return is_available
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    logger.warning(
                        f"Ошибка при асинхронной проверке {url} (попытка {attempt + 1}): {type(e).__name__} - {e}"
                    )
                    if attempt < retries - 1:
                        await asyncio.sleep(
                            1
                        )  # Небольшая пауза перед повторной попыткой
                except Exception as e:
                    logger.error(
                        f"Неожиданная ошибка при асинхронной проверке {url}: {e}",
                        exc_info=True,
                    )
                    return False  # В случае неожиданной ошибки считаем недоступным
    except Exception as e:
        logger.error(f"Ошибка создания aiohttp сессии для {url}: {e}", exc_info=True)

    return False  # Если все попытки не удались


async def update_site_availability(
    session: AsyncSession, site_id: int, url: str
) -> bool:
    """Обновляет статус сайта в БД асинхронно и возвращает статус."""
    logger.debug(f"Асинхронное обновление статуса сайта ID={site_id}, URL={url}")
    try:
        is_available = await check_website_async(url)
        site = await session.get(
            Site, site_id
        )  # Используем session.get для поиска по PK
        if site:
            site.is_available = is_available
            await session.flush()  # Применяем изменения, но не коммитим (коммит в вызывающей функции)
            logger.info(
                f"Статус сайта {site_id} подготовлен к обновлению (асинхронно): {'доступен' if is_available else 'недоступен'}"
            )
            return is_available
        else:
            logger.warning(f"Сайт {site_id} не найден в базе данных (асинхронно).")
            return False
    except Exception as e:
        logger.error(
            f"Ошибка при асинхронном обновлении статуса сайта {site_id}: {e}",
            exc_info=True,
        )
        raise  # Перевыбрасываем, чтобы вызывающая функция могла обработать и сделать rollback
