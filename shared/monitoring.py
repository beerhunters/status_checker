# Без изменений, сохранена логика проверки сайтов
import aiohttp
from shared.models import Site
from shared.db import AsyncSessionFactory
import logging

logger = logging.getLogger("WebsiteMonitorBot")


async def check_website_async(url: str, retries: int = 2) -> bool:
    headers = {"User-Agent": "WebsiteMonitorBot/1.0 (Async Check)"}
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for attempt in range(retries):
            try:
                async with session.get(url, headers=headers) as response:
                    return 200 <= response.status < 400
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt == retries - 1:
                    return False
    return False
