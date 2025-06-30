# # bot/bot_main.py
# import asyncio
# from aiogram import Bot, Dispatcher
# from aiogram.client.default import DefaultBotProperties
# from aiogram.enums import ParseMode
# from shared.config import settings
# from shared.db import init_db, AsyncSessionFactory, User
# from shared.logger_setup import logger
# from bot.handlers import router as main_router
# from bot.celery_app import initialize_celery_schedule
#
# bot = Bot(
#     token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
# )
#
#
# async def main() -> None:
#     logger.info("Starting Website Monitor Bot...")
#     try:
#         await init_db()
#         initialize_celery_schedule()  # Initialize Celery schedule after DB is ready
#     except Exception as e:
#         logger.critical(f"Failed to initialize database or Celery: {e}", exc_info=True)
#         return
#     dp = Dispatcher()
#     dp.include_router(main_router)
#     logger.info("Deleting webhook and starting polling...")
#     await bot.delete_webhook(drop_pending_updates=True)
#     await dp.start_polling(bot)
#     logger.info("Bot polling stopped.")
#
#
# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except (KeyboardInterrupt, SystemExit):
#         logger.info("Bot stopped by user.")
# Изменения: Убрана зависимость от Celery, инициализация APScheduler для периодических задач
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from shared.config import settings
from bot.handlers import router
from bot.scheduler import setup_scheduler
import asyncio
import logging

from shared.db import init_db


async def main() -> None:
    try:
        await init_db()  # Инициализация БД с созданием директории
    except Exception as e:
        logging.error(f"Failed to initialize database: {str(e)}")
        raise
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    # Настройка планировщика задач для проверки сайтов
    await setup_scheduler(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
