from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable
from . import db_scripts


class DatabaseWares(BaseMiddleware):
    """Middleware for database."""

    def __init__(self, db: db_scripts.Database) -> None:
        """Initialization."""
        self.db = db

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]],
                              Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]) -> Any:
        """Save database to dict."""
        data['db'] = self.db
        return await handler(event, data)