# # bot/handlers.py
# from aiogram import Router, F
# from aiogram.filters import CommandStart
# from aiogram.types import Message, CallbackQuery, ErrorEvent
# from aiogram.fsm.context import FSMContext
# from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
# from aiogram.handlers import ErrorHandler
# from shared.db import (
#     get_or_create_user,
#     get_user_sites,
#     delete_site_by_id,
#     AsyncSessionFactory,
# )
# from shared.models import User, Site
# from sqlalchemy.future import select
# from shared.logger_setup import logger
# from bot.fsm import AddSite
# from bot.keyboards import get_main_menu_keyboard, get_sites_keyboard, get_back_keyboard
# from shared.monitoring import update_site_availability
# from datetime import datetime
# import traceback
# from typing import Optional
#
# router = Router()
#
#
# # Класс для хранения информации об ошибке
# class ErrorInfo:
#     def __init__(self, exception: Exception, update: Optional[ErrorEvent] = None):
#         self.exception = exception
#         self.exception_name = type(exception).__name__
#         self.exception_message = str(exception)
#         self.error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         self.update = update
#         self.traceback_info = traceback.format_exc()
#         self.traceback_snippet = self._format_traceback()
#         self.error_location = self._get_error_location()
#
#     def _get_error_location(self) -> str:
#         if not hasattr(self.exception, "__traceback__"):
#             return "❓ Неизвестное местоположение"
#         tb = traceback.extract_tb(self.exception.__traceback__)
#         if not tb:
#             return "❓ Неизвестное местоположение"
#         last_call = tb[-1]
#         filename = last_call.filename
#         line = last_call.lineno
#         func = last_call.name
#         code_line = last_call.line.strip() if last_call.line else "???"
#         return (
#             f"📂 <b>Файл:</b> {filename}\n"
#             f"📌 <b>Строка:</b> {line}\n"
#             f"🔹 <b>Функция:</b> {func}\n"
#             f"🖥 <b>Код:</b> <pre>{code_line}</pre>"
#         )
#
#     def _format_traceback(self, max_length: int = 2000) -> str:
#         tb_lines = self.traceback_info.splitlines()
#         snippet = (
#             "\n".join(tb_lines[-4:]) if len(tb_lines) >= 4 else self.traceback_info
#         )
#         if len(snippet) > max_length:
#             return snippet[:max_length] + "\n...[сокращено]"
#         return snippet
#
#     def get_user_info(self) -> tuple[Optional[int], Optional[str], Optional[str]]:
#         if not self.update:
#             return None, None, None
#         update = self.update.update
#         if update.message:
#             return (
#                 update.message.from_user.id,
#                 update.message.from_user.full_name,
#                 update.message.text,
#             )
#         elif update.callback_query:
#             return (
#                 update.callback_query.from_user.id,
#                 update.callback_query.from_user.full_name,
#                 update.callback_query.data,
#             )
#         return None, None, None
#
#
# # Обработчик ошибок
# @router.errors()
# class MyErrorHandler(ErrorHandler):
#     async def handle(self) -> None:
#         logger.info("Обработчик ошибок вызван")
#         exception = getattr(self.event, "exception", None)
#         update = getattr(self.event, "update", None)
#
#         if not exception:
#             logger.error("Событие без исключения: %s", self.event)
#             return
#
#         error_info = ErrorInfo(exception, self.event)
#
#         # Логирование ошибки
#         logger.error(
#             "Ошибка %s: %s\nМестоположение: %s\nTraceback: %s",
#             error_info.exception_name,
#             error_info.exception_message,
#             error_info.error_location.replace("\n", " | "),
#             error_info.traceback_snippet,
#         )
#
#         # Уведомление пользователя
#         await self._notify_user(error_info)
#
#         # Уведомление администраторов
#         await self._notify_admins(error_info)
#
#     async def _notify_user(self, error_info: ErrorInfo) -> None:
#         update = error_info.update.update if error_info.update else None
#         if not update:
#             logger.warning("Нет update для уведомления пользователя")
#             return
#
#         user_message = (
#             "Извините, произошла непредвиденная ошибка. 😥\nПопробуйте позже."
#         )
#         try:
#             if update.message:
#                 await update.message.answer(
#                     user_message, reply_markup=get_main_menu_keyboard()
#                 )
#                 logger.info("Сообщение об ошибке отправлено пользователю (Message)")
#             elif update.callback_query and update.callback_query.message:
#                 await update.callback_query.message.answer(
#                     user_message, reply_markup=get_main_menu_keyboard()
#                 )
#                 logger.info(
#                     "Сообщение об ошибке отправлено пользователю (CallbackQuery)"
#                 )
#             else:
#                 logger.warning("Неизвестный тип update: %s", type(update))
#         except Exception as e:
#             logger.error("Ошибка при отправке сообщения пользователю: %s", str(e))
#
#     async def _notify_admins(self, error_info: ErrorInfo) -> None:
#         from shared.config import settings
#
#         user_id, user_name, user_message = error_info.get_user_info()
#
#         admin_message = (
#             f"⚠️ <b>Ошибка в боте!</b>\n\n"
#             f"⏰ <b>Время:</b> {error_info.error_time}\n\n"
#             f"👤 <b>Пользователь:</b> {user_name or 'Неизвестно'}\n"
#             f"🆔 <b>ID:</b> {user_id or 'Неизвестно'}\n"
#             f"💬 <b>Сообщение:</b> {user_message or 'Неизвестно'}\n\n"
#             f"❌ <b>Тип ошибки:</b> {error_info.exception_name}\n"
#             f"📝 <b>Описание:</b> {error_info.exception_message}\n\n"
#             f"📍 <b>Местоположение:</b>\n{error_info.error_location}\n\n"
#             f"📚 <b>Трейсбек:</b>\n<pre>{error_info.traceback_snippet}</pre>"
#         )
#
#         try:
#             await self.bot.send_message(
#                 settings.admin_chat_id,  # Убедитесь, что добавили ADMIN_CHAT_ID в settings
#                 admin_message,
#                 parse_mode="HTML",
#             )
#             logger.info("Сообщение отправлено администратору")
#         except Exception as e:
#             logger.error("Не удалось отправить сообщение администратору: %s", str(e))
#
#
# # Остальные обработчики (без изменений)
# async def handle_db_error(message_or_callback, operation: str):
#     user_id = message_or_callback.from_user.id
#     logger.error(f"Database error during {operation} for user {user_id}")
#     text = "Произошла ошибка при работе с базой данных. Попробуйте позже."
#     if isinstance(message_or_callback, Message):
#         await message_or_callback.answer(text, reply_markup=get_main_menu_keyboard())
#     elif isinstance(message_or_callback, CallbackQuery):
#         await message_or_callback.message.answer(
#             text, reply_markup=get_main_menu_keyboard()
#         )
#         await message_or_callback.answer("Ошибка БД", show_alert=True)
#
#
# @router.message(CommandStart())
# async def command_start_handler(message: Message) -> None:
#     try:
#         await get_or_create_user(message.from_user.id, message.from_user.username)
#         await message.answer(
#             f"Привет, {message.from_user.full_name}! 👋\n\n"
#             "Я бот для мониторинга доступности сайтов. "
#             "Я буду проверять ваши сайты каждые несколько минут и сообщать, "
#             "если какой-то из них станет недоступен.\n\n"
#             "Используйте кнопки ниже для управления:",
#             reply_markup=get_main_menu_keyboard(),
#         )
#     except Exception as e:
#         logger.error(
#             f"Error in start command for {message.from_user.id}: {e}", exc_info=True
#         )
#         await handle_db_error(message, "start command")
#
#
# # @router.message(CommandStart())
# # async def command_start_handler(message: Message) -> None:
# #     raise Exception("Тестовая ошибка в command_start_handler")
#
#
# @router.callback_query(F.data == "to_start")
# async def to_start_callback(callback: CallbackQuery):
#     """Обработчик кнопки 'В начало'."""
#     try:
#         await get_or_create_user(callback.from_user.id, callback.from_user.username)
#         text = (
#             f"Привет, {callback.from_user.full_name}! 👋\n\n"
#             "Вы вернулись в главное меню. Используйте кнопки ниже:"
#         )
#         try:
#             await callback.message.edit_text(
#                 text,
#                 reply_markup=get_main_menu_keyboard(),
#             )
#         except TelegramBadRequest:
#             # Если сообщение не изменилось, просто отвечаем на callback
#             await callback.message.answer(text, reply_markup=get_main_menu_keyboard())
#             await callback.message.delete()  # Удаляем старое сообщение
#
#     except Exception as e:
#         logger.error(
#             f"Error in to_start for user {callback.from_user.id}: {e}", exc_info=True
#         )
#         await callback.message.answer(
#             "Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu_keyboard()
#         )
#     finally:
#         await callback.answer()
#
#
# @router.callback_query(F.data == "add_site")
# async def add_site_callback(callback: CallbackQuery, state: FSMContext):
#     """Начинает процесс добавления сайта."""
#     await callback.message.edit_text(
#         "Пожалуйста, отправьте URL сайта, который вы хотите отслеживать "
#         "(например, https://google.com):",
#         reply_markup=get_back_keyboard(),  # Добавляем кнопку "В начало"
#     )
#     await state.set_state(AddSite.waiting_for_url)
#     await callback.answer()
#
#
# @router.message(AddSite.waiting_for_url)
# async def process_url(message: Message, state: FSMContext):
#     """Обрабатывает введенный URL, добавляет и проверяет сайт."""
#     url = message.text.strip().lower()  # Приводим к нижнему регистру для унификации
#     await state.clear()
#
#     # Простая валидация URL
#     if not (url.startswith("http://") or url.startswith("https://")):
#         await message.answer(
#             "Неверный формат URL. Пожалуйста, отправьте URL, "
#             "начинающийся с http:// или https://.",
#             reply_markup=get_main_menu_keyboard(),
#         )
#         return
#
#     # Дополнительная валидация (простая)
#     if "." not in url[url.find("://") + 3 :]:
#         await message.answer(
#             "Похоже, в URL отсутствует домен. Пожалуйста, проверьте и отправьте снова.",
#             reply_markup=get_main_menu_keyboard(),
#         )
#         return
#
#     try:
#         async with AsyncSessionFactory() as session:
#             # 1. Получаем пользователя
#             user_stmt = select(User).filter(User.telegram_id == message.from_user.id)
#             result = await session.execute(user_stmt)
#             user = result.scalars().first()
#             if not user:  # На всякий случай, хотя /start должен был создать
#                 user = await get_or_create_user(
#                     message.from_user.id, message.from_user.username
#                 )
#
#             # 2. Проверяем, существует ли сайт у этого пользователя
#             site_stmt = select(Site).filter(Site.user_id == user.id, Site.url == url)
#             result = await session.execute(site_stmt)
#             existing_site = result.scalars().first()
#
#             if existing_site:
#                 await message.answer(
#                     f"Сайт {url} уже отслеживается.",
#                     reply_markup=get_main_menu_keyboard(),
#                 )
#                 return
#
#             # 3. Добавляем новый сайт
#             new_site = Site(url=url, user_id=user.id)
#             session.add(new_site)
#             await session.flush()  # Получаем ID нового сайта
#             site_id = new_site.id
#
#             # 4. Проверяем доступность и обновляем статус
#             is_available = await update_site_availability(session, site_id, url)
#             status_text = "доступен" if is_available else "недоступен"
#
#             # 5. Коммитим все изменения
#             await session.commit()
#
#             await message.answer(
#                 f"Сайт {url} успешно добавлен! Текущий статус: {status_text}.",
#                 reply_markup=get_main_menu_keyboard(),
#             )
#
#     except Exception as e:
#         logger.error(
#             f"Error adding site {url} for {message.from_user.id}: {e}", exc_info=True
#         )
#         await handle_db_error(message, "adding site")
#
#
# @router.callback_query(F.data == "list_sites")
# async def list_sites_callback(callback: CallbackQuery):
#     """Показывает список сайтов пользователя."""
#     try:
#         sites = await get_user_sites(callback.from_user.id)
#         keyboard = get_sites_keyboard(sites)
#         text = (
#             "Ваши сайты (нажмите, чтобы удалить):"
#             if sites
#             else "У вас пока нет сайтов для отслеживания."
#         )
#
#         try:
#             await callback.message.edit_text(text, reply_markup=keyboard)
#         except TelegramBadRequest as e:
#             logger.warning(f"Failed to edit message for list_sites (no change?): {e}")
#             # Если не удалось отредактировать (например, текст тот же), просто отвечаем
#             await callback.answer()
#
#     except Exception as e:
#         logger.error(
#             f"Error listing sites for {callback.from_user.id}: {e}", exc_info=True
#         )
#         await handle_db_error(callback, "listing sites")
#     finally:
#         # Всегда отвечаем на callback, чтобы убрать 'часики'
#         await callback.answer()
#
#
# @router.callback_query(F.data.startswith("delete_site_"))
# async def delete_site_callback(callback: CallbackQuery):
#     """Удаляет сайт по ID."""
#     try:
#         site_id_str = callback.data.split("_")[2]
#         site_id = int(site_id_str)
#     except (IndexError, ValueError):
#         logger.error(f"Invalid callback data received: {callback.data}")
#         await callback.answer("Ошибка: неверные данные.", show_alert=True)
#         return
#
#     try:
#         success = await delete_site_by_id(site_id, callback.from_user.id)
#         if success:
#             await callback.answer("Сайт удален.", show_alert=False)
#             # Обновляем список сайтов после удаления
#             sites = await get_user_sites(callback.from_user.id)
#             keyboard = get_sites_keyboard(sites)
#             text = (
#                 "Ваши сайты (нажмите, чтобы удалить):"
#                 if sites
#                 else "У вас больше нет сайтов для отслеживания."
#             )
#             await callback.message.edit_text(text, reply_markup=keyboard)
#         else:
#             await callback.answer(
#                 "Не удалось удалить сайт (возможно, он уже удален).", show_alert=True
#             )
#
#     except TelegramBadRequest as e:
#         logger.warning(f"Failed to edit message after delete (maybe no change?): {e}")
#         await callback.answer("Сайт удален.")  # Все равно подтверждаем удаление
#     except Exception as e:
#         logger.error(
#             f"Error deleting site {site_id} for {callback.from_user.id}: {e}",
#             exc_info=True,
#         )
#         await callback.answer(
#             "Не удалось удалить сайт. Попробуйте позже.", show_alert=True
#         )
#         await handle_db_error(callback, "deleting site")
# Изменения: Убраны ссылки на Celery, обновлены импорты из shared/
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from bot.fsm import AddSite
from bot.keyboards import get_main_menu_keyboard, get_sites_keyboard, get_back_keyboard
from shared.db import (
    get_or_create_user,
    add_site_to_user,
    get_user_sites,
    delete_site_by_id,
    AsyncSessionFactory,
)
from shared.models import User, Site
from shared.utils import send_notification_async
import traceback
import logging
from typing import Optional

