# Без изменений, сохранена структура для совместимости
from aiogram.fsm.state import State, StatesGroup


class AddSite(StatesGroup):
    waiting_for_url = State()
