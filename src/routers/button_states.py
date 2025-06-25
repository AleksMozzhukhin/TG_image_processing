from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    """Состояния кнопки старт"""
    set_language = State()
    menu = State()
    buttons = State()
