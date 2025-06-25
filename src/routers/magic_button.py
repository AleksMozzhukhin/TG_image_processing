"""Magic button scenario with FusionBrain AI integration."""

import sys
import os
import logging
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv
import messages
import uuid
import time

load_dotenv()

MAGIC_BASE = 30
AWAITING_MAGIC_ACTION = MAGIC_BASE + 0
GENERATING_TEXT = MAGIC_BASE + 1
GENERATING_IMAGE = MAGIC_BASE + 2

IS_CHOOSING_ACTION=2

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = os.getenv("DEEPSEEK_API_KEY")
MAX_TOKENS = 30 
MODEL = "deepseek-chat"

FUSIONBRAIN_API_KEY = os.getenv("FUSIONBRAIN_API_KEY")
FUSIONBRAIN_SECRET_KEY = os.getenv("FUSIONBRAIN_SECRET_KEY")

async def magic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало сценария Magic - генерация описания картины"""
    query = update.callback_query
    await query.answer()
    bot_language = context.user_data["bot_language"]
    
    if query.data == "magic":
        # Сообщение о начале генерации
        status_msg = await query.edit_message_text(
            text="🧠 Генерирую описание картины...",
            reply_markup=None
        )
        context.user_data["status_msg_id"] = status_msg.message_id
        
        try:
            description = await generate_art_description(update, context)
            context.user_data["art_description"] = description
            await query.edit_message_text(
                text="🎨 Создаю картину по описанию...",
                reply_markup=None
            )
            
            image_url = await generate_fusionbrain_image(description)
            
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=context.user_data["status_msg_id"]
            )
            
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image_url,
                caption=f"🖼️ {description}",
                #reply_markup=get_magic_keyboard(bot_language)
            )
            
            return IS_CHOOSING_ACTION
            
        except Exception as e:
            logging.error(f"Magic error: {e}")
            await query.edit_message_text(
                text="⚠️ Ошибка генерации. Попробуйте позже.",
                reply_markup=get_magic_keyboard(bot_language)
            )
            return 
    
    print(f'Unexpected query data {query.data} in magic_start', file=sys.stderr)
    return

async def generate_art_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерация описания через DeepSeek"""
    query = update.callback_query
    await query.answer()
    
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MODEL,
            "messages": [{
                "role": "user",
                "content": "Сгенерируй краткое описание любой картины, 10-15 слов. Опиши сюжет, стиль и настроение."
            }],
            "max_tokens": MAX_TOKENS,
            "temperature": 0.7
        }
        
        status_msg = await query.edit_message_text(
            text="🖌️ Художник рисует словами...",
            reply_markup=None
        )
        
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        generated_text = response.json()["choices"][0]["message"]["content"]
    
        final_text = ' '.join(generated_text.split()[:15])
        
        return final_text
    
    except Exception as e:
        logging.error(f"DeepSeek error: {e}")
        await query.edit_message_text(
            text="⚠️ Ошибка генерации. Попробуйте позже.",
            #reply_markup=get_actions_keyboard()
        )
    
    return 

async def generate_fusionbrain_image(description: str) -> str:
    """Генерация изображения через FusionBrain API"""
    auth_url = "https://api.fusionbrain.ai/web/api/v1/text2image/oauth"
    headers = {
        "X-Key": f"Key {FUSIONBRAIN_API_KEY}",
        "X-Secret": f"Secret {FUSIONBRAIN_SECRET_KEY}",
    }

    generate_url = "https://api.fusionbrain.ai/web/api/v1/text2image/run"
    payload = {
        "type": "GENERATE",
        "style": "DEFAULT",
        "width": 1024,
        "height": 1024,
        "generateParams": {
            "query": f"{description}, high quality artwork"
        }
    }
    
    response = requests.post(generate_url, headers=headers, json=payload)
    response.raise_for_status()
    task_id = response.json()["uuid"]
    
    check_url = f"https://api.fusionbrain.ai/web/api/v1/text2image/status/{task_id}"
    for _ in range(10): 
        time.sleep(5)
        status_response = requests.get(check_url, headers=headers)
        if status_response.json()["status"] == "DONE":
            return status_response.json()["images"][0]
    
    raise TimeoutError("Image generation timeout")

def get_magic_keyboard(language: str):
    """Клавиатура после генерации"""
    bot_language = "ru"
    return InlineKeyboardMarkup([
            [InlineKeyboardButton(messages.REMOVE_NOISE[bot_language], callback_data="remove_noise")],
            [InlineKeyboardButton(messages.GENERATE_IMAGE[bot_language], callback_data="generate_image")],
            [InlineKeyboardButton(messages.VIEW_HISTORY[bot_language], callback_data="view_history")],
            [InlineKeyboardButton("✨ "+ messages.MAGIC[bot_language] + " ✨", callback_data="magic")],
    ])

# States для ConversationHandler
magic_states = {
    AWAITING_MAGIC_ACTION: [
        CallbackQueryHandler(magic, pattern="^magic_button$"),
    ],
    GENERATING_TEXT: [],
    GENERATING_IMAGE: [],
}