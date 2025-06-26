from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


class ButtonText:
    """Текст кнопочек в телеграмме"""

    REMOVE_NOISE = "Удалить шум с изображения"
    GENERATE_IMAGE = "Сгенерировать новое изображение"
    VIEW_HISTORY = "Посмотреть историю"
    MAGIC = "Магия"

    SET_EN = "English"
    SET_RU = "Русский"


def menu_buttons() -> InlineKeyboardMarkup:
    """Inline-клавиатура для основного меню"""
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки с callback_data
    builder.row(
        InlineKeyboardButton(text=ButtonText.REMOVE_NOISE, callback_data="remove_noise")
    )
    builder.row(
        InlineKeyboardButton(
            text=ButtonText.GENERATE_IMAGE, callback_data="generate_image"
        )
    )
    builder.row(
        InlineKeyboardButton(text=ButtonText.VIEW_HISTORY, callback_data="view_history")
    )
    builder.row(
        InlineKeyboardButton(text=ButtonText.MAGIC, callback_data="magic_action")
    )
    return builder.as_markup()


def language_buttons() -> InlineKeyboardMarkup:
    """Показ кнопок выбора языка (инлайн клавиатура)"""
    builder = InlineKeyboardBuilder()

    builder.button(text=ButtonText.SET_RU, callback_data="lang_ru_RU")
    builder.button(text=ButtonText.SET_EN, callback_data="lang_en_EN")

    builder.adjust(2)
    return builder.as_markup()
