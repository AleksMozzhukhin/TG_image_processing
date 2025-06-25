from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    """Состояния кнопки старт"""
    set_language = State()
    menu = State()
    buttons = State()

class DelNoise_States(StatesGroup): 
    """Состояния кнопки удалить шум"""
    get_image = State()
