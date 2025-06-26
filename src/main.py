import os
import asyncio
import logging
import sys
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties

from routers.all_routers import all_routers


load_dotenv()

async def main():
    """Основная функция для запуска бота."""
    
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not telegram_token:
        logging.critical("Не удалось загрузить все переменные окружения! (TOKEN, SUPABASE_URL, SUPABASE_KEY)")
        sys.exit(1)

    dispatcher = Dispatcher()
    dispatcher.include_router(all_routers)
    bot = Bot(
        token=telegram_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN) 
    )

    logging.info("Бот запускается...")
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
    )
    asyncio.run(main())