# shared/utils.py
import requests
import time
from shared.logger_setup import logger


def check_website_sync(
    url: str, retries: int = 3, delay: int = 2, timeout: int = 10
) -> bool:
    """Checks website availability synchronously with retries."""
    logger.debug(f"Starting synchronous check for site: {url}")
    headers = {"User-Agent": "WebsiteMonitorBot/1.0 (Sync Check)"}
    for attempt in range(retries):
        try:
            response = requests.get(
                url, headers=headers, timeout=timeout, allow_redirects=True
            )
            is_available = 200 <= response.status_code < 400
            logger.info(
                f"{url} — {'available' if is_available else 'unavailable'} "
                f"(status: {response.status_code}, attempt {attempt + 1})"
            )
            return is_available
        except requests.RequestException as e:
            logger.warning(f"Error checking {url} (attempt {attempt + 1}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    logger.warning(f"Site {url} unavailable after {retries} attempts.")
    return False
