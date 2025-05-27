# bot/bot_main.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from shared.config import settings
from shared.db import init_db, AsyncSessionFactory, User
from shared.logger_setup import logger
from bot.handlers import router as main_router

# Создаем основной экземпляр бота
bot = Bot(
    token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)


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
