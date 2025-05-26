# bot/monitoring.py
import requests
import time
from celery import shared_task
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from shared.db import SyncSessionFactory  # Используем Sync Session
from shared.logger_setup import logger
from shared.models import Site, User
from sqlalchemy.future import select

# --- Синхронные функции для Celery ---


def check_website_sync(url: str, retries: int = 3, delay: int = 2) -> bool:
    """Проверяет доступность сайта синхронно с повторными попытками."""
    logger.debug(f"Начинаем синхронную проверку сайта: {url}")
    headers = {"User-Agent": "WebsiteMonitorBot/1.0 (Sync Check)"}
    for attempt in range(retries):
        try:
            response = requests.get(
                url, headers=headers, timeout=10, allow_redirects=True
            )
            # Считаем 2xx и 3xx успешными
            is_available = 200 <= response.status_code < 400
            logger.info(
                f"{url} — {'доступен' if is_available else 'недоступен'} "
                f"(статус: {response.status_code}, попытка {attempt + 1})"
            )
            return is_available
        except requests.RequestException as e:
            logger.warning(f"Ошибка при проверке {url} (попытка {attempt + 1}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)  # Пауза перед повтором
    logger.warning(f"Сайт {url} недоступен после {retries} попыток.")
    return False


# @shared_task(bind=True, max_retries=3, default_retry_delay=60)  # Повтор через 60 секунд
# def check_single_site(self, site_id: int, url: str, user_id: int):
#     """Задача Celery для проверки одного сайта."""
#     logger.debug(f"Выполняется задача Celery для сайта ID={site_id}, URL={url}")
#     with SyncSessionFactory() as session:
#         try:
#             # Используем .get() для загрузки по первичному ключу
#             site = session.get(Site, site_id)
#             if not site:
#                 logger.warning(f"Сайт ID={site_id} не найден в задаче Celery.")
#                 return
#
#             was_available = site.is_available
#             is_available = check_website_sync(url)
#             now = datetime.now(timezone.utc)  # Используем UTC
#
#             send_alert = False
#             # Если статус изменился на "недоступен"
#             if was_available and not is_available:
#                 send_alert = True
#                 site.last_notified = now
#             # Если статус "недоступен" и прошло > 15 минут (или никогда не уведомляли)
#             elif not is_available and (
#                 site.last_notified is None
#                 or (now - site.last_notified).total_seconds() > 900
#             ):
#                 send_alert = True
#                 site.last_notified = now
#
#             # Обновляем статус и время проверки в любом случае
#             site.is_available = is_available
#             site.last_checked = now
#             session.commit()  # Сохраняем изменения
#
#             if send_alert:
#                 logger.info(
#                     f"Сайт {url} (ID={site_id}) недоступен. Отправка уведомления пользователю {user_id}..."
#                 )
#                 from bot.bot_main import send_notification_sync
#
#                 send_notification_sync(
#                     user_id, f"🚨 Внимание! Ваш сайт {url} недоступен!"
#                 )
#
#         except requests.RequestException as exc:
#             logger.warning(f"Сетевая ошибка при проверке {url}, повтор... ({exc})")
#             raise self.retry(exc=exc)  # Celery выполнит повтор
#         except Exception as e:
#             logger.error(
#                 f"Неожиданная ошибка обработки сайта {site_id}: {e}", exc_info=True
#             )
#             # Здесь можно решить, стоит ли повторять при других ошибках
#             # raise self.retry(exc=e)
#
#
# @shared_task
# def run_monitoring_check():
#     """Задача запуска мониторинга всех сайтов."""
#     logger.info("Запуск периодической задачи run_monitoring_check...")
#     with SyncSessionFactory() as session:
#         try:
#             # Выбираем только id, url и user_id, чтобы не загружать лишнего
#             stmt = select(Site.id, Site.url, Site.user_id)
#             sites = session.execute(stmt).fetchall()
#             logger.info(f"Найдено {len(sites)} сайтов для проверки.")
#
#             for site_id, url, user_id in sites:
#                 check_single_site.delay(site_id, url, user_id)
#             logger.info("Задачи на проверку сайтов успешно поставлены в очередь.")
#         except Exception as e:
#             logger.error(
#                 f"Ошибка при получении списка сайтов для мониторинга: {e}",
#                 exc_info=True,
#             )
# bot/monitoring.py
@shared_task
def run_monitoring_check():
    """Задача запуска мониторинга всех сайтов."""
    logger.info("Запуск периодической задачи run_monitoring_check...")
    with SyncSessionFactory() as session:
        try:
            stmt = select(Site.id, Site.url, User.telegram_id).join(
                User, Site.user_id == User.id
            )
            sites = session.execute(stmt).fetchall()
            logger.info(f"Найдено {len(sites)} сайтов для проверки.")
            for site_id, url, telegram_id in sites:
                check_single_site.delay(site_id, url, telegram_id)
            logger.info("Задачи на проверку сайтов успешно поставлены в очередь.")
        except Exception as e:
            logger.error(
                f"Ошибка при получении списка сайтов для мониторинга: {e}",
                exc_info=True,
            )


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def check_single_site(self, site_id: int, url: str, telegram_id: int):
    """Задача Celery для проверки одного сайта."""
    logger.debug(f"Выполняется задача Celery для сайта ID={site_id}, URL={url}")
    with SyncSessionFactory() as session:
        try:
            site = session.get(Site, site_id)
            if not site:
                logger.warning(f"Сайт ID={site_id} не найден в задаче Celery.")
                return

            was_available = site.is_available
            is_available = check_website_sync(url)
            now = datetime.now(timezone.utc)

            send_alert = False
            if was_available and not is_available:
                send_alert = True
                site.last_notified = now
            elif not is_available and (
                site.last_notified is None
                or (now - site.last_notified).total_seconds() > 900
            ):
                send_alert = True
                site.last_notified = now

            site.is_available = is_available
            site.last_checked = now
            session.commit()

            if send_alert:
                logger.info(
                    f"Сайт {url} (ID={site_id}) недоступен. Отправка уведомления пользователю {telegram_id}..."
                )
                from bot.bot_main import send_notification_sync

                send_notification_sync(
                    telegram_id, f"🚨 Внимание! Ваш сайт {url} недоступен!"
                )

        except requests.RequestException as exc:
            logger.warning(f"Сетевая ошибка при проверке {url}, повтор... ({exc})")
            raise self.retry(exc=exc)
        except Exception as e:
            logger.error(
                f"Неожиданная ошибка обработки сайта {site_id}: {e}", exc_info=True
            )
