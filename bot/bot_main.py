import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from shared.config import settings
from shared.db import init_db
from shared.logger_setup import logger
from bot.handlers import router as main_router
from bot.monitoring import run_monitoring_check

bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)


async def send_notification(user_id: int, message_text: str):
    """Отправляет уведомление с обработкой ошибок."""
    try:
        await bot.send_message(user_id, message_text)
        logger.debug(f"Sent notification to {user_id}")
    except TelegramForbiddenError:
        logger.warning(
            f"User {user_id} blocked the bot. Consider marking user as inactive."
        )
        # Здесь можно добавить логику для деактивации пользователя в БД
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

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        run_monitoring_check,
        "interval",
        minutes=settings.check_interval_minutes,
        args=[send_notification],
        misfire_grace_time=60,  # Допускаем опоздание на 60 сек
    )
    scheduler.start()
    logger.info(
        f"Scheduler started. Check interval: {settings.check_interval_minutes} minutes."
    )

    # Удаляем вебхук, если он был установлен
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Starting bot polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
