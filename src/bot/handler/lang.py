from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from bot.keyboard import get_lang_kb, get_main_kb
from bot.model import User
from config import config

router = Router(name='change_language_router')


class ChooseLang(StatesGroup):
    waiting_for_lang = State()


@router.message(F.text == __('language_change'))
async def change_language(message: Message, state: FSMContext):
    """Change language command."""
    await state.set_state(ChooseLang.waiting_for_lang)
    await message.answer(_('choose_lang_message'), reply_markup=get_lang_kb())


@router.callback_query(ChooseLang.waiting_for_lang)
async def choose_language(callback: CallbackQuery, state: FSMContext):
    """Choose language handler."""
    if not isinstance(callback.message, Message):
        await callback.answer(_('no_message_error'))
        await state.clear()
        return
    if not callback.data:
        await callback.answer(_('no_message_error'))
        await state.clear()
        return
    if callback.data == 'cancel':
        await callback.message.delete()
        await callback.message.answer(
            _('lang_change_cancel_message'), reply_markup=get_main_kb()
        )
        await state.clear()
        await callback.answer()
        return
    lang_code = callback.data.split('_')[-1]
    if lang_code not in config.service.locales:
        await state.clear()
        await callback.message.edit_text(text=_('incorrect_lang_code'))
        await callback.answer()
    await User.find_one(User.user_id == callback.from_user.id).set(
        {'language_code': lang_code}
    )
    if lang_code == 'ru':
        text = '✅ Язык успешно изменён на русский.'
    else:
        text = '✅ Language successfully changed to English.'
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        text=text, reply_markup=get_main_kb(locale=lang_code)
    )
