import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError

from shared.config import settings
from shared.db import init_db
from shared.logger_setup import logger
from bot.handlers import router as main_router
from bot.celery_app import celery_app

bot = Bot(
    token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)


async def send_notification(user_id: int, message_text: str):
    """Отправляет уведомление с обработкой ошибок."""
    try:
        await bot.send_message(user_id, message_text)
        logger.debug(f"Sent notification to {user_id}")
    except TelegramForbiddenError:
        logger.warning(
            f"User {user_id} blocked the bot. Consider marking user as inactive."
        )
    except TelegramAPIError as e:
        logger.error(f"Failed to send message to {user_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending message to {user_id}: {e}")


async def main() -> None:
    logger.info("Starting Website Monitor Bot...")

    try:
        await init_db()
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}. Exiting.")
        return

    dp = Dispatcher()
    dp.include_router(main_router)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Starting bot polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
