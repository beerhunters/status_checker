import requests
from shared.config import settings
import logging

logger = logging.getLogger("WebsiteMonitorBot")


async def send_notification_async(user_id: int, message: str) -> None:
    url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
    payload = {"chat_id": user_id, "text": message, "parse_mode": "HTML"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=5) as response:
                if not (200 <= response.status < 400):
                    logger.error(
                        f"Failed to send notification to {user_id}: {response.status}"
                    )
    except Exception as e:
        logger.error(f"Error sending notification to {user_id}: {str(e)}")


def send_notification_sync(user_id: int, message: str) -> None:
    url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
    payload = {"chat_id": user_id, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=5)
        if not (200 <= response.status_code < 400):
            logger.error(
                f"Failed to send notification to {user_id}: {response.status_code}"
            )
    except Exception as e:
        logger.error(f"Error sending notification to {user_id}: {str(e)}")
