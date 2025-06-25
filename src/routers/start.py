from aiogram import Router, html, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery 
import os
import sys 
from pathlib import Path 

from keyboards_buttons import language_buttons, menu_buttons
from routers.button_states import Form

parent_dir = str(Path(__file__).parent.parent.parent)  # на два уровня выше: .parent.parent
sys.path.append(parent_dir)

from db import db_scripts, db_wares

sys.path.remove(parent_dir)  

start = Router()

@start.message(CommandStart())
async def command_start(message: Message, state: FSMContext, db: db_scripts.Database) -> None:
    """Обработка команды /start - сначала выбор языка."""
    await state.set_state(Form.set_language)
    await message.answer(
        "Пожалуйста, выберите язык / Please choose your language:",
        reply_markup=language_buttons()
    )

@start.callback_query(Form.set_language, F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery, state: FSMContext, db: db_scripts.Database):
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
    await state.set_state(Form.menu)
    await callback.answer()

@start.message(Form.menu)
async def show_main_menu(message: Message):
    """Показ главного меню."""
    await message.answer(
        "Выберите действие:",
        reply_markup=menu_buttons()
    )