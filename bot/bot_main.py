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