router = Router()
logger = logging.getLogger("WebsiteMonitorBot")


class ErrorInfo:
    def __init__(self, exception: Exception, update: Optional[object] = None):
        self.exception = exception
        self.update = update
        self.traceback_info = traceback.format_exc()

    def _get_error_location(self) -> str:
        tb = traceback.extract_tb(self.exception.__traceback__)
        last_call = tb[-1]
        filename = last_call.filename
        line = last_call.lineno
        func = last_call.name
        code_line = last_call.line.strip() if last_call.line else "???"
        return f"{filename}:{line} ({func}): {code_line}"

    def _format_traceback(self, max_length: int = 2000) -> str:
        tb_lines = self.traceback_info.splitlines()
        snippet = "\n".join(tb_lines[-10:])
        return snippet[:max_length]

    def get_user_info(self) -> tuple[Optional[int], Optional[str], Optional[str]]:
        if not self.update:
            return None, None, None
        update = self.update.update
        user_id = (
            getattr(update, "from_user", None).id
            if hasattr(update, "from_user")
            else None
        )
        username = (
            getattr(update, "from_user", None).username
            if hasattr(update, "from_user")
            else None
        )
        return user_id, username, None


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        "Добро пожаловать! Используйте меню для управления сайтами.",
        reply_markup=get_main_menu_keyboard(),
    )


@router.callback_query(F.data == "to_start")
async def to_start_callback(callback: CallbackQuery):
    text = "Главное меню"
    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "add_site")
async def add_site_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите URL сайта для мониторинга:", reply_markup=get_back_keyboard()
    )
    await state.set_state(AddSite.waiting_for_url)


@router.message(AddSite.waiting_for_url)
async def process_url(message: Message, state: FSMContext):
    url = message.text.strip().lower()
    async with AsyncSessionFactory() as session:
        try:
            user = await get_or_create_user(
                message.from_user.id, message.from_user.username
            )
            site = await add_site_to_user(message.from_user.id, url)
            if site:
                status_text = "доступен" if site.is_available else "недоступен"
                await message.answer(
                    f"Сайт {url} добавлен! Статус: {status_text}",
                    reply_markup=get_main_menu_keyboard(),
                )
            else:
                await message.answer(
                    "Сайт уже добавлен или произошла ошибка.",
                    reply_markup=get_main_menu_keyboard(),
                )
        except Exception as e:
            logger.error(f"Error adding site: {str(e)}")
            await message.answer(
                "Произошла ошибка при добавлении сайта.",
                reply_markup=get_main_menu_keyboard(),
            )
        await state.clear()


@router.callback_query(F.data == "list_sites")
async def list_sites_callback(callback: CallbackQuery):
    sites = await get_user_sites(callback.from_user.id)
    if sites:
        keyboard = get_sites_keyboard(sites)
        await callback.message.edit_text("Ваши сайты:", reply_markup=keyboard)
    else:
        await callback.message.edit_text(
            "У вас нет добавленных сайтов.", reply_markup=get_main_menu_keyboard()
        )


@router.callback_query(F.data.startswith("delete_site_"))
async def delete_site_callback(callback: CallbackQuery):
    site_id = int(callback.data.split("_")[2])
    success = await delete_site_by_id(site_id, callback.from_user.id)
    if success:
        await callback.message.edit_text(
            "Сайт удален!", reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.message.edit_text(
            "Ошибка при удалении сайта.", reply_markup=get_main_menu_keyboard()
        )
