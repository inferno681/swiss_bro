from aiogram import F, Router
from aiogram.types import Message

from bot.constants import (
    CHECK_GOODS,
    ERROR_MESSAGE,
    NO_GOODS_MESSAGE,
    PRODUCT_INFO_LINE,
    RUBLE_PRICE_LINE_INFO,
)
from bot.currency import get_currency_to_rub_rate
from bot.keyboard import main_kb
from bot.model import Product

router = Router(name='check_goods_router')


@router.message(F.text == CHECK_GOODS)
async def cmd_check_all(message: Message) -> None:
    """Check all products command handler."""
    if not message.from_user:
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=main_kb,
        )
        return
    products = await Product.find_many(
        Product.user_id == message.from_user.id
    ).to_list()
    if not products:
        await message.answer(NO_GOODS_MESSAGE, reply_markup=main_kb)
        return

    lines = []
    for num, product in enumerate(products):
        rate = await get_currency_to_rub_rate(product['currency'])
        if rate:
            lines.append(
                PRODUCT_INFO_LINE.format(
                    pos=num + 1,
                    name=product['name'],
                    price=product['price'],
                    currency=product['currency'],
                )
                + ' '
                + RUBLE_PRICE_LINE_INFO.format(
                    rub_price=round(rate * float(product['price']))
                )
            )
        else:
            lines.append(
                PRODUCT_INFO_LINE.format(
                    pos=num,
                    name=product.name,
                    price=product.price,
                    currency=product.currency,
                )
            )
    text = '\n'.join(lines)
    await message.answer(text, reply_markup=main_kb)
