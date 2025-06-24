import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler
from start import start, while_choosing_language, IS_CHOOSING_LANGUAGE, IS_CHOOSING_ACTION
import actions 

load_dotenv()

def main():
    if not (TELEGRAM_TOKEN := os.getenv("TELEGRAM_BOT_TOKEN")): 
        print("Telegram token not found! Install telegram token!")
    else: 
        app_builder = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        states = {
            IS_CHOOSING_LANGUAGE: [
                CallbackQueryHandler(while_choosing_language, pattern="^bot_language"),
            ],
            IS_CHOOSING_ACTION: [
                CallbackQueryHandler(remove_noise, pattern="^remove_noise"),
                CallbackQueryHandler(generate_image, pattern="^generate_image"),
                CallbackQueryHandler(view_history, pattern="^view_history"),
                CallbackQueryHandler(magic, pattern="^magic"),
            ],
        }

        states |= image_processing_states

        handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states=states, 
            fallbacks=[CommandHandler("start", start)], 
        )
        application.add_handler(handler)
        app_builder.run_polling()

if __name__ == "__main__":
    main()