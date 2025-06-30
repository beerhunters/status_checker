from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Optional, List
from shared.db import (
    get_or_create_user,
    add_site_to_user,
    get_user_sites,
    delete_site_by_id,
)
from shared.models import Site
from .fsm import AddSite
from .keyboards import get_main_menu_keyboard, get_sites_keyboard, get_back_keyboard
import logging
import traceback

router = Router()
logger = logging.getLogger("WebsiteMonitorBot")


class ErrorInfo:
    def __init__(self, exception: Exception, update: Optional[object] = None):
        self.exception = exception
        self.update = update
        self.traceback_info = "".join(traceback.format_tb(exception.__traceback__))

    def _get_error_location(self) -> str:
        tb = traceback.extract_tb(self.exception.__traceback__)
        last_call = tb[-1]
        filename = last_call.filename
        line = last_call.lineno
        func = last_call.name
        code_line = last_call.line.strip() if last_call.line else "???"
        return f"{filename}:{line} in {func} -> {code_line}"

    def _format_traceback(self, max_length: int = 2000) -> str:
        tb_lines = self.traceback_info.splitlines()
        snippet = "\n".join(tb_lines[-10:])
        return snippet[:max_length]

    def get_user_info(self) -> tuple[Optional[int], Optional[str], Optional[str]]:
        update = self.update.update
        user_id = (
            update.from_user.id
            if hasattr(update, "from_user") and update.from_user
            else None
        )
        username = (
            update.from_user.username
            if hasattr(update, "from_user") and update.from_user
            else None
        )
        return user_id, username


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    user_id = message.from_user.id
    username = message.from_user.username
    # Создаём или получаем пользователя в БД
    user = await get_or_create_user(telegram_id=user_id, username=username)
    logger.info(f"User {user_id} ({username}) started the bot")
    text = (
        f"Привет, {username or 'пользователь'}!\n\n"
        "Я бот для мониторинга доступности сайтов. "
        "Добавляй свои сайты, и я буду сообщать, если они станут недоступны."
    )
    await message.answer(text, reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "to_start")
async def to_start_callback(callback: CallbackQuery):
    text = "Главное меню"
    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "add_site")
async def add_site_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите URL сайта для мониторинга:", reply_markup=get_back_keyboard()
    )
    await state.set_state(AddSite.waiting_for_url)
    await callback.answer()


@router.message(AddSite.waiting_for_url)
async def process_url(message: Message, state: FSMContext):
    url = message.text.strip().lower()
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    site = await add_site_to_user(message.from_user.id, url)
    if site:
        status_text = "доступен" if site.is_available else "недоступен"
        await message.answer(
            f"Сайт {url} добавлен! Текущий статус: {status_text}",
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        await message.answer(
            "Не удалось добавить сайт. Возможно, он уже добавлен или URL некорректен.",
            reply_markup=get_main_menu_keyboard(),
        )
    await state.clear()


@router.callback_query(F.data == "list_sites")
async def list_sites_callback(callback: CallbackQuery):
    sites = await get_user_sites(callback.from_user.id)
    if not sites:
        await callback.message.edit_text(
            "У вас нет добавленных сайтов.", reply_markup=get_main_menu_keyboard()
        )
    else:
        keyboard = get_sites_keyboard(sites)
        await callback.message.edit_text("Ваши сайты:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("delete_site_"))
async def delete_site_callback(callback: CallbackQuery):
    site_id = int(callback.data.split("_")[2])
    success = await delete_site_by_id(site_id, callback.from_user.id)
    if success:
        await callback.message.edit_text(
            "Сайт удалён!", reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.message.edit_text(
            "Не удалось удалить сайт.", reply_markup=get_main_menu_keyboard()
        )
    await callback.answer()
