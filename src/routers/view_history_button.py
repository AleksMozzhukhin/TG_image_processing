from aiogram import Router, html, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
import supabase as sb

from ..keyboards_buttons import menu_buttons, ButtonText
from .button_states import Form

view_history = Router()

@view_history.message(Form.buttons, F.text == ButtonText.VIEW_HISTORY)
async def show_history(message: Message, state: FSMContext, supabase_client: sb.Client):
    """Показать историю запросов пользователя"""
    user_id = message.from_user.id
    
    try:
        response = supabase_client.table("images")\
            .select("request, created_at, image_url")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        
        history_items = response.data
        
        if not history_items:
            await message.answer("У вас еще нет истории запросов.")
            return
            
        # Создаем инлайн-кнопки для каждого запроса
        builder = InlineKeyboardBuilder()
        for item in history_items:
            timestamp = datetime.fromisoformat(item['created_at']).strftime("%d.%m.%Y %H:%M")
            button_text = f"{item['request'][:30]}... ({timestamp})"
            builder.add(InlineKeyboardButton(
                text=button_text,
                callback_data=f"show_image:{item['image_url']}"
            ))
        builder.row(InlineKeyboardButton(
            text="🚪 Выйти из истории",
            callback_data="exit_history"
        ))
        
        builder.adjust(1)  # По одной кнопке в строке
        await message.answer(
            "Ваши предыдущие запросы:",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        await message.answer(f"Ошибка при получении истории: {str(e)}")

@view_history.callback_query(F.data.startswith("show_image:"))
async def handle_history_select(callback: CallbackQuery):
    """Показать выбранное изображение из истории"""
    async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
            response.raise_for_status()
            image_data = response.content
        
        # 2. Создаем объект для отправки через Telegram
    image_file = BufferedInputFile(
            file=image_data,
            filename="generated_image.png"
        )
        
    # 3. Отправляем изображение
    await callback.message.answer_photo(
            image_file,
            caption="Результат вашего запроса"
        )
    await state.set_state(Form.menu)
    await callback.answer()

@view_history.callback_query(F.data == "exit_history")
async def handle_exit_history(callback: CallbackQuery):
    """Выход из режима просмотра истории"""
    await callback.message.edit_text(
        "Вы вернулись в главное меню:",
        reply_markup=None  # Удаляем инлайн-клавиатуру
    )
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=menu_buttons()
    )
    await state.set_state(Form.menu)
    await callback.answer()