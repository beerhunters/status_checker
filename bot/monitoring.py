import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from celery import shared_task
from shared.db import get_all_sessions_with_users, SessionFactory
from shared.logger_setup import logger


def check_website_sync(url: str, retries: int = 2) -> bool:
    logger.debug(f"Начало проверки сайта: {url}")
    for attempt in range(retries):
        try:
            headers = {"User-Agent": "WebsiteMonitorBot/1.0 (+https://yourbot.info)"}
            response = requests.get(
                url, headers=headers, timeout=10, allow_redirects=True
            )
            is_available = 200 <= response.status_code < 300
            logger.debug(
                f"Попытка {attempt + 1}: {url}, статус: {response.status_code}, доступен: {is_available}"
            )
            return is_available
        except requests.RequestException as e:
            logger.warning(f"Попытка {attempt + 1} ошибка для {url}: {e}")
        if attempt < retries - 1:
            time.sleep(1)
    logger.debug(f"Сайт {url} недоступен после {retries} попыток")
    return False


def update_site_availability_sync(session: Session, site_id: int, url: str) -> bool:
    logger.debug(f"Обновление статуса для сайта id={site_id}, url={url}")
    try:
        is_available = check_website_sync(url)
        result = session.execute(
            "UPDATE sites SET is_available = :status WHERE id = :site_id RETURNING id",
            {"status": is_available, "site_id": site_id},
        )
        session.commit()
        if result.scalars().first():
            logger.info(
                f"Сайт {site_id}: {'доступен' if is_available else 'недоступен'}"
            )
            return is_available
        else:
            logger.warning(f"Сайт {site_id} не найден в базе")
            return False
    except Exception as e:
        logger.error(f"Ошибка обновления статуса сайта {site_id}: {e}", exc_info=True)
        session.rollback()
        return False


@shared_task(bind=True, max_retries=3)
def check_single_site(self, site_id: int, url: str, user_id: int):
    logger.debug(
        f"Запуск задачи check_single_site: site_id={site_id}, url={url}, user_id={user_id}, task_id={self.request.id}"
    )
    with SessionFactory() as session:
        try:
            is_available = update_site_availability_sync(session, site_id, url)
            if not is_available:
                result = session.execute(
                    "SELECT last_notified FROM sites WHERE id = :site_id",
                    {"site_id": site_id},
                )
                last_notified = result.scalars().first()
                now = datetime.utcnow()
                if last_notified is None or now - last_notified > timedelta(minutes=15):
                    logger.warning(f"Сайт {url} (Пользователь: {user_id}) НЕДОСТУПЕН!")
                    from bot.bot_main import send_notification_sync

                    try:
                        send_notification_sync(
                            user_id, f"🚨 Внимание! Ваш сайт {url} недоступен!"
                        )
                        logger.info(
                            f"Отправлено уведомление пользователю {user_id} для сайта {url}"
                        )
                        session.execute(
                            "UPDATE sites SET last_notified = :now WHERE id = :site_id",
                            {"now": now, "site_id": site_id},
                        )
                        session.commit()
                    except Exception as e:
                        logger.error(
                            f"Ошибка отправки уведомления для сайта {url}: {e}",
                            exc_info=True,
                        )
                        raise self.retry(countdown=60)
            return is_available
        except Exception as e:
            logger.error(
                f"Ошибка обработки сайта {site_id} ({url}): {e}", exc_info=True
            )
            raise self.retry(countdown=60)


@shared_task
def run_monitoring_check():
    logger.debug("Запуск задачи run_monitoring_check")
    try:
        with SessionFactory() as session:
            sites = get_all_sessions_with_users(session)
            logger.debug(f"Получено {len(sites)} сайтов для мониторинга")
            for site in sites:
                if not site.user:
                    logger.error(
                        f"Сайт {site.id} ({site.url}) не имеет связанного пользователя, пропускаем."
                    )
                    continue
                check_single_site.delay(site.id, site.url, site.user.telegram_id)
    except Exception as e:
        logger.error(f"Ошибка в run_monitoring_check: {e}", exc_info=True)
        raise
    logger.debug("Задача run_monitoring_check завершена")
    return None
