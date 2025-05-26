# bot/keyboards.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from shared.models import Site
from typing import List


def get_main_menu_keyboard():
    """Возвращает клавиатуру главного меню."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить сайт", callback_data="add_site")
    builder.button(text="🌐 Мои сайты", callback_data="list_sites")
    builder.adjust(1)  # Одна кнопка в ряд
    return builder.as_markup()


def get_sites_keyboard(sites: List[Site]):
    """Возвращает клавиатуру со списком сайтов и кнопкой 'В начало'."""
    builder = InlineKeyboardBuilder()
    if sites:
        for site in sites:
            # Ограничиваем длину URL в кнопке
            display_url = site.url[:35] + "..." if len(site.url) > 38 else site.url
            status_icon = "✅" if site.is_available else "❌"
            builder.button(
                text=f"{status_icon} {display_url}",
                callback_data=f"delete_site_{site.id}",
            )
    else:
        builder.button(
            text="Нет сайтов для отображения", callback_data="no_sites"
        )  # Неактивная кнопка

    # Всегда добавляем кнопку "В начало"
    builder.button(text="🏠 В начало", callback_data="to_start")
    builder.adjust(1)  # Одна кнопка в ряд
    return builder.as_markup()


def get_back_keyboard():
    """Возвращает клавиатуру с кнопкой 'В начало'."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 В начало", callback_data="to_start")
    return builder.as_markup()
