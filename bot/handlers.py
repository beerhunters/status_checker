from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ErrorEvent
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from shared.db import (
    get_or_create_user,
    add_site_to_user,
    get_user_sites,
    delete_site_by_id,
    AsyncSessionFactory,
)
from shared.logger_setup import logger
from bot.fsm import AddSite
from bot.keyboards import get_main_menu_keyboard, get_sites_keyboard
from shared.monitoring import update_site_availability

router = Router()


async def handle_db_error(message: Message, operation: str):
    logger.error(f"Database error during {operation} for user {message.from_user.id}")
    await message.answer(
        "Произошла ошибка при работе с базой данных. Попробуйте позже."
    )


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    try:
        await get_or_create_user(message.from_user.id, message.from_user.username)
        await message.answer(
            f"Привет, {message.from_user.full_name}! Я помогу тебе отслеживать доступность сайтов.",
            reply_markup=get_main_menu_keyboard(),
        )
    except Exception as e:
        await handle_db_error(message, "start command")


@router.callback_query(F.data == "to_start")
async def to_start_callback(callback: CallbackQuery):
    try:
        await get_or_create_user(callback.from_user.id, callback.from_user.username)
        await callback.message.edit_text(
            f"Привет, {callback.from_user.full_name}! Я помогу тебе отслеживать доступность сайтов.",
            reply_markup=get_main_menu_keyboard(),
        )
    except TelegramBadRequest as e:
        logger.warning(f"Failed to edit message for to_start: {e}")
        await callback.message.answer(
            f"Привет, {callback.from_user.full_name}! Я помогу тебе отслеживать доступность сайтов.",
            reply_markup=get_main_menu_keyboard(),
        )
    except Exception as e:
        logger.error(f"Error in to_start for user {callback.from_user.id}: {e}")
        await callback.message.answer(
            "Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard(),
        )
    finally:
        await callback.answer()


@router.callback_query(F.data == "add_site")
async def add_site_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Пожалуйста, отправьте URL сайта, который вы хотите отслеживать (например, https://google.com):"
    )
    await state.set_state(AddSite.waiting_for_url)
    await callback.answer()


@router.message(AddSite.waiting_for_url)
async def process_url(message: Message, state: FSMContext):
    url = message.text.strip()
    await state.clear()

    if not url or not (url.startswith("http://") or url.startswith("https://")):
        await message.answer(
            "Неверный формат URL. Пожалуйста, отправьте URL, начинающийся с http:// или https://."
        )
        return

    try:
        async with AsyncSessionFactory() as session:
            site = await add_site_to_user(message.from_user.id, url)
            if site:
                # Проверяем доступность и обновляем статус
                await update_site_availability(session, site.id, url)
                await message.answer(f"Сайт {url} успешно добавлен и проверен!")
            else:
                await message.answer(f"Сайт {url} уже отслеживается.")
    except Exception as e:
        await handle_db_error(message, "adding site")


@router.callback_query(F.data == "list_sites")
async def list_sites_callback(callback: CallbackQuery):
    try:
        sites = await get_user_sites(callback.from_user.id)
        keyboard = get_sites_keyboard(sites)
        if not sites:
            await callback.message.answer("У вас пока нет сайтов для отслеживания.")
        else:
            await callback.message.answer(
                "Ваши сайты (нажмите, чтобы удалить):", reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Error listing sites for {callback.from_user.id}: {e}")
        await callback.message.answer(
            "Не удалось получить список сайтов. Попробуйте позже."
        )
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("delete_site_"))
async def delete_site_callback(callback: CallbackQuery):
    try:
        site_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        logger.error(f"Invalid callback data received: {callback.data}")
        await callback.answer("Ошибка: неверные данные.", show_alert=True)
        return

    try:
        success = await delete_site_by_id(site_id, callback.from_user.id)
        if success:
            await callback.message.edit_text("Сайт удален.")
        else:
            await callback.message.edit_text(
                "Не удалось удалить сайт (возможно, он уже удален)."
            )
    except TelegramBadRequest as e:
        logger.warning(f"Failed to edit message (maybe no change?): {e}")
        await callback.answer("Сайт удален (сообщение не изменилось).")
    except Exception as e:
        logger.error(f"Error deleting site {site_id} for {callback.from_user.id}: {e}")
        await callback.message.answer("Не удалось удалить сайт. Попробуйте позже.")
    finally:
        await callback.answer()


@router.errors()
async def error_handler(event: ErrorEvent):
    logger.critical(
        f"Unhandled error caused by update {event.update}: {event.exception}",
        exc_info=True,
    )

    update = event.update
    user_id = None
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id

    if user_id:
        try:
            if not isinstance(event.exception, (TelegramForbiddenError)):
                await event.update.bot.send_message(
                    user_id,
                    "Произошла непредвиденная ошибка. Мы уже работаем над ее устранением.",
                )
        except Exception as e:
            logger.error(f"Failed to send error message to user {user_id}: {e}")
