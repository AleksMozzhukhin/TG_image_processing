import os
import random
from aiogram.types import FSInputFile
from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from ..keyboards_buttons import ButtonText, menu_buttons
from .button_states import Form

magic = Router()

CATS_IMAGES_DIR = "images/cats/"

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

@magic.message(Form.buttons, F.text == ButtonText.MAGIC)
async def handle_magic_button(message: Message, state: FSMContext) -> None:
    """Используйте волшебную кнопку — отправляйте случайные фотографии котиков с милыми подписями"""
    num_images = random.randint(1, 5)
    
    #cat_images = db.get_random_cat_images(num_images)

    cat_images = [f for f in os.listdir(CATS_IMAGES_DIR) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not cat_images:
        await message.answer(_("Котики куда-то убежали... Попробуйте позже!"))
        return
    
    # Отправляем каждую картинку с случайной подписью
    for image_name in selected_images:
        image_path = os.path.join(CATS_IMAGES_DIR, image_name)
        caption = random.choice(CUTE_CAPTIONS)
        photo = FSInputFile(image_path)
        await message.answer_photo(photo, caption=caption)
    
    await message.answer(_("Вот ваша порция котиков! 😊"), 
                         reply_markup=menu_buttons())
    await state.set_state(Form.buttons)