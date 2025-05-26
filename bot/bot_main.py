# bot/bot_main.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError

from shared.config import settings
from shared.db import (
    init_db,
    AsyncSessionFactory,
    User,
)  # Убедитесь, что User импортирован
from shared.logger_setup import logger
from bot.handlers import router as main_router
from bot.celery_app import celery_app  # Импортируем, чтобы Celery знал о нем

# Создаем основной экземпляр бота
bot = Bot(
    token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)


async def send_notification(user_id: int, message_text: str):
    """Асинхронно отправляет уведомление пользователю."""
    try:
        await bot.send_message(user_id, message_text)
        logger.debug(f"Sent notification to {user_id}")
    except TelegramForbiddenError:
        logger.warning(
            f"User {user_id} blocked the bot. Consider marking user as inactive."
        )
        # Здесь можно добавить логику для деактивации пользователя в БД
        # async with AsyncSessionFactory() as session:
        #     user = await session.query(User).filter(User.telegram_id == user_id).first()
        #     if user:
        #         user.is_active = False # Если добавите поле is_active
        #         await session.commit()
    except TelegramAPIError as e:
        logger.error(f"Failed to send message to {user_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending message to {user_id}: {e}")


def send_notification_sync(user_id: int, message: str):
    """
    Отправляет уведомление синхронно (для Celery), используя asyncio.run.
    Внимание: Создает новый экземпляр бота и запускает новый event loop.
    Может быть неоптимально для высокой нагрузки.
    """
    logger.debug(f"Attempting to send sync notification to {user_id}")

    async def _send():
        # Создаем временный экземпляр бота
        temp_bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        try:
            await temp_bot.send_message(user_id, message)
            logger.info(f"Sync notification sent successfully to {user_id}")
        except TelegramForbiddenError:
            logger.warning(f"User {user_id} blocked the bot (sync).")
        except TelegramAPIError as e:
            logger.error(f"Failed to send sync message to {user_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending sync message to {user_id}: {e}")
        finally:
            # Обязательно закрываем сессию временного бота
            await temp_bot.session.close()

    try:
        asyncio.run(_send())
    except RuntimeError as e:
        # Это может случиться, если eventlet создает конфликт с asyncio.run
        logger.error(
            f"Failed to run asyncio_run for sending message: {e}. "
            f"Eventlet/Asyncio conflict? Consider using a queue."
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
