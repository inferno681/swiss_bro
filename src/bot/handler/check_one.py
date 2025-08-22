from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.constants import (
    CHECK_ONE,
    CHECK_ONE_CANCELED_MESSAGE,
    ERROR_MESSAGE,
    NO_GOODS_MESSAGE,
    NO_MESSAGE_ERROR,
    PRICE_INFO_MESSAGE,
    PRODUCT_NOT_FOUND_MESSAGE,
    RUB_LINE,
)
from bot.currency import get_currency_to_rub_rate
from bot.keyboard import get_keyboard_with_navigation, main_kb
from bot.model import Product
from config import config


class DeleteProduct(StatesGroup):
    waiting_for_name = State()


class ProductInfo(StatesGroup):
    waiting_for_name = State()


router = Router(name='check_one_router')


@router.message(F.text == CHECK_ONE)
async def cmd_check_one(message: Message, state: FSMContext):
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

    await state.set_state(ProductInfo.waiting_for_name)
    await state.update_data(pages=pages, current_page=current_page)
    lines = [
        f'{product['name']} — {product['price']} {product['currency']}'
        for product in products
    ]
    text = (
        f'Выберите товар для просмотра статистики (стр. {current_page + 1} / '
        f'{len(pages)}):\n\n'
        f'{'\n'.join(lines)}'
    )

    await message.answer(
        text,
        reply_markup=get_keyboard_with_navigation(
            products, current_page, len(pages)
        ),
    )


@router.callback_query(ProductInfo.waiting_for_name)
async def check_one_callback(callback: CallbackQuery, state: FSMContext):
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
            CHECK_ONE_CANCELED_MESSAGE, reply_markup=main_kb
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
        product = await Product.find_one(
            Product.user_id == telegram_id, Product.name == product_name
        )
        if not product:
            await callback.message.answer(
                PRODUCT_NOT_FOUND_MESSAGE.format(product_name=product_name),
                reply_markup=main_kb,
            )
            await state.clear()
            await callback.answer()
            return
        rate = await get_currency_to_rub_rate(product.currency)
        if rate:
            rub_line = RUB_LINE.format(
                rub_price=round(rate * float(product.price))
            )
        else:
            rub_line = ''
        await callback.message.edit_text(
            text=PRICE_INFO_MESSAGE.format(
                product=product.name,
                new_price=f'{product.price} {product.currency}',
                min_price=f'{product.min_price} {product.currency}',
                max_price=f'{product.max_price} {product.currency}',
                created_at=product.created_at.strftime('%d.%m.%Y %H:%M'),
                updated_at=product.updated_at.strftime('%d.%m.%Y %H:%M'),
                rub_line=rub_line,
                url=product.url,
            ),
            parse_mode='HTML',
            disable_web_page_preview=True,
        )
        await state.clear()
        await callback.answer()
