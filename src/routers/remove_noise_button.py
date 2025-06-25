from aiogram import Router, html, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards_buttons import menu_buttons, ButtonText
from routers.button_states import Form, DelNoise_States
from db import db_scripts, db_wares

remove_noise = Router()

@remove_noise.message(Form.buttons, F.text == ButtonText.REMOVE_NOISE )
async def handle_remove_noise(message: Message, state: FSMContext) -> None:
    """Удалить шум с изображения, начало обработки"""
    await message.answer(
        _("Загрузите вышу картинку"),
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(DelNoise_States.get_image)

@remove_noise.message(DelNoise_States.get_image, F.photo)
async def process_received_image(message: Message, state: FSMContext) -> None:
    """Обработка полученного изображения."""
    photo: PhotoSize = message.photo[-1]
    
    await message.answer("Обрабатываю изображение...")
    
    try:
        image_bytes = await message.bot.download(photo.file_id)
        
        # Обрабатываем изображение функциями

        

        await message.answer_photo(
            enhanced_image,
            caption=_("Обработанное изображение готово!")
        )
        
    except Exception as e:
        await message.answer(_("Произошла ошибка при обработке: {error}").format(error=str(e)))
    
    await message.answer(
        "Выберите действие",
        reply_markup=menu_buttons()
    )
    await state.set_state(Form.buttons)