from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
import supabase as sb
import io

from ..keyboards_buttons import menu_buttons
from .button_states import Form, DelNoise_States
from tempfile import mkdtemp
from ..ML_component import main_model

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
    
    try:
        image_bytes_io = await message.bot.download(photo.file_id)
        print('image bytes io passed\n')
        image_bytes = image_bytes_io.read()
        print('image bytes passed\n')
        temp_dir = mkdtemp(prefix="inpainting_")

        recovered_image_np = main_model.run_inpainting_pipeline(
            damaged_image_source=image_bytes,
            output_dir=temp_dir,
            max_iters=25,
            use_gpu=False
        )
        
        if recovered_image_np is None:
            raise ValueError("Процесс восстановления вернул None")
        
        success, processed_image_bytes = cv2.imencode('.png', recovered_image_np)
        if not success:
            raise ValueError("Ошибка конвертации изображения в PNG")
        
        print('success passed\n')
        processed_image_bytes = processed_image_bytes.tobytes()
        print('tobytes passed\n')
        
            
        file_name = f"processed_{user.id}_{uuid4().hex}.jpg"
        file_path = f"users/{user.id}/{file_name}"
            
        storage_response = supabase_client.storage.from_("images").upload(
                file_path,
                processed_image,
                file_options={"content-type": "image/jpeg"}
        )

        image_url = supabase_client.storage.from_("images").get_public_url(file_path)
        
        request_data = {
            "created_at": datetime.now().isoformat(),
            "user_id": user.id,
            "request": "remove noise",
            "image_url": image_url, 
        }
        
        db_response = supabase_client.table("images").insert(request_data).execute()
        
        print('db response passed\n')
        with io.BytesIO(processed_bytes) as img_buffer:
            img_buffer.name = "restored.png"
            await message.answer_photo(
                img_buffer,
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