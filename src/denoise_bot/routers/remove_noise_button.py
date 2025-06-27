import datetime
import io
import uuid
import numpy as np

from .start import menu_buttons
from .button_states import Form, DelNoise_States
from tempfile import mkdtemp

import cv2
import numpy as np
import supabase as sb
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from ..ML_component import main_model


remove_noise = Router()


@remove_noise.callback_query(Form.is_choosing, F.data.startswith("remove_noise"))
async def handle_remove_noise(callback: CallbackQuery, state: FSMContext) -> None:
    """Удалить шум с изображения, начало обработки."""
    await callback.message.answer(_("Загрузите вашу картинку (как фото или как файл)"), reply_markup=None)
    await state.set_state(DelNoise_States.get_image)


@remove_noise.message(
    DelNoise_States.get_image,
    (F.photo) | (F.document & F.document.mime_type.startswith("image/")),
)
async def process_received_image(message: Message, state: FSMContext, supabase_client: sb.Client) -> None:
    """
    Обрабатывает полученное изображение (фото или файл).

    Скачивает изображение, запускает ML-пайплайн для восстановления,
    сохраняет результат в Supabase и отправляет его пользователю.
    """
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id
    else:
        await message.answer("Пожалуйста, отправьте изображение как фото или файл.")
        return

    user = message.from_user
    processing_msg = await message.answer(_("🔄 Ваше изображение обрабатывается..."))
    try:
        image_bytes_io = await message.bot.download(file_id)
        image_bytes = image_bytes_io.read()

        await processing_msg.edit_text(_("🔄 Обрабатываем изображение моделью..."))

        temp_dir = mkdtemp(prefix="inpainting_")
        recovered_image_np = main_model.run_inpainting_pipeline(
            damaged_image_source=io.BytesIO(image_bytes),
            output_dir=temp_dir,
            max_iters=250,
            use_gpu=True,
        )
        await processing_msg.edit_text(_("🔄 Подготавливаем результат..."))
        if recovered_image_np is None:
            raise ValueError(_("Модель вернула None"))

        if recovered_image_np.dtype == np.float64:
            min_val = recovered_image_np.min()
            max_val = recovered_image_np.max()

            if max_val - min_val > 0:
                normalized_image = (recovered_image_np - min_val) / (max_val - min_val)
                recovered_image_np = (255 * normalized_image).astype(np.uint8)
            else:
                recovered_image_np = recovered_image_np.astype(np.uint8)

        if len(recovered_image_np.shape) == 3 and recovered_image_np.shape[-1] == 3:
            recovered_image_np = cv2.cvtColor(recovered_image_np, cv2.COLOR_BGR2RGB)

        success, encoded_img = cv2.imencode(".jpg", recovered_image_np)
        if not success:
            raise ValueError(_("Ошибка кодирования jpg"))

        processed_image_bytes = encoded_img.tobytes()

        file_name = f"processed_{user.id}_{uuid.uuid4().hex}.jpg"
        file_path = f"users/{user.id}/{file_name}"

        storage_response = supabase_client.storage.from_("images").upload(
            path=file_path,
            file=processed_image_bytes,
            file_options={"content-type": "image/jpeg"},  # Указываем корректный mime-type
        )

        image_url = supabase_client.storage.from_("images").get_public_url(file_path)

        request_data = {
            "created_at": datetime.datetime.now().isoformat(),
            "user_id": user.id,
            "request": "remove noise",
            "image_url": image_url
        }

        db_response = supabase_client.table("images").insert(request_data).execute()

        photo_file = BufferedInputFile(file=encoded_img.tobytes(), filename="result.jpg")
        await processing_msg.delete()
        await message.answer_photo(photo=photo_file, caption=_("✅ Результат обработки"))

    except Exception as e:
        await processing_msg.delete()  # Удаляем сообщение "обрабатывается" даже в случае ошибки
        await message.answer("Ошибка обработки: {}".format(str(e)))
        import traceback

        traceback.print_exc()

    finally:
        if "temp_dir" in locals():
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    await message.answer("Выберите действие:", reply_markup=menu_buttons())
    await state.set_state(Form.is_choosing)
