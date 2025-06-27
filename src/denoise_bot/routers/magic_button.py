import os
import random
from aiogram.types import FSInputFile
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.denoise_bot.routers.keyboards_buttons import ButtonText, menu_buttons
from .button_states import Form

magic = Router()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATS_IMAGES_DIR = os.path.join(BASE_DIR, "cats")

CUTE_CAPTIONS = [
    "Мур-мур-мур! 😻",
    "Котька в ударе!",
    "Пушистый комочек счастья 🐾",
    "Ты сегодня молодец, как этот котик!",
    "Мягкий и пушистый, как твое настроение сейчас!",
    "Котик одобряет твой выбор!",
    "Умиротворение в каждом взгляде 😊",
    "Ты заслужил этого котика!",
    "Пушистый антистресс в твоем чатике!",
    "Мурчание передается через фото!",
]

@magic.callback_query(Form.is_choosing, F.data.startswith("magic_action"))
async def handle_magic_button(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик нажатия на кнопку - отправляет котиков сразу"""
    await callback.answer()
    
    try:
        cat_images = [f for f in os.listdir(CATS_IMAGES_DIR) 
                     if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        if not cat_images:
            await callback.message.answer(_("Котики куда-то убежали... Попробуйте позже!"))
            return

        num_images = min(random.randint(1, 5), len(cat_images))
        selected_images = random.sample(cat_images, num_images)

        for image_name in selected_images:
            image_path = os.path.join(CATS_IMAGES_DIR, image_name)
            caption = random.choice(CUTE_CAPTIONS)
            photo = FSInputFile(image_path)
            await callback.message.answer_photo(photo, caption=caption)
        
        await callback.message.answer(_("Вот ваша порция котиков! 😊"),
                             reply_markup=menu_buttons())

        await state.set_state(Form.is_choosing)

    except Exception as e:
        await callback.message.answer(_("Произошла ошибка при загрузке котиков 😿"))