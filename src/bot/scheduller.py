import asyncio
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from logging import getLogger

from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pymongo import MongoClient
from aiogram import Bot
from bot.db import mongo
from bot.parser import get_price
from config import config

log = getLogger(__name__)


bot: Bot | None = None


def set_bot(bot_instance: Bot):
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

JOB_ID = 'update_prices_job'


async def update_single_product(product: dict) -> bool:
    url = product['url']
    try:
        new_price_row = await asyncio.wait_for(get_price(url), timeout=10)
    except Exception as exc:
        log.error(f'Ошибка при получении цены для {url}: {exc}')
        return False

    if new_price_row is None:
        log.warning(f'Цена не найдена для {url}')
        return False

    try:
        new_price = Decimal(new_price_row)
        old_price = Decimal(product.get('price', new_price))
        min_price = Decimal(product.get('min_price', new_price))
        max_price = Decimal(product.get('max_price', new_price))
    except (InvalidOperation, TypeError, ValueError) as exc:
        log.error(f'Ошибка приведения цены к Decimal для {url}: {exc}')
        return False

    update = {}
    if new_price < min_price:
        update['min_price'] = str(new_price)
    if new_price > max_price:
        update['max_price'] = str(new_price)
    if new_price != old_price:
        update['price'] = str(new_price)

    if update:
        update['updated_at'] = datetime.now(timezone.utc)
        try:
            await mongo.update_document(url, update)
            log.info(f'Цена обновлена для {url}: {new_price}')
            if bot:
                try:
                    await bot.send_message(
                        chat_id=product['telegram_id'],
                        text=f'💰 Цена на <b>{product["name"]}</b> обновилась: {new_price}',
                        parse_mode='HTML',
                    )
                except Exception as exc:
                    log.error(f'Ошибка при отправке сообщения: {exc}')
            return True
        except Exception as exc:
            log.error(f'Ошибка при обновлении документа {url}: {exc}')
            return False
    else:
        log.info(f'Цена не изменилась для {url}')
        return False


async def update_prices_job():
    log.info("🚀 Starting price update job...")

    products = await mongo.get_all_documents()
    if not products:
        log.error('Could not get product list from the database.')
        return

    tasks = [update_single_product(product) for product in products]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = sum(1 for result in results if result is True)
    log.info(
        '✅ Update job finished. Successfully updated '
        f'{success_count}/{len(products)} products.'
    )


async def start_scheduler():
    """Start the scheduler and add the update job if it doesn't exist."""
    try:
        if not scheduler.running:
            scheduler.start()
            log.info("Scheduler started successfully.")
        if scheduler.get_job(JOB_ID):
            log.info(f'Задача {JOB_ID} уже существует, не добавляю повторно.')
        else:
            scheduler.add_job(
                update_prices_job,
                'interval',
                hours=12,
                id=JOB_ID,
                replace_existing=False,
            )
            log.info(f'Задача {JOB_ID} добавлена в планировщик.')
    except Exception as exc:
        log.error(f"Failed to start scheduler: {exc}")
