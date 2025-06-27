from aiogram import Router, html, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
import datetime
import supabase as sb
import httpx
from aiogram.types import BufferedInputFile

from .start import menu_buttons
from .button_states import Form, History_state

view_history = Router()

@view_history.callback_query(Form.is_choosing, F.data.startswith("view_history"))
async def handle_view_history(callback: CallbackQuery, state: FSMContext, supabase_client: sb.Client):
    """Показать историю запросов пользователя"""
    user_id = callback.from_user.id
    try:
        await callback.answer() 
        response = supabase_client.table("images")\
            .select("id, request, created_at, image_url")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        
        history_items = response.data
        history_data = {}

        if not history_items:
            await callback.message.answer(_("У вас еще нет истории запросов."))
            return
        
        builder = InlineKeyboardBuilder()
        for item in history_items:
            item_id = str(item['id'])
            timestamp = datetime.datetime.fromisoformat(item['created_at']).strftime("%d.%m.%Y %H:%M")
            button_text = f"{item['request'][:]}... ({timestamp})"[:64]

            history_data[item_id] = {
                'image_url': item['image_url'],
                'request': item['request']
            }

            builder.add(InlineKeyboardButton(
                text=button_text,
                callback_data=f"show_image:{item_id}"
            ))
        await state.update_data(history_data=history_data)
        builder.row(InlineKeyboardButton(
            text=_("🚪 Выйти из истории"),
            callback_data="exit_history"
        ))
        
        builder.adjust(1)
        await callback.message.answer(
            _("Ваши предыдущие запросы:"),
            reply_markup=builder.as_markup()
        )
        await state.set_state(History_state)
        #await callback.answer()
        
    except Exception as e:
        await callback.message.answer(_("Ошибка при получении истории: {}").format(str(e)))
        await callback.answer()

@view_history.callback_query(History_state, F.data.startswith("show_image:"))
async def handle_history_select(callback: CallbackQuery, state: FSMContext):
    """Показать выбранное изображение из истории"""
    try:
        await callback.answer()
        item_id = callback.data.split(":")[1]

        state_data = await state.get_data()
        history_data = state_data.get('history_data', {})
        item = history_data.get(item_id)
        
        if not item:
            await callback.answer(_("❌ Изображение не найдено"), show_alert=True)
            return
        
        async with httpx.AsyncClient() as client:
            response = await client.get(item['image_url'])
            response.raise_for_status()
            image_data = response.content
        
        await callback.message.answer_photo(
            BufferedInputFile(
            file=image_data,
            filename="downloaded_image.png"
        ),
            caption=_("🖼️ Запрос: {}").format(item['request'][:200])
        )
        #builder = InlineKeyboardBuilder()
        # for item_id, item_data in history_data.items():
        #     timestamp = datetime.datetime.fromisoformat(item_data['created_at']).strftime("%d.%m %H:%M")
        #     btn_text = f"{item_data['request'][:15]}... {timestamp}"[:64]
        #     builder.add(InlineKeyboardButton(
        #         text=btn_text,
        #         callback_data=f"hist_item:{item_id}"
        #     ))
        
        # builder.row(InlineKeyboardButton(
        #     text="🔙 Назад",
        #     callback_data="exit_history"
        # ))
        
        # await callback.message.answer(
        #     "📜 Ваша история запросов:",
        #     reply_markup=builder.as_markup()
        # )
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text=_("↩️ Назад к списку"),
            callback_data="back_to_history"
        ))
        builder.add(InlineKeyboardButton(
            text=_("🚪 Выйти из истории"),
            callback_data="exit_history"
        ))
        
        await callback.message.answer(
            _("Вы можете вернуться к списку запросов:"),
            reply_markup=builder.as_markup()
        )
        await state.set_state(History_again)
 
    except Exception as e:
        await callback.answer(_("❌ Ошибка загрузки"), show_alert=True)
        print(f"Error: {repr(e)}")

@view_history.callback_query(History_again, F.data == "back_to_history")
async def return_to_history_list(callback: CallbackQuery, state: FSMContext, supabase_client: sb.Client):
    """Возврат к полному списку истории, вызывая исходную функцию"""
    try:
        await callback.answer()
        await state.set_state(History_again)

        state_data = await state.get_data()
        user_id = callback.from_user.id
        
        # Создаем искусственный callback объект для повторного вызова handle_view_history
        class ArtificialCallback:
            def __init__(self):
                self.message = callback.message
                self.from_user = callback.from_user
                self.data = "view_history"  # Имитируем исходный callback
        
        # Вызываем исходную функцию показа истории
        await handle_view_history(ArtificialCallback(), state, supabase_client)
        
        # Удаляем временное сообщение с кнопкой "Назад"
        try:
            await callback.message.delete()
        except:
            pass
            
    except Exception as e:
        await callback.answer(_("❌ Не удалось загрузить историю"), show_alert=True)
        print(f"Return to history error: {repr(e)}")


@view_history.callback_query(F.data == "exit_history")
async def handle_exit_history(callback: CallbackQuery, state: FSMContext):
    """Выход из режима просмотра истории"""
    await callback.answer()
    await callback.message.edit_text(
        _("Вы вернулись в главное меню:"),
        reply_markup=None
    )
    await callback.message.answer(
        _("Выберите действие:"),
        reply_markup=menu_buttons()
    )
    await state.set_state(Form.is_choosing)