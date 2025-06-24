import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()

def main():
    if not (TELEGRAM_TOKEN := os.getenv("TELEGRAM_BOT_TOKEN")): 
        print("Telegram token not found! Install telegram token!")
    else: 
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.run_polling()

if __name__ == "__main__":
    main()