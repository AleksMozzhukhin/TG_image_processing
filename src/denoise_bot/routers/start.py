import gettext
import os

import supabase as sb
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from .button_states import Form

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

start = Router()

locales_path = os.path.join(os.path.dirname(__file__), "locales")
translation = gettext.translation("translations", localedir=locales_path, fallback=True)
_, ngettext = translation.gettext, translation.ngettext
user_langs = {}


def set_locale(locale_name):
    """Set locale for particular user."""
    locales_path = os.path.join(os.path.dirname(__file__), "locales")

    try:
        translation = gettext.translation(
            "translations", localedir=locales_path, languages=[locale_name], fallback=True
        )
        translation.install()
        global _
        global ngettext
        _ = translation.gettext
        ngettext = translation.ngettext
    except Exception as e:
        print(f"Locale error: {e}")
        translation = gettext.NullTranslations()
        translation.install()
        _ = translation.gettext
        ngettext = translation.ngettext

class ButtonText:
    """Текст кнопочек в телеграмме"""

    SET_EN = "English"
    SET_RU = "Русский"


def menu_buttons() -> InlineKeyboardMarkup:
    """Inline-клавиатура для основного меню"""
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки с callback_data
    builder.row(
        InlineKeyboardButton(text=_("Удалить шум с изображения"), callback_data="remove_noise")
    )
    builder.row(
        InlineKeyboardButton(text=_("Сгенерировать изображение"), callback_data="generate_image")
    )
    builder.row(
        InlineKeyboardButton(text=_("Посмотреть историю"), callback_data="view_history")
    )
    builder.row(
        InlineKeyboardButton(text=_("Магия"), callback_data="magic_action")
    )
    return builder.as_markup()


def language_buttons() -> InlineKeyboardMarkup:
    """Показ кнопок выбора языка (инлайн клавиатура)"""
    builder = InlineKeyboardBuilder()

    builder.button(text=ButtonText.SET_RU, callback_data="lang_ru_RU")
    builder.button(text=ButtonText.SET_EN, callback_data="lang_en_EN")

    builder.adjust(2)
    return builder.as_markup()


@start.message(CommandStart())
async def command_start(message: Message, state: FSMContext, supabase_client: sb.Client) -> None:
    """Обработка команды /start - сначала выбор языка."""
    await state.set_state(Form.set_language)
    await message.answer(
        "Пожалуйста, выберите язык / Please choose your language:",
        reply_markup=language_buttons(),
    )


@start.callback_query(Form.set_language, F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery, state: FSMContext, supabase_client: sb.Client):
    """Обработка выбора языка."""
    language = callback.data.split("_")[1]
    user_langs[callback.from_user.id] = language
    set_locale(language)

    await callback.message.edit_text(text=_("Выбран русский язык"), reply_markup=None)
    await callback.message.answer(_("Выберите действие:"), reply_markup=menu_buttons())

    await state.set_state(Form.is_choosing)
    await callback.answer()


@start.message(Form.buttons)
async def show_main_menu(message: Message):
    """Показ главного меню по текстовому сообщению от пользователя."""
    print("_SHOW MAIN MENU_")
    await message.answer(_("Выберите действие:"), reply_markup=menu_buttons())
