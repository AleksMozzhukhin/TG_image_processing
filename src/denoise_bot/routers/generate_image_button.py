import base64
import uuid
from datetime import datetime

import supabase as sb
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message, ReplyKeyboardRemove
from dotenv import load_dotenv

from ..fusion_brain import FusionBrainAPI
from .start import menu_buttons
from .button_states import Form, GenImage_States
from .start import menu_buttons

load_dotenv()

generate_image = Router()

# Константы для FusionBrain API
FUSIONBRAIN_API_KEY = "E41777D35F336F1D0C2B00EB08D75F38"
FUSIONBRAIN_API_SECRET = "1E0A23558FF802583C814E5AD49C4814"
FUSIONBRAIN_URL = "https://api-key.fusionbrain.ai/key/api/v1/pipeline/run'"


@generate_image.callback_query(Form.is_choosing, F.data.startswith("generate_image"))
async def handle_generate_image(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка нажатия кнопки генерации изображения."""
    await callback.message.answer(_("Введите текст для генерации изображения:"), reply_markup=ReplyKeyboardRemove())
    await state.set_state(GenImage_States.waiting_for_prompt)


@generate_image.message(GenImage_States.waiting_for_prompt)
async def generate_image_from_text(message: Message, state: FSMContext, supabase_client: sb.Client) -> None:
    """Генерация изображения по тексту через API."""
    prompt = message.text
    user = message.from_user

    await message.answer(_("Генерирую изображение...⏳"))

    try:
        api = FusionBrainAPI("https://api-key.fusionbrain.ai/", FUSIONBRAIN_API_KEY, FUSIONBRAIN_API_SECRET)
        pipeline_id = api.get_pipeline()

        generated_uuid = api.generate(prompt, pipeline_id)
        files = api.check_generation(generated_uuid)

        image_base64 = files[0]
        image_data = base64.b64decode(image_base64)

        file_name = f"generated_{user.id}_{uuid.uuid4().hex}.png"
        file_path = f"users/{user.id}/{file_name}"

        # Загружаем изображение в Supabase
        storage_response = supabase_client.storage.from_("images").upload(
            file_path, image_data, file_options={"content-type": "image/png"}
        )

        image_url = supabase_client.storage.from_("images").get_public_url(file_path)
        request_data = {
            "created_at": datetime.now().isoformat(),
            "user_id": user.id,
            "request": prompt,
            "image_url": image_url
        }

        db_response = supabase_client.table("images").insert(request_data).execute()

        photo_file = BufferedInputFile(file=image_data, filename="result.jpg")

        await message.answer_photo(photo=photo_file, caption=_("Ваше изображение готово!"))

    except Exception as e:
        await message.answer(_("Произошла ошибка при обработке: {}").format(error=str(e)))

    await message.answer(_("Выберите действие:"), reply_markup=menu_buttons())
    await state.set_state(Form.is_choosing)
