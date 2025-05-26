# bot/bot_main.py
import asyncio
import requests
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramAPIError,
    TelegramBadRequest,
)

from shared.config import settings
from shared.db import init_db, AsyncSessionFactory, User
from shared.logger_setup import logger
from bot.handlers import router as main_router
from bot.celery_app import celery_app

# Создаем основной экземпляр бота
bot = Bot(
    token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)


def send_notification_sync(user_id: int, message: str):
    """Отправляет уведомление синхронно через Telegram API с использованием requests."""
    logger.debug(f"Attempting to send sync notification to {user_id}")
    url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
    payload = {"chat_id": user_id, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info(f"Sync notification sent successfully to {user_id}")
        else:
            logger.error(f"Failed to send sync message to {user_id}: {response.text}")
            if "chat not found" in response.text.lower():
                logger.warning(
                    f"Chat with user {user_id} not found. User may not have started the bot."
                )
    except requests.RequestException as e:
        logger.error(f"Failed to send sync message to {user_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending sync message to {user_id}: {e}")


async def main() -> None:
    """Основная функция запуска бота."""
    logger.info("Starting Website Monitor Bot...")

    # Инициализация базы данных
    try:
        await init_db()
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}. Exiting.", exc_info=True)
        return

    # Настройка диспетчера
    dp = Dispatcher()
    dp.include_router(main_router)

    # Удаляем вебхук и запускаем поллинг
    logger.info("Deleting webhook and starting polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    logger.info("Bot polling stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")
