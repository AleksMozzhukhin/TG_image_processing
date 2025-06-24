import sys

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

import messages 

IS_CHOOSING_LANGUAGE=1
IS_CHOOSING_ACTION=2

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
        Реализация команды /start
        Выбор языка пользователем
    """
    keyboard = [
        [
            InlineKeyboardButton("English", callback_data="bot_language_en"),
            InlineKeyboardButton("Русский", callback_data="bot_language_ru"),
        ],
    ]
    reply_markup=InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        update.effective_chat.id, "Select language for the bot\nВыберите язык для бота", reply_markup=reply_markup

    )
    return IS_CHOOSING_LANGUAGE

async def while_choosing_language(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    """
        Приглашение пользователя выбрать язык интерфейса (английский или русский)
    """
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("bot_language"):
        print(f'An error occurred. Incorrect data was sent: {query.data}', file=sys.stderr)
        return 
    choosen_language = query.data[-2:]
    if choosen_language not in ["en", "ru"]:
        print(f'An error occurred. Incorrect data was sent: {query.data}', file=sys.stderr)
        return
    
    context.user_data["bot_language"] = choosen_language

    await context.bot.send_message(
        chat_id=update.effective_chat.id,  
        text=messages.USER_LANGUAGE[choosen_language] % choosen_language  
    )
    keyboard = [
            [InlineKeyboardButton(messages.REMOVE_NOISE[choosen_language], callback_data="remove_noise")],
            [InlineKeyboardButton(messages.GENERATE_IMAGE[choosen_language], callback_data="generate_image")],
            [InlineKeyboardButton(messages.VIEW_HISTORY[choosen_language], callback_data="view_history")],
            [InlineKeyboardButton("✨ "+ messages.MAGIC[choosen_language] + " ✨", callback_data="magic")],
    ]
    
    reply_markup=InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        update.effective_chat.id, messages.CHOOSE_SCENARIO[choosen_language], reply_markup=reply_markup
    )
    return IS_CHOOSING_ACTION