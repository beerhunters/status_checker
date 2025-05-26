# bot/handlers.py
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ErrorEvent
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from shared.db import (
    get_or_create_user,
    get_user_sites,
    delete_site_by_id,
    AsyncSessionFactory,
)
from shared.models import User, Site  # Импортируем модели
from sqlalchemy.future import select  # Импортируем select
from shared.logger_setup import logger
from bot.fsm import AddSite
from bot.keyboards import get_main_menu_keyboard, get_sites_keyboard, get_back_keyboard
from shared.monitoring import update_site_availability  # Импортируем async версию

router = Router()


async def handle_db_error(message_or_callback, operation: str):
    """Обрабатывает ошибки БД, отправляя сообщение пользователю."""
    user_id = message_or_callback.from_user.id
    logger.error(f"Database error during {operation} for user {user_id}")
    text = "Произошла ошибка при работе с базой данных. Попробуйте позже."
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(text, reply_markup=get_main_menu_keyboard())
    elif isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(
            text, reply_markup=get_main_menu_keyboard()
        )
        await message_or_callback.answer("Ошибка БД", show_alert=True)


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Обработчик команды /start."""
    try:
        await get_or_create_user(message.from_user.id, message.from_user.username)
        await message.answer(
            f"Привет, {message.from_user.full_name}! 👋\n\n"
            "Я бот для мониторинга доступности сайтов. "
            "Я буду проверять ваши сайты каждые несколько минут и сообщать, "
            "если какой-то из них станет недоступен.\n\n"
            "Используйте кнопки ниже для управления:",
            reply_markup=get_main_menu_keyboard(),
        )
    except Exception as e:
        logger.error(
            f"Error in start command for {message.from_user.id}: {e}", exc_info=True
        )
        await handle_db_error(message, "start command")


@router.callback_query(F.data == "to_start")
async def to_start_callback(callback: CallbackQuery):
    """Обработчик кнопки 'В начало'."""
    try:
        await get_or_create_user(callback.from_user.id, callback.from_user.username)
        text = (
            f"Привет, {callback.from_user.full_name}! 👋\n\n"
            "Вы вернулись в главное меню. Используйте кнопки ниже:"
        )
        try:
            await callback.message.edit_text(
                text,
                reply_markup=get_main_menu_keyboard(),
            )
        except TelegramBadRequest:
            # Если сообщение не изменилось, просто отвечаем на callback
            await callback.message.answer(text, reply_markup=get_main_menu_keyboard())
            await callback.message.delete()  # Удаляем старое сообщение

    except Exception as e:
        logger.error(
            f"Error in to_start for user {callback.from_user.id}: {e}", exc_info=True
        )
        await callback.message.answer(
            "Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu_keyboard()
        )
    finally:
        await callback.answer()


@router.callback_query(F.data == "add_site")
async def add_site_callback(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс добавления сайта."""
    await callback.message.edit_text(
        "Пожалуйста, отправьте URL сайта, который вы хотите отслеживать "
        "(например, https://google.com):",
        reply_markup=get_back_keyboard(),  # Добавляем кнопку "В начало"
    )
    await state.set_state(AddSite.waiting_for_url)
    await callback.answer()


@router.message(AddSite.waiting_for_url)
async def process_url(message: Message, state: FSMContext):
    """Обрабатывает введенный URL, добавляет и проверяет сайт."""
    url = message.text.strip().lower()  # Приводим к нижнему регистру для унификации
    await state.clear()

    # Простая валидация URL
    if not (url.startswith("http://") or url.startswith("https://")):
        await message.answer(
            "Неверный формат URL. Пожалуйста, отправьте URL, "
            "начинающийся с http:// или https://.",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    # Дополнительная валидация (простая)
    if "." not in url[url.find("://") + 3 :]:
        await message.answer(
            "Похоже, в URL отсутствует домен. Пожалуйста, проверьте и отправьте снова.",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    try:
        async with AsyncSessionFactory() as session:
            # 1. Получаем пользователя
            user_stmt = select(User).filter(User.telegram_id == message.from_user.id)
            result = await session.execute(user_stmt)
            user = result.scalars().first()
            if not user:  # На всякий случай, хотя /start должен был создать
                user = await get_or_create_user(
                    message.from_user.id, message.from_user.username
                )

            # 2. Проверяем, существует ли сайт у этого пользователя
            site_stmt = select(Site).filter(Site.user_id == user.id, Site.url == url)
            result = await session.execute(site_stmt)
            existing_site = result.scalars().first()

            if existing_site:
                await message.answer(
                    f"Сайт {url} уже отслеживается.",
                    reply_markup=get_main_menu_keyboard(),
                )
                return

            # 3. Добавляем новый сайт
            new_site = Site(url=url, user_id=user.id)
            session.add(new_site)
            await session.flush()  # Получаем ID нового сайта
            site_id = new_site.id

            # 4. Проверяем доступность и обновляем статус
            is_available = await update_site_availability(session, site_id, url)
            status_text = "доступен" if is_available else "недоступен"

            # 5. Коммитим все изменения
            await session.commit()

            await message.answer(
                f"Сайт {url} успешно добавлен! Текущий статус: {status_text}.",
                reply_markup=get_main_menu_keyboard(),
            )

    except Exception as e:
        logger.error(
            f"Error adding site {url} for {message.from_user.id}: {e}", exc_info=True
        )
        await handle_db_error(message, "adding site")


@router.callback_query(F.data == "list_sites")
async def list_sites_callback(callback: CallbackQuery):
    """Показывает список сайтов пользователя."""
    try:
        sites = await get_user_sites(callback.from_user.id)
        keyboard = get_sites_keyboard(sites)
        text = (
            "Ваши сайты (нажмите, чтобы удалить):"
            if sites
            else "У вас пока нет сайтов для отслеживания."
        )

        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except TelegramBadRequest as e:
            logger.warning(f"Failed to edit message for list_sites (no change?): {e}")
            # Если не удалось отредактировать (например, текст тот же), просто отвечаем
            await callback.answer()

    except Exception as e:
        logger.error(
            f"Error listing sites for {callback.from_user.id}: {e}", exc_info=True
        )
        await handle_db_error(callback, "listing sites")
    finally:
        # Всегда отвечаем на callback, чтобы убрать 'часики'
        await callback.answer()


@router.callback_query(F.data.startswith("delete_site_"))
async def delete_site_callback(callback: CallbackQuery):
    """Удаляет сайт по ID."""
    try:
        site_id_str = callback.data.split("_")[2]
        site_id = int(site_id_str)
    except (IndexError, ValueError):
        logger.error(f"Invalid callback data received: {callback.data}")
        await callback.answer("Ошибка: неверные данные.", show_alert=True)
        return

    try:
        success = await delete_site_by_id(site_id, callback.from_user.id)
        if success:
            await callback.answer("Сайт удален.", show_alert=False)
            # Обновляем список сайтов после удаления
            sites = await get_user_sites(callback.from_user.id)
            keyboard = get_sites_keyboard(sites)
            text = (
                "Ваши сайты (нажмите, чтобы удалить):"
                if sites
                else "У вас больше нет сайтов для отслеживания."
            )
            await callback.message.edit_text(text, reply_markup=keyboard)
        else:
            await callback.answer(
                "Не удалось удалить сайт (возможно, он уже удален).", show_alert=True
            )

    except TelegramBadRequest as e:
        logger.warning(f"Failed to edit message after delete (maybe no change?): {e}")
        await callback.answer("Сайт удален.")  # Все равно подтверждаем удаление
    except Exception as e:
        logger.error(
            f"Error deleting site {site_id} for {callback.from_user.id}: {e}",
            exc_info=True,
        )
        await callback.answer(
            "Не удалось удалить сайт. Попробуйте позже.", show_alert=True
        )
        await handle_db_error(callback, "deleting site")


@router.errors()
async def error_handler(event: ErrorEvent):
    """Глобальный обработчик ошибок."""
    logger.critical(
        f"Unhandled error caused by update {event.update.update_id}: {event.exception}",
        exc_info=True,
    )

    update = event.update
    user = (
        update.message.from_user
        if update.message
        else update.callback_query.from_user if update.callback_query else None
    )

    if user:
        try:
            # Не отправляем сообщение, если бот заблокирован
            if not isinstance(event.exception, TelegramForbiddenError):
                await event.update.bot.send_message(
                    user.id,
                    "Извините, произошла непредвиденная ошибка. 😥\n"
                    "Мы уже работаем над ее устранением. Пожалуйста, попробуйте позже.",
                    reply_markup=get_main_menu_keyboard(),
                )
        except Exception as e:
            logger.error(f"Failed to send error message to user {user.id}: {e}")
