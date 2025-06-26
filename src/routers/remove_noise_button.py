from aiogram import Router, html, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile
import supabase as sb
import cv2
import datetime
import io
import uuid
import numpy as np

from ..keyboards_buttons import menu_buttons, ButtonText
from .button_states import Form, DelNoise_States
from tempfile import mkdtemp
from ML_component import main_model


remove_noise = Router()


@remove_noise.callback_query(Form.is_choosing, F.data.startswith("remove_noise"))
async def handle_remove_noise(callback: CallbackQuery, state: FSMContext) -> None:
    print('\nENTRED HRNOISE\n')
    """Удалить шум с изображения, начало обработки"""
    await callback.message.answer(
        "Загрузите вышу картинку",
        reply_markup=None
    )
    await state.set_state(DelNoise_States.get_image)

@remove_noise.message(DelNoise_States.get_image, F.photo)
async def process_received_image(message: Message, state: FSMContext, supabase_client: sb.Client) -> None:
    photo: PhotoSize = message.photo[-1]
    user = message.from_user
    
    try:
        image_bytes_io = await message.bot.download(photo.file_id)
        image_bytes = image_bytes_io.read()
        
        temp_dir = mkdtemp(prefix="inpainting_")
        recovered_image_np = main_model.run_inpainting_pipeline(
            damaged_image_source=io.BytesIO(image_bytes),
            output_dir=temp_dir,
            max_iters=5,
            use_gpu=False
        )

        if recovered_image_np is None:
            raise ValueError("Модель вернула None")

        print(f"Исходный формат: {recovered_image_np.shape}, {recovered_image_np.dtype}")
        
        if recovered_image_np.dtype == np.float64:
            recovered_image_np = (255 * (recovered_image_np - recovered_image_np.min()) / 
                                (recovered_image_np.max() - recovered_image_np.min()))
            recovered_image_np = recovered_image_np.astype(np.uint8)
        
        if len(recovered_image_np.shape) == 3 and recovered_image_np.shape[-1] == 3:
            recovered_image_np = cv2.cvtColor(recovered_image_np, cv2.COLOR_BGR2RGB)

        success, encoded_img = cv2.imencode('.jpg', recovered_image_np)
        if not success:
            raise ValueError("Ошибка кодирования jpg")

        processed_image_bytes = encoded_img.tobytes()
        print('tobytes passed\n')
          
        file_name = f"processed_{user.id}_{uuid.uuid4().hex}.jpg"
        file_path = f"users/{user.id}/{file_name}"

        print("\n", file_path, "\n", "file path")

        storage_response = supabase_client.storage.from_("images").upload(
            path=file_path,
            file=processed_image_bytes,
            file_options={"content-type": "image/*"}
        )

        print('storage response passed\n')
        print(storage_response)

        image_url = supabase_client.storage.from_("images").get_public_url(file_path)
        
        request_data = {
            "created_at": datetime.datetime.now().isoformat(),
            "user_id": user.id,
            "request": "remove noise",
            "image_url": image_url, 
        }

        print('request data passed\n')
        
        db_response = supabase_client.table("images").insert(request_data).execute()
        
        print('db response passed\n')
        photo_file = BufferedInputFile(
            file=encoded_img.tobytes(),
            filename="result.jpg"
        )

        await message.answer_photo(
            photo=photo_file,
            caption="✅ Результат обработки"
        )

    except Exception as e:
        await message.answer(f"Ошибка обработки: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        if 'temp_dir' in locals():
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    await state.set_state(Form.buttons)