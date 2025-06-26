import os
import asyncio
import logging
import sys
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties

from supabase import create_client, Client

from routers.all_routers import all_routers
from .db.db_wares import SupabaseMiddleware

load_dotenv()

async def main():
    """Основная функция для запуска бота."""
    
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not all([telegram_token, supabase_url, supabase_key]):
        logging.critical("Не удалось загрузить все переменные окружения! (TOKEN, SUPABASE_URL, SUPABASE_KEY)")
        sys.exit(1)

    supabase_client: Client = create_client(supabase_url, supabase_key)
    dispatcher = Dispatcher()
    dispatcher.update.outer_middleware.register(SupabaseMiddleware(supabase_client))
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