from aiogram import Router, html, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery 
import os
import sys 
from pathlib import Path 
import supabase as sb
import gettext

from keyboards_buttons import language_buttons, menu_buttons
from routers.button_states import Form
 
user_langs = {} 

start = Router()

def set_locale(locale_name):
    """Set locale for particular user."""
    locales_path = os.path.join(os.path.dirname(__file__), 'locales')

    try:
        translation = gettext.translation(
            "bot",
            localedir=locales_path,
            languages=[locale_name],
            fallback=True
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
async def command_start(message: Message, state: FSMContext, supabase_client: sb.Client) -> None:
    """Обработка команды /start - сначала выбор языка."""
    await state.set_state(Form.set_language)
    await message.answer(
        "Пожалуйста, выберите язык / Please choose your language:",
        reply_markup=language_buttons()
    )

@start.callback_query(Form.set_language, F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery, state: FSMContext, supabase_client: sb.Client):
    """Обработка выбора языка."""
    language = callback.data.split("_")[1]  
    user_langs[callback.from_user.id] = language
    set_locale(language)
    
    await callback.message.edit_text(
        text="Выбран русский язык" if language == "ru_RU" else "English language selected",
        reply_markup=None  
    )
    await show_main_menu(callback.message) 
    await state.set_state(Form.menu)
    await callback.answer()

@start.message(Form.menu)
async def show_main_menu(message: Message):
    """Показ главного меню."""
    await message.answer(
        "Выберите действие:",
        reply_markup=menu_buttons()
    )