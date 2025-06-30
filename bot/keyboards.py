from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from shared.models import Site
from typing import List


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Добавить сайт", callback_data="add_site")
    builder.button(text="Мои сайты", callback_data="list_sites")
    builder.adjust(2)
    return builder.as_markup()


def get_sites_keyboard(sites: List[Site]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for site in sites:
        display_url = site.url[:35] + "..." if len(site.url) > 38 else site.url
        status_icon = "✅" if site.is_available else "❌"
        builder.button(
            text=f"{status_icon} {display_url}", callback_data=f"site_{site.id}"
        )
        builder.button(text=f"Удалить", callback_data=f"delete_site_{site.id}")
    builder.button(text="Назад", callback_data="to_start")
    builder.adjust(2)
    return builder.as_markup()


def get_back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data="to_start")
    return builder.as_markup()
