from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from bot.constants import (
    ADD_GOOD,
    CANCEL,
    CHECK_GOODS,
    CHECK_ONE,
    DELETE_GOOD,
    MAIN_KB_PLACEHOLDER,
    NEXT_PAGE_BUTTON,
    PREV_PAGE_BUTTON,
)
from bot.model import Product

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=ADD_GOOD), KeyboardButton(text=CHECK_GOODS)],
        [KeyboardButton(text=DELETE_GOOD), KeyboardButton(text=CHECK_ONE)],
    ],
    resize_keyboard=True,
    input_field_placeholder=MAIN_KB_PLACEHOLDER,
)


cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=CANCEL)]],
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
            InlineKeyboardButton(text=PREV_PAGE_BUTTON, callback_data='prev')
        )
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(text=NEXT_PAGE_BUTTON, callback_data='next')
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append(
        [InlineKeyboardButton(text=CANCEL, callback_data='cancel')]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
