# bot/monitoring.py

import requests
import time
from celery import shared_task
from sqlalchemy.orm import Session
from shared.db import SessionFactory
from shared.logger_setup import logger


def check_website_sync(url: str, retries: int = 2) -> bool:
    """Проверяет доступность сайта синхронно."""
    logger.debug(f"Начинаем проверку сайта: {url}")
    for attempt in range(retries):
        try:
            headers = {"User-Agent": "WebsiteMonitorBot/1.0"}
            response = requests.get(url, headers=headers, timeout=10)
            is_available = 200 <= response.status_code < 300
            logger.info(
                f"{url} — {'доступен' if is_available else 'недоступен'} (попытка {attempt + 1})"
            )
            return is_available
        except requests.RequestException as e:
            logger.warning(f"Ошибка при проверке {url}: {e}")
            if attempt < retries - 1:
                time.sleep(1)
    return False


def update_site_availability_sync(session: Session, site_id: int, url: str) -> bool:
    """Обновляет статус сайта в БД."""
    logger.debug(f"Обновление статуса сайта ID={site_id}, URL={url}")
    try:
        is_available = check_website_sync(url)

        # Прямой SQL-запрос через синхронную сессию
        result = session.execute(
            "UPDATE sites SET is_available = :status WHERE id = :site_id RETURNING id",
            {"status": is_available, "site_id": site_id},
        )
        session.commit()

        if result.fetchone():
            logger.info(
                f"Статус сайта {site_id} успешно обновлён: {'доступен' if is_available else 'недоступен'}"
            )
            return is_available
        else:
            logger.warning(f"Сайт {site_id} не найден в базе данных.")
            return False
    except Exception as e:
        logger.error(
            f"Ошибка при обновлении статуса сайта {site_id}: {e}", exc_info=True
        )
        session.rollback()
        return False


@shared_task(bind=True, max_retries=3)
def check_single_site(self, site_id: int, url: str, user_id: int):
    """Задача Celery для проверки одного сайта."""
    logger.debug(f"Выполняется задача Celery для сайта {site_id}")
    with SessionFactory() as session:
        try:
            is_available = update_site_availability_sync(session, site_id, url)

            if not is_available:
                # Проверяем, отправляли ли уведомление недавно
                last_notified_row = session.execute(
                    "SELECT last_notified FROM sites WHERE id = :site_id",
                    {"site_id": site_id},
                ).fetchone()

                last_notified = last_notified_row[0] if last_notified_row else None
                now = datetime.utcnow()

                if (
                    last_notified is None or (now - last_notified).total_seconds() > 900
                ):  # 15 минут
                    from bot.bot_main import send_notification_sync

                    try:
                        send_notification_sync(
                            user_id, f"🚨 Внимание! Ваш сайт {url} недоступен!"
                        )
                        logger.info(
                            f"Уведомление о недоступности отправлено пользователю {user_id}"
                        )

                        session.execute(
                            "UPDATE sites SET last_notified = :now WHERE id = :site_id",
                            {"now": now, "site_id": site_id},
                        )
                        session.commit()
                    except Exception as e:
                        logger.error(
                            f"Ошибка отправки уведомления для сайта {url}: {e}"
                        )
                        raise self.retry(countdown=60)
            return is_available
        except Exception as e:
            logger.error(f"Ошибка обработки сайта {site_id}: {e}", exc_info=True)
            raise self.retry(countdown=60)


@shared_task
def run_monitoring_check():
    """Задача запуска мониторинга всех сайтов."""
    logger.debug("Запуск задачи run_monitoring_check")
    with SessionFactory() as session:
        try:
            result = session.execute("SELECT id, url, user_id FROM sites")
            sites = result.fetchall()
            logger.info(f"Найдено {len(sites)} сайтов для проверки")

            for site in sites:
                site_id, url, user_id = site
                check_single_site.delay(site_id, url, user_id)
        except Exception as e:
            logger.error(f"Ошибка при получении списка сайтов: {e}", exc_info=True)
