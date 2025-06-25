from aiogram import Router, html
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards_buttons import language_buttons, menu_buttons
from button_states import Form
from db import db_scripts, db_wares

start = Router()

@start_dialogue_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext, db: db_scripts.DataBase) -> None:
    """Обработка команды /start - сначала выбор языка."""
    await state.set_state(Form.set_language)
    await message.answer(
        "Пожалуйста, выберите язык / Please choose your language:",
        reply_markup=language_buttons()
    )

@start_dialogue_router.callback_query(Form.set_language, F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery, state: FSMContext, db: db_scripts.DataBase):
    """Обработка выбора языка."""
    language = callback.data.split("_")[1]  
    #db.set_user_language(callback.from_user.id, language)
    
    _.locale = language
    
    """if not db.user_exists(callback.from_user.id):
        db.add_user(callback.from_user.id, callback.from_user.full_name or "Anonymous")"""
    
    await callback.message.edit_text(
        text="Выбран русский язык" if language == "ru" else "English language selected",
        reply_markup=None  
    )
    await state.set_state(Form.main_menu)
    await callback.answer()

@start_dialogue_router.message(Form.main_menu)
async def show_main_menu(message: Message):
    """Показ главного меню."""
    await message.answer(
        "Выберите действие:",
        reply_markup=menu_buttons()
    )