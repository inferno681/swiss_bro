from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.markdown import hbold

from bot.constants import ALLOWED_SITES
from bot.keyboard import get_main_kb
from bot.model import User
from config import config

router = Router(name='cmd_router')


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Start command handler."""
    tg_user = message.from_user
    if not tg_user:
        await message.answer(_('user_not_recognized'))
        return
    user = await User.find_one(User.user_id == tg_user.id)
    if user is None:
        user = User(
            user_id=tg_user.id,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            username=tg_user.username,
            full_name=tg_user.full_name,
            language_code=tg_user.language_code,
            is_premium=getattr(tg_user, 'is_premium', None),
        )
        await user.insert()
    else:
        user.first_name = tg_user.first_name
        user.last_name = tg_user.last_name
        user.username = tg_user.username
        user.full_name = tg_user.full_name
        user.language_code = tg_user.language_code
        user.is_premium = getattr(tg_user, 'is_premium', None)
        await user.save()
    if tg_user.language_code in config.service.locales:
        locale = tg_user.language_code
    else:
        locale = 'en'
    await message.answer(
        _('start_message').format(
            name=hbold(tg_user.full_name), sites=', \n'.join(ALLOWED_SITES)
        ),
        reply_markup=get_main_kb(locale=locale),
    )


@router.message(F.text == __('cancel'))
async def cancel_handler(message: Message, state: FSMContext):
    """Cancel handler."""
    await state.clear()
    await message.answer(_('cancel'), reply_markup=get_main_kb())
