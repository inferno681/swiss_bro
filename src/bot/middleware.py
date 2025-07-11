from logging import getLogger
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.log_message import UNAUTHORIZED_ACCESS_LOG


class AdminOnlyMiddleware(BaseMiddleware):
    """Check admins ids middleware."""

    def __init__(self, admin_ids: set[int]):
        """Class constructor."""
        self.admin_ids = admin_ids
        self.log = getLogger(__name__)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Async call method."""
        user = getattr(event, 'from_user', None)
        if user and user.id in self.admin_ids:
            return await handler(event, data)
        self.log.info(
            UNAUTHORIZED_ACCESS_LOG,
            user.id if user else 'Unknown',
        )
        return None
