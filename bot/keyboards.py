from aiogram.utils.keyboard import InlineKeyboardBuilder
from shared.models import Site
from typing import List


def get_main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить сайт", callback_data="add_site")
    builder.button(text="🌐 Мои сайты", callback_data="list_sites")
    builder.button(text="🏠 В начало", callback_data="to_start")
    builder.adjust(1)  # Одна кнопка в столбец
    return builder.as_markup()


def get_sites_keyboard(sites: List[Site]):
    builder = InlineKeyboardBuilder()
    if not sites:
        builder.button(text="🏠 В начало", callback_data="to_start")
        return builder.as_markup()
    for site in sites:
        # Ограничиваем длину URL в кнопке
        display_url = site.url[:35] + "..." if len(site.url) > 38 else site.url
        builder.button(text=f"❌ {display_url}", callback_data=f"delete_site_{site.id}")
    builder.button(text="🏠 В начало", callback_data="to_start")
    builder.adjust(1)  # Одна кнопка в столбец
    return builder.as_markup()
