from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.i18n import gettext as _

from bot.model import Product


def get_main_kb(locale: str | None = None):
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_('add_good', locale=locale)),
                KeyboardButton(text=_('check_goods', locale=locale)),
            ],
            [
                KeyboardButton(text=_('delete_good', locale=locale)),
                KeyboardButton(text=_('check_one', locale=locale)),
            ],
            [KeyboardButton(text=_('language_change', locale=locale))],
        ],
        resize_keyboard=True,
        input_field_placeholder=_('main_kb_place_holder', locale=locale),
    )


def get_cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=_('cancel'))]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_keyboard_with_navigation(
    products: list[Product], page: int, total_pages: int
) -> InlineKeyboardMarkup:
    keyboard = []

    for product in products:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=product.name,
                    callback_data=f'name:{product.name}',
                )
            ]
        )

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text=_('prev_button'), callback_data='prev')
        )
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(text=_('next_button'), callback_data='next')
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append(
        [InlineKeyboardButton(text=_('cancel'), callback_data='cancel')]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_lang_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='🇷🇺 Русский', callback_data='set_lang_ru'
                ),
                InlineKeyboardButton(
                    text='🇬🇧 English', callback_data='set_lang_en'
                ),
            ],
            [InlineKeyboardButton(text=_('cancel'), callback_data='cancel')],
        ]
    )
