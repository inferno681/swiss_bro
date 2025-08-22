from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from bot.constants import (
    ADD_GOOD,
    ALLOWED_SITES,
    ALREADY_EXISTS_MESSAGE,
    ERROR_MESSAGE,
    GOOD_ADDED_MESSAGE,
    INCORRECT_URL_MESSAGE,
    LINK_RECEIVED_MESSAGE,
    NO_PRICE_MESSAGE,
    NOT_URL_MESSAGE,
    PRICE_IN_RUBLES,
    SEND_LINK_MESSAGE,
    URL_REGEX,
)
from bot.currency import get_currency_to_rub_rate
from bot.keyboard import cancel_kb, main_kb
from bot.model import Product
from bot.parser import get_price

router = Router(name='add_good_router')


class AddProduct(StatesGroup):
    waiting_for_url = State()
    waiting_for_name = State()


@router.message(F.text == ADD_GOOD)
async def cmd_add_start(message: Message, state: FSMContext) -> None:
    """Command to start adding a product."""
    await message.answer(SEND_LINK_MESSAGE, reply_markup=cancel_kb)
    await state.set_state(AddProduct.waiting_for_url)


@router.message(AddProduct.waiting_for_url, F.text.regexp(URL_REGEX))
async def process_url(message: Message, state: FSMContext) -> None:
    """Process the URL sent by the user."""
    if not message.text:
        await message.answer(
            INCORRECT_URL_MESSAGE.format(sites=", ".join(ALLOWED_SITES))
        )
        return

    url_match = URL_REGEX.search(message.text)
    if not url_match:
        await message.answer(
            INCORRECT_URL_MESSAGE.format(sites=", ".join(ALLOWED_SITES))
        )
        return

    url = url_match.group(0)
    if not url.startswith(ALLOWED_SITES):
        await message.answer(
            INCORRECT_URL_MESSAGE.format(sites=", ".join(ALLOWED_SITES))
        )
        return
    if not message.from_user:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=main_kb,
        )
        await state.clear()
        return
    if await Product.find_one(
        Product.user_id == message.from_user.id, Product.url == url
    ):
        await message.answer(ALREADY_EXISTS_MESSAGE, reply_markup=main_kb)
        await state.clear()
        return
    await state.update_data(url=url)

    await message.answer(LINK_RECEIVED_MESSAGE, reply_markup=cancel_kb)
    await state.set_state(AddProduct.waiting_for_name)


@router.message(AddProduct.waiting_for_name)
async def process_name(message: Message, state: FSMContext) -> None:
    """Process the name of the product."""
    state_data = await state.get_data()
    url = state_data.get("url")
    name = message.text

    if not isinstance(url, str) or not isinstance(name, str):
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=main_kb,
        )
        await state.clear()
        return

    if not message.from_user:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=main_kb,
        )
        await state.clear()
        return

    price_info = await get_price(url)
    if price_info:
        price, currency = price_info
        await Product(
            user_id=message.from_user.id,
            url=url,
            name=name,
            price=price,
            min_price=price,
            max_price=price,
            currency=currency,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ).insert()
        rate = await get_currency_to_rub_rate(currency)
        if rate:
            text = (
                GOOD_ADDED_MESSAGE.format(
                    name=name, price=f'{price} {currency}'
                )
                + ' '
                + PRICE_IN_RUBLES.format(price=round(rate * float(price)))
            )
        else:
            text = GOOD_ADDED_MESSAGE.format(
                name=name, price=f'{price} {currency}'
            )
        await message.answer(
            text,
            reply_markup=main_kb,
        )
    else:
        await message.answer(NO_PRICE_MESSAGE, reply_markup=main_kb)

    await state.clear()


@router.message(AddProduct.waiting_for_url)
async def invalid_url(message: Message):
    await message.answer(NOT_URL_MESSAGE)
