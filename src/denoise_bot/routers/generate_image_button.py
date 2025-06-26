import base64
import os
from datetime import datetime
from io import BytesIO

import aiohttp
import supabase as sb
from aiogram import F, Router, html
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from dotenv import load_dotenv

from ..keyboards_buttons import ButtonText, menu_buttons
from .button_states import Form, GenImage_States

load_dotenv()

generate_image = Router()

# Константы для FusionBrain API
FUSIONBRAIN_API_KEY = os.getenv("FUSIONBRAIN_API_KEY")
FUSIONBRAIN_URL = "https://api.fusionbrain.ai/v1/text2image/run"


@generate_image.callback_query(Form.is_choosing, F.data.startswith("generate_image"))
async def handle_generate_image(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка нажатия кнопки генерации изображения"""
    print("ENTERED HGENIMAGE\n")

    await callback.message.answer(
        "Введите текст для генерации изображения:", reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(GenImage_States.waiting_for_prompt)


@generate_image.message(GenImage_States.waiting_for_prompt)
async def generate_image_from_text(
    message: Message, state: FSMContext, supabase_client: sb.Client
) -> None:
    """Генерация изображения по тексту через API"""
    print("entered generate image from text\n")

    prompt = message.text

    current_datetime = datetime.now()
    # datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

    await message.answer("Генерирую изображение...⏳")

    print("after genering picture\nentering try except\n")

    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {FUSIONBRAIN_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model_id": 1,  # ID модели генерации
                "params": {
                    "width": 512,
                    "height": 512,
                    "num_images": 1,
                    "text": prompt,
                },
            }

            print("async with aiohttp passed\n")

            async with session.post(
                FUSIONBRAIN_URL, json=payload, headers=headers
            ) as resp:
                print("entered async\n")
                if resp.status != 200:
                    await message.answer(_("Ошибка генерации. Попробуйте позже."))
                    return

                print("resp status 200\n")
                response_data = await resp.json()
                print("await resp\n")
                task_id = response_data.get("task_id")
                print("task_id\n")

            print("async with session passed\n")

        result_url = f"https://api.fusionbrain.ai/v1/text2image/status/{task_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(result_url, headers=headers) as resp:
                result_data = await resp.json()
                if result_data.get("status") != "SUCCESS":
                    await message.answer("Не удалось сгенерировать изображение.")
                    return

                image_base64 = result_data["images"][0]
                image_data = base64.b64decode(image_base64)

                file_name = f"generated_{user.id}_{uuid4().hex}.png"
        file_path = f"users/{user.id}/{file_name}"

        upload_response = supabase_client.storage.from_("images").upload(
            file_path, image_data, file_options={"content-type": "image/png"}
        )

        public_url = supabase_client.storage.from_("images").get_public_url(file_path)
        record_data = {
            "created_at": current_datetime.isoformat(),
            "user_id": user.id,
            "request": prompt,
            "public_url": public_url,
        }

        supabase_client.table("images").insert(record_data).execute()

        await message.answer_photo(
            BytesIO(image_data), caption="Ваше изображение готово!"
        )

    except Exception as e:
        await message.answer(
            _("Произошла ошибка при обработке: {error}").format(error=str(e))
        )

    # Возвращаем в главное меню
    await message.answer("Выберите действие:", reply_markup=menu_buttons())
    await state.set_state(Form.buttons)
