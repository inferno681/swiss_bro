from aiogram import F, Router
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from bot.constants import PRODUCT_INFO_LINE
from bot.currency import get_currency_to_rub_rate
from bot.keyboard import get_main_kb
from bot.model import Product

router = Router(name='check_goods_router')


@router.message(F.text == __('check_goods'))
async def cmd_check_all(message: Message) -> None:
    """Check all products command handler."""
    if not message.from_user:
        await message.answer(
            _('error_message'),
            reply_markup=get_main_kb(),
        )
        return
    products = await Product.find_many(
        Product.user_id == message.from_user.id
    ).to_list()
    if not products:
        await message.answer(_('no_goods_message'), reply_markup=get_main_kb())
        return

    lines = []
    for num, product in enumerate(products):
        rate = await get_currency_to_rub_rate(product.currency)
        if rate:
            lines.append(
                PRODUCT_INFO_LINE.format(
                    pos=num + 1,
                    name=product.name,
                    price=product.price,
                    currency=product.currency,
                )
                + ' '
                + _('ruble_price_info').format(
                    rub_price=round(rate * float(product.price))
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
    await message.answer(text, reply_markup=get_main_kb())
