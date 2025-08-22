from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from bot.constants import (
    ALLOWED_SITES,
    CANCEL,
    START_MESSAGE,
    USER_NOT_RECOGNIZED,
)
from bot.keyboard import main_kb
from bot.model import User

router = Router(name='cmd_router')


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Start command handler."""
    tg_user = message.from_user
    if not tg_user:
        await message.answer(USER_NOT_RECOGNIZED)
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
        user.is_premium = getattr(tg_user, 'is_premium', None)
        await user.save()
    await message.answer(
        START_MESSAGE.format(
            name=hbold(tg_user.full_name), sites=', \n'.join(ALLOWED_SITES)
        ),
        reply_markup=main_kb,
    )


@router.message(F.text == CANCEL)
async def cancel_handler(message: Message, state: FSMContext):
    """Cancel handler."""
    await state.clear()
    await message.answer('cancel', reply_markup=main_kb)
