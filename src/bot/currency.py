import xml.etree.ElementTree as ET
from logging import getLogger
from time import time

from aiohttp import ClientSession

from bot.log_message import CURRENCY_NOT_FOUND_LOG, XML_ERROR_LOG
from config import config

log = getLogger(__name__)

_rate_cache: dict[str, tuple[float, float]] = {}


async def get_currency_to_rub_rate(currency: str) -> float | None:
    now = time()
    if currency in _rate_cache:
        rate, ts = _rate_cache[currency]
        if now - ts < config.service.rate_data_ttl:
            return rate
    async with ClientSession() as session:
        async with session.get(
            config.service.currency_rate_source
        ) as response:
            root = ET.fromstring(await response.text(encoding='windows-1251'))

    for valute in root.findall('Valute'):
        if valute.findtext('CharCode') == currency:
            value_text = valute.findtext('Value')
            nominal_text = valute.findtext('Nominal')
            if value_text is None or nominal_text is None:
                log.info(XML_ERROR_LOG, currency)
                return None
            try:
                rate = float(value_text.replace(',', '.')) / float(
                    nominal_text
                )
                _rate_cache[currency] = (rate, now)
                return rate
            except (ValueError, TypeError):
                log.info(XML_ERROR_LOG, currency)

    log.info(CURRENCY_NOT_FOUND_LOG, currency)
    return None
