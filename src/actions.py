"""Image processing scenario realization."""

import sys
import os
import uuid
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, constants
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
#from database import save_image_to_db, get_image_from_db  # Измненить на наши функции обработки 
#from image_processor import process_image  #Изменить на бота обработки изображений
import message

IMAGE_PROCESSING_BASE = 20
AWAITING_IMAGE_UPLOAD = IMAGE_PROCESSING_BASE + 0
PROCESSING_IMAGE = IMAGE_PROCESSING_BASE + 1
IMAGE_RESULT_READY = IMAGE_PROCESSING_BASE + 2

async def remove_noise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
        Начало обработки сценария удаления шума
    """
    query = update.callback_query
    await query.answer()
    bot_language = context.user_data["bot_language"]
    
    if query.data.startswith("remove_noise"):
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=messages.IMAGE_UPLOAD_PROMPT[bot_language]
        )
        return AWAITING_IMAGE_UPLOAD
        
    print(f'Unexpected query data {query.data} in image_processing_start', file=sys.stderr)
    return

async def handle_image_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
        Управление загрузкой картинки и ее предобработка
    """
    bot_language = context.user_data["bot_language"]
    photo_file = await update.message.photo[-1].get_file()
    image_bytes = await photo_file.download_as_bytearray()
    
    image_id = str(uuid.uuid4())
    context.user_data["image_id"] = image_id
    
    processing_msg = await update.message.reply_text(
        messages.IMAGE_PROCESSING[bot_language]
    )
    context.user_data["processing_msg_id"] = processing_msg.message_id
    await process_and_respond(update, context)
    
    return IMAGE_RESULT_READY

async def process_and_respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Конечная обработка картинки и ее отправка
    """
    bot_language = context.user_data["bot_language"]
    image_id = context.user_data["image_id"]
    msg_id = context.user_data["processing_msg_id"]
    
    try:
        image_data = get_image_from_db(image_id)

        processed_image = await process_image(image_data)
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg_id,
            text=messages.IMAGE_PROCESSING_COMPLETE[bot_language]
        )
        
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=processed_image,
            caption=messages.IMAGE_RESULT_CAPTION[bot_language]
        )
        
    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg_id,
            text=messages.IMAGE_PROCESSING_ERROR[bot_language] % str(e)
        )
    
    return await show_image_result_options(update, context)

async def show_image_result_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показ вариантов кнопок действий после завершения обработки картинки
    """
    bot_language = context.user_data["bot_language"]
    
    keyboard = [
        [
            InlineKeyboardButton(
                messages.PROCESS_ANOTHER_IMAGE[bot_language], 
                callback_data="process_image"
            ),
            InlineKeyboardButton(
                messages.BACK_TO_MENU[bot_language], 
                callback_data="back_to_menu"
            )
        ]
    ]
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=messages.CHOOSE_SCENARIO[bot_language],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return IMAGE_RESULT_READY

image_processing_states = {
    AWAITING_IMAGE_UPLOAD: [
        MessageHandler(filters.PHOTO, handle_image_upload),
    ],
    PROCESSING_IMAGE: [], 
    IMAGE_RESULT_READY: [
                CallbackQueryHandler(remove_noise, pattern="^remove_noise"),
                CallbackQueryHandler(generate_image, pattern="^generate_image"),
                CallbackQueryHandler(view_history, pattern="^view_history"),
                CallbackQueryHandler(magic, pattern="^magic"),
    ],
}