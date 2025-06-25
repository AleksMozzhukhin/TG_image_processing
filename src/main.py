import os
import asyncio
import logging
import sys
from dotenv import load_dotenv

from aiogram import Bot
from aiogram import Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties

load_dotenv()

async def main():
    """Создание базой конфигурации бота"""
    dispatcher = Dispatcher()
    #добавить код, когда будет готова бд
    db_instance = db_scripts.DataBase()
    if not (TELEGRAM_TOKEN := os.getenv("TELEGRAM_BOT_TOKEN")): 
        print("Telegram token not found! Install telegram token!")
        sys.exit(1)
    bot = Bot(
        token=TELEGRAM_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s - [%(levelname)s] -  %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"  # noqa: E501
    )
    asyncio.run(main())