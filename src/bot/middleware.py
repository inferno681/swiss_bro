from logging import getLogger
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from aiogram.types.user import User as TelegramUser
from aiogram.utils.i18n.middleware import I18nMiddleware

from bot.log_message import UNAUTHORIZED_ACCESS_LOG
from bot.model import User, UserLocaleProjection
from config import config


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
        user = data.get('event_from_user') or getattr(event, 'from_user', None)
        if user:
            if user.id in self.admin_ids:
                return await handler(event, data)
            if await self._is_registered(user):
                return await handler(event, data)
        if isinstance(event, Message):
            text = event.text or ''
            if text.lstrip().startswith('/start'):
                return await handler(event, data)
        self.log.info(
            UNAUTHORIZED_ACCESS_LOG,
            user.id if user else 'Unknown',
        )
        return None

    async def _is_registered(self, user: TelegramUser) -> bool:
        try:
            user_db = await User.find_one(User.user_id == user.id)
            return bool(user_db)
        except Exception:
            return False


class DBI18nMiddleware(I18nMiddleware):
    async def get_locale(
        self, event: TelegramObject, data: Dict[str, Any]
    ) -> str:
        user = data.get('event_from_user') or getattr(event, 'from_user', None)
        if user:
            locale = await User.find_one(User.user_id == user.id).project(
                UserLocaleProjection
            )
            if locale and locale.language_code in config.service.locales:
                return locale.language_code
        return self.i18n.default_locale
