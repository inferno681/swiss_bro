from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.constants import (
    DELETE_GOOD,
    DELETION_CANCELED_MESSAGE,
    ERROR_MESSAGE,
    NO_GOODS_MESSAGE,
    NO_MESSAGE_ERROR,
    PRODUCT_DELETED_MESSAGE,
)
from bot.keyboard import get_keyboard_with_navigation, main_kb
from bot.model import Product
from config import config


class DeleteProduct(StatesGroup):
    waiting_for_name = State()


router = Router(name='delete_good_router')


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
    all_ids = await Product.get_all_ids(telegram_id)

    if not all_ids:
        await message.answer(NO_GOODS_MESSAGE, reply_markup=main_kb)
        return

    page_size = config.service.page_size
    pages = [
        all_ids[i : i + page_size] for i in range(0, len(all_ids), page_size)
    ]
    current_page = 0

    products = await Product.get_documents_by_ids(
        telegram_id, pages[current_page]
    )

    await state.set_state(DeleteProduct.waiting_for_name)
    await state.update_data(pages=pages, current_page=current_page)
    lines = [
        f'{product.name} — {product.price} {product.currency}'
        for product in products
    ]
    text = (
        f'Выберите товар для удаления (стр. {current_page + 1} / '
        f'{len(pages)}):\n\n'
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
        products = await Product.get_documents_by_ids(
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
        await Product.find_one(
            Product.user_id == telegram_id, Product.name == product_name
        ).delete_one()
        await callback.message.delete()
        await callback.message.answer(
            PRODUCT_DELETED_MESSAGE.format(product_name=product_name)
        )
        await state.clear()
        await callback.answer()
