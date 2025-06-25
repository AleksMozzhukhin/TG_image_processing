from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder


class ButtonText:
    """Текст кнопочок в телеграмме"""

    REMOVE_NOISE = "Удалить шум с изображения"
    GENERATE_IMAGE = "Сгенерировать новое изображение"
    VIEW_HISTORY = "Посмотреть историю"
    MAGIC =  "Магия"

    SET_EN = "English"
    SET_RU = "Русский"


def menu_buttons() -> ReplyKeyboardMarkup:
    """Показ кнопок  выбора основынх действий"""
    builder = ReplyKeyboardBuilder()

    builder.add(KeyboardButton(text=ButtonText.REMOVE_NOISE))
    builder.add(KeyboardButton(text=ButtonText.GENERATE_IMAGE))
    builder.add(KeyboardButton(text=ButtonText.VIEW_HISTORY))
    builder.add(KeyboardButton(text=ButtonText.MAGIC))
    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)

def language_buttons() -> ReplyKeyboardMarkup:
    """Показ кнопок выбора языка"""
    builder = ReplyKeyboardBuilder()

    builder.add(KeyboardButton(text=ButtonText.SET_EN))
    builder.add(KeyboardButton(text=ButtonText.SET_RU))
    builder.adjust(1)
