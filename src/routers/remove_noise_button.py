from aiogram import Router, html, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile
import supabase as sb
import cv2
import datetime
import io
import uuid

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
    """Обработка полученного изображения."""
    photo: PhotoSize = message.photo[-1]
    user = message.from_user
    try:
        image_bytes_io = await message.bot.download(photo.file_id)
        print('image bytes io passed\n')
        image_bytes = image_bytes_io.read()
        print('image bytes passed\n')
        temp_dir = mkdtemp(prefix="inpainting_")

        recovered_image_np = main_model.run_inpainting_pipeline(
            damaged_image_source=io.BytesIO(image_bytes),
            output_dir=temp_dir,
            max_iters=25,
            use_gpu=False
        )

        print('recovered image finished\n')
        
        if recovered_image_np is None:
            raise ValueError("Процесс восстановления вернул None")
        
        success, processed_image_bytes = cv2.imencode('.png', recovered_image_np)

        print('cv2 finished\n')
        if not success:
            raise ValueError("Ошибка конвертации изображения в PNG")
        
        print('success passed\n')
        processed_image_bytes = processed_image_bytes.tobytes()
        print('tobytes passed\n')
        
            
        file_name = f"processed_{user.id}_{uuid.uuid4().hex}.png"
        file_path = f"users/{user.id}/{file_name}"

        # storage_response = supabase_client.storage.from_("images").upload(
        #     path=file_path,
        #     file=processed_image_bytes,
        #     file_options={"content-type": "image/png"}
        # )

        print('storage response passed\n')

        image_url = "https://google.com" # supabase_client.storage.from_("images").get_public_url(file_path)
        
        request_data = {
            "created_at": datetime.datetime.now().isoformat(),
            "user_id": user.id,
            "request": "remove noise",
            "image_url": image_url, 
        }

        print('request data passed\n')
        
        db_response = supabase_client.table("images").insert(request_data).execute()
        
        print('db response passed\n')
        with io.BytesIO(processed_image_bytes) as img_buffer:

            photo_file = BufferedInputFile(
                file=processed_image_bytes,
                filename="restored.png"
            )

            await message.answer_photo(
                photo=photo_file,
                caption="✅ Ваше изображение восстановлено!"
            )
        print('with... passed\n')
        
    except Exception as e:
        await message.answer(_("Произошла ошибка при обработке: {error}").format(error=str(e)))
    
    await message.answer(
        "Выберите действие",
        reply_markup=menu_buttons()
    )
    await state.set_state(Form.is_choosing)