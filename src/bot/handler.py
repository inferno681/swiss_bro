from datetime import datetime, timezone
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold

from bot.constants import (
    ADD_GOOD,
    ALLOWED_SITES,
    ALREADY_EXISTS_MESSAGE,
    CANCEL,
    CHECK_GOODS,
    DELETE_GOOD,
    DELETION_CANCELED_MESSAGE,
    ERROR_MESSAGE,
    GOOD_ADDED_MESSAGE,
    INCORRECT_URL_MESSAGE,
    LINK_RECEIVED_MESSAGE,
    NO_GOODS_MESSAGE,
    NO_MESSAGE_ERROR,
    NO_PRICE_MESSAGE,
    NOT_URL_MESSAGE,
    PRODUCT_DELETED_MESSAGE,
    SEND_LINK_MESSAGE,
    URL_REGEX,
)
from bot.db import mongo
from bot.keyboard import cancel_kb, get_keyboard_with_navigation, main_kb
from bot.parser import get_price
from bot.scheme import BaseScheme
from config import config


class AddProduct(StatesGroup):
    waiting_for_url = State()
    waiting_for_name = State()


class DeleteProduct(StatesGroup):
    waiting_for_name = State()


router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Start command handler."""
    user_name = (
        message.from_user.full_name if message.from_user else 'Anonymous'
    )
    await message.answer(f'Привет, {hbold(user_name)}!', reply_markup=main_kb)


@router.message(F.text == ADD_GOOD)
async def cmd_add_start(message: Message, state: FSMContext) -> None:
    """Command to start adding a product."""
    await message.answer(SEND_LINK_MESSAGE, reply_markup=cancel_kb)
    await state.set_state(AddProduct.waiting_for_url)


@router.message(AddProduct.waiting_for_url, F.text.regexp(URL_REGEX))
async def process_url(message: Message, state: FSMContext) -> None:
    """Process the URL sent by the user."""
    if not message.text:
        await message.answer(INCORRECT_URL_MESSAGE)
        return

    url_match = URL_REGEX.search(message.text)
    if not url_match:
        await message.answer(INCORRECT_URL_MESSAGE)
        return

    url = url_match.group(0)
    if not url.startswith(ALLOWED_SITES):
        await message.answer(INCORRECT_URL_MESSAGE)
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

    price = await get_price(url)
    if not message.from_user:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=main_kb,
        )
        await state.clear()
        return

    if price:
        good_info = BaseScheme(
            telegram_id=message.from_user.id,
            url=url,
            name=name,
            price=price,
            min_price=price,
            max_price=price,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        if await mongo.insert_document(good_info.model_dump()):
            await message.answer(
                GOOD_ADDED_MESSAGE.format(name=name, price=price),
                reply_markup=main_kb,
            )
        else:
            await message.answer(ALREADY_EXISTS_MESSAGE, reply_markup=main_kb)
    else:
        await message.answer(NO_PRICE_MESSAGE, reply_markup=main_kb)

    await state.clear()


@router.message(AddProduct.waiting_for_url)
async def invalid_url(message: Message):
    await message.answer(NOT_URL_MESSAGE)


@router.message(F.text == CANCEL)
async def cancel_handler(message: Message, state: FSMContext):
    """Cancel handler."""
    await state.clear()
    await message.answer('Отмена', reply_markup=main_kb)


@router.message(F.text == CHECK_GOODS)
async def cmd_check_all(message: Message) -> None:
    """Check all products command handler."""
    if not message.from_user:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=main_kb,
        )
        return
    products = await mongo.get_all_documents(message.from_user.id)
    if not products:
        await message.answer(NO_GOODS_MESSAGE, reply_markup=main_kb)
        return

    lines = [
        f'{num + 1}. {product['name']} — {product['price']}'
        for num, product in enumerate(products)
    ]
    text = '\n'.join(lines)
    await message.answer(text, reply_markup=main_kb)


@router.message(F.text == DELETE_GOOD)
async def cmd_delete_good(message: Message, state: FSMContext):
    if not message.from_user:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=main_kb,
        )
        await state.clear()
        return
    telegram_id = message.from_user.id
    all_ids = await mongo.get_all_ids(telegram_id)

    if not all_ids:
        await message.answer(NO_GOODS_MESSAGE, reply_markup=main_kb)
        return

    page_size = config.service.page_size
    pages = [
        all_ids[i : i + page_size] for i in range(0, len(all_ids), page_size)
    ]
    current_page = 0

    products = await mongo.get_documents_by_ids(
        telegram_id, pages[current_page]
    )

    await state.set_state(DeleteProduct.waiting_for_name)
    await state.update_data(pages=pages, current_page=current_page)
    lines = [f'{product['name']} — {product['price']}' for product in products]
    text = (
        f'Выберите товар для удаления (стр. {current_page + 1} / '
        f'{len(pages)}):/n/n'
        f'{'\n'.join(lines)}'
    )

    await message.answer(
        text,
        reply_markup=get_keyboard_with_navigation(
            products, current_page, len(pages)
        ),
    )


@router.callback_query(DeleteProduct.waiting_for_name)
async def process_callback(callback: CallbackQuery, state: FSMContext):
    pagination_data = await state.get_data()
    pages = pagination_data.get('pages', [])
    current_page = pagination_data.get('current_page', 0)
    telegram_id = callback.from_user.id

    if not isinstance(callback.message, Message):
        await callback.answer(NO_MESSAGE_ERROR)
        await state.clear()
        return

    if callback.data == 'cancel':
        await callback.message.delete()
        await callback.message.answer(
            DELETION_CANCELED_MESSAGE, reply_markup=main_kb
        )
        await state.clear()
        await callback.answer()
        return
    if not callback.data:
        await callback.answer(NO_MESSAGE_ERROR)
        await state.clear()
        return

    if callback.data.startswith('next'):
        current_page += 1
    elif callback.data.startswith('prev'):
        current_page -= 1

    if callback.data.startswith('next') or callback.data.startswith('prev'):
        await state.update_data(current_page=current_page)
        products = await mongo.get_documents_by_ids(
            telegram_id, pages[current_page]
        )

        await callback.message.edit_reply_markup(
            reply_markup=get_keyboard_with_navigation(
                products, current_page, len(pages)
            )
        )
        await callback.answer()
        return

    if callback.data.startswith('name:'):
        product_name = callback.data.split(':', 1)[1]
        await mongo.delete_document(telegram_id, product_name)
        await callback.message.delete()
        await callback.message.answer(
            PRODUCT_DELETED_MESSAGE.format(product_name=product_name)
        )
        await state.clear()
        await callback.answer()
