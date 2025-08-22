import asyncio
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from logging import getLogger

from aiogram import Bot
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pymongo import MongoClient

from bot.constants import JOB_ID, RUB_LINE, UPDATE_PRICE_MESSAGE
from bot.currency import get_currency_to_rub_rate
from bot.log_message import (
    DECIMAL_ERROR_LOG,
    DOCUMENT_UPDATE_ERROR_LOG,
    GET_PRICE_ERROR_LOG,
    JOB_ADDED_LOG,
    JOB_EXISTS_LOG,
    MESSAGE_SEND_ERROR_LOG,
    PRICE_NOT_CHANGED_LOG,
    PRICE_NOT_FOUND_ERROR_LOG,
    PRICE_UPDATED_LOG,
    PRODUCT_LIST_NOT_RECEIVED_LOG,
    PRODUCT_UPDATE_RESULT_LOG,
    SCHEDULER_START_FAILED_LOG,
    SCHEDULER_START_LOG,
    START_PRICE_UPDATE_LOG,
)
from bot.model import Product
from bot.parser import get_price
from config import config

log = getLogger(__name__)


bot: Bot | None = None


def set_bot(bot_instance: Bot):
    """Set bot globally."""
    global bot
    bot = bot_instance


jobstores = {
    'default': MongoDBJobStore(
        client=MongoClient(config.mongo_url),
        database=config.mongodb.db,
        collection='jobs',
    )
}
scheduler = AsyncIOScheduler(jobstores=jobstores)


async def update_single_product(product: Product) -> bool:
    """Update single product method."""
    url = product.url
    try:
        price_info = await asyncio.wait_for(get_price(url), timeout=10)
        if price_info is None:
            log.warning(PRICE_NOT_FOUND_ERROR_LOG, url)
            return False
        new_price_row = price_info[0]
    except Exception as exc:
        log.error(GET_PRICE_ERROR_LOG, url, exc)
        return False

    if new_price_row is None:
        log.warning(PRICE_NOT_FOUND_ERROR_LOG, url)
        return False

    try:
        new_price = Decimal(new_price_row)
        old_price = Decimal(product.price or new_price)
        min_price = Decimal(product.min_price or new_price)
        max_price = Decimal(product.max_price or new_price)
    except (InvalidOperation, TypeError, ValueError) as exc:
        log.error(DECIMAL_ERROR_LOG, url, exc)
        return False

    update: dict = {}
    if new_price < min_price:
        update['min_price'] = str(new_price)
    if new_price > max_price:
        update['max_price'] = str(new_price)
    if new_price != old_price:
        update['price'] = str(new_price)

    if update:
        update['updated_at'] = datetime.now(timezone.utc)
        update['checked_at'] = datetime.now(timezone.utc)
        try:
            document = await product.set(update)
            log.info(PRICE_UPDATED_LOG, url, new_price)
            if bot and document and product.telegram_id:
                rate = await get_currency_to_rub_rate(product.currency)
                if rate:
                    rub_line = RUB_LINE.format(
                        rub_price=round(rate * float(product.price))
                    )
                else:
                    rub_line = ''
                try:
                    await bot.send_message(
                        chat_id=product.telegram_id,
                        text=UPDATE_PRICE_MESSAGE.format(
                            product=document.name,
                            rub_line=rub_line,
                            new_price=(
                                f'{document.price} ' f'{document.currency}'
                            ),
                            min_price=(
                                f'{document.min_price} ' f'{document.currency}'
                            ),
                            max_price=(
                                f'{document.max_price} ' f'{document.currency}'
                            ),
                            created_at=document.created_at.strftime(
                                '%d.%m.%Y %H:%M'
                            ),
                            updated_at=document.updated_at.strftime(
                                '%d.%m.%Y %H:%M'
                            ),
                            url=document.url,
                        ),
                        parse_mode='HTML',
                        disable_web_page_preview=True,
                    )
                except Exception as exc:
                    log.error(MESSAGE_SEND_ERROR_LOG, exc)
            return True
        except Exception as exc:
            log.error(DOCUMENT_UPDATE_ERROR_LOG, url, exc)
            return False
    else:
        update['checked_at'] = datetime.now(timezone.utc)
        await product.set(update)
        log.info(PRICE_NOT_CHANGED_LOG, url)
        return False


async def update_prices_job():
    """Price update job."""
    log.info(START_PRICE_UPDATE_LOG)

    products = await Product.find_all().to_list()
    if not products:
        log.error(PRODUCT_LIST_NOT_RECEIVED_LOG)
        return

    tasks = [update_single_product(product) for product in products]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = sum(1 for result in results if result is True)
    log.info(PRODUCT_UPDATE_RESULT_LOG, success_count, len(products))


async def start_scheduler():
    """Start the scheduler and add the update job if it doesn't exist."""
    try:
        if not scheduler.running:
            scheduler.start()
            log.info(SCHEDULER_START_LOG)
        if scheduler.get_job(JOB_ID):
            log.info(JOB_EXISTS_LOG, JOB_ID)
        else:
            scheduler.add_job(
                update_prices_job,
                'interval',
                hours=12,
                id=JOB_ID,
                replace_existing=False,
            )
            log.info(JOB_ADDED_LOG, JOB_ID)
    except Exception as exc:
        log.error(SCHEDULER_START_FAILED_LOG, exc)
