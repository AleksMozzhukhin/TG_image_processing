import gettext
import os
import sys
from pathlib import Path

import supabase as sb
from aiogram import F, Router, html
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..keyboards_buttons import language_buttons, menu_buttons
from .button_states import DelNoise_States, Form

user_langs = {}

start = Router()


def set_locale(locale_name):
    """Set locale for particular user."""
    locales_path = os.path.join(os.path.dirname(__file__), "locales")

    try:
        translation = gettext.translation(
            "bot", localedir=locales_path, languages=[locale_name], fallback=True
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


@start.message(CommandStart())
async def command_start(
    message: Message, state: FSMContext, supabase_client: sb.Client
) -> None:
    """Обработка команды /start - сначала выбор языка."""
    await state.set_state(Form.set_language)
    await message.answer(
        "Пожалуйста, выберите язык / Please choose your language:",
        reply_markup=language_buttons(),
    )


@start.callback_query(Form.set_language, F.data.startswith("lang_"))
async def process_language_selection(
    callback: CallbackQuery, state: FSMContext, supabase_client: sb.Client
):
    """Обработка выбора языка."""
    language = callback.data.split("_")[1]
    user_langs[callback.from_user.id] = language
    set_locale(language)

    await callback.message.edit_text(
        text="Выбран русский язык" if language == "RU" else "English language selected",
        reply_markup=None,
    )
    await callback.message.answer("Выберите действие:", reply_markup=menu_buttons())

    print("await choose action finished\n")

    await state.set_state(Form.is_choosing)
    await callback.answer()


@start.message(Form.buttons)
async def show_main_menu(message: Message):
    """Показ главного меню по текстовому сообщению от пользователя."""
    await message.answer("Выберите действие:", reply_markup=menu_buttons())

    print("SHOW_MAIN_MENU\n")
    return
