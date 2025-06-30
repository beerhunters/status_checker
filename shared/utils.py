# import requests
# import time
# import redis
# from bot.celery_app import celery_app  # Убедитесь, что импорт корректен
# from shared.logger_setup import logger
# from shared.config import settings
# from redis.exceptions import ConnectionError, TimeoutError
#
#
# import aiohttp
# from shared.config import settings
#
#
# async def send_notification_async(user_id: int, message: str) -> None:
#     url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
#     payload = {"chat_id": user_id, "text": message, "parse_mode": "HTML"}
#     async with aiohttp.ClientSession() as session:
#         try:
#             async with session.post(url, json=payload, timeout=5) as response:
#                 if response.status != 200:
#                     logger.error(
#                         f"Failed to send notification to {user_id}: {await response.text()}"
#                     )
#         except Exception as e:
#             logger.error(f"Error sending notification to {user_id}: {str(e)}")
#
#
# def check_website_sync(
#     url: str, retries: int = 3, delay: int = 2, timeout: int = 5
# ) -> bool:
#     logger.debug(f"Starting check for site: {url}")
#     headers = {"User-Agent": "WebsiteMonitorBot/1.0 (Sync Check)"}
#     for attempt in range(retries):
#         try:
#             response = requests.get(
#                 url, headers=headers, timeout=timeout, allow_redirects=True
#             )
#             is_available = 200 <= response.status_code < 400
#             logger.info(
#                 f"{url} — {'available' if is_available else 'unavailable'} "
#                 f"(status: {response.status_code}, attempt {attempt + 1})"
#             )
#             return is_available
#         except requests.RequestException as e:
#             logger.warning(f"Error checking {url} (attempt {attempt + 1}): {e}")
#             if attempt < retries - 1:
#                 time.sleep(delay)
#     logger.warning(f"Site {url} unavailable after {retries} attempts.")
#     return False
#
#
# def send_notification_sync(user_id: int, message: str) -> None:
#     logger.debug(f"Attempting to send sync notification to {user_id}")
#     url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
#     payload = {"chat_id": user_id, "text": message, "parse_mode": "HTML"}
#     try:
#         response = requests.post(url, json=payload, timeout=5)
#         if response.status_code == 200:
#             logger.info(f"Sync notification sent successfully to {user_id}")
#         else:
#             logger.error(f"Failed to send sync message to {user_id}: {response.text}")
#             if "chat not found" in response.text.lower():
#                 logger.warning(
#                     f"Chat with user {user_id} not found. User may not have started the bot."
#                 )
#     except requests.RequestException as e:
#         logger.error(f"Failed to send sync message to {user_id}: {e}")
#     except Exception as e:
#         logger.error(f"Unexpected error sending sync message to {user_id}: {e}")
#
#
# def publish_celery_task(
#     task_name: str, args: list, retries: int = 3, delay: int = 5
# ) -> bool:
#     """Publishes a Celery task using apply_async with retries."""
#     for attempt in range(retries):
#         try:
#             redis_client = redis.Redis(
#                 host=settings.redis_host,
#                 port=settings.redis_port,
#                 db=0,
#                 decode_responses=True,
#                 socket_connect_timeout=5,
#                 socket_timeout=5,
#             )
#             redis_client.ping()
#             logger.debug(f"Redis ping successful on attempt {attempt + 1}")
#             redis_client.close()
#             celery_app.send_task(task_name, args=args, kwargs={})
#             logger.info(f"Published task {task_name} with args {args} to Celery")
#             return True
#         except (ConnectionError, TimeoutError) as e:
#             logger.warning(
#                 f"Failed to publish task {task_name} (attempt {attempt + 1}): {e}"
#             )
#             if attempt < retries - 1:
#                 time.sleep(delay)
#         except Exception as e:
#             logger.error(f"Error publishing task {task_name}: {e}", exc_info=True)
#             break
#     logger.error(f"Failed to publish task {task_name} after {retries} attempts")
#     return False
# Без изменений, сохранена логика уведомлений
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
