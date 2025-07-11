from logging import getLogger
from types import MappingProxyType
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from bot.log_message import (
    NO_SELECTOR_ERROR_LOG,
    PAGE_LOAD_ERROR_LOG,
    PRICE_NOT_FOUND_ERROR_LOG,
)
from config import config

log = getLogger(__name__)

PRICE_SELECTORS = MappingProxyType(
    {
        'toppreise.ch': ('div.Plugin_Price', 'CHF'),
    }
)


async def fetch_page_source(url: str) -> str:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/114.0.0.0 Safari/537.36'
            ),
            locale='de-DE',
            geolocation={'longitude': 8.5417, 'latitude': 47.3769},
            permissions=['geolocation'],
            viewport={'width': 1280, 'height': 720},
            accept_downloads=True,
        )
        page = await context.new_page()

        try:
            await page.goto(url, timeout=config.service.goto_timeout)
            await page.wait_for_timeout(config.service.wait_timeout)
            html = await page.content()
        except Exception as exc:
            log.error(PAGE_LOAD_ERROR_LOG, exc)
            html = ''
        await browser.close()
        return html


def extract_price(html: str, selector: str) -> str | None:
    soup = BeautifulSoup(html, 'lxml')
    element = soup.select_one(selector)
    if element:
        return element.get_text(strip=True)
    log.warning(PAGE_LOAD_ERROR_LOG, selector)
    return None


async def get_price(url: str) -> tuple[str, str] | None:
    domain = urlparse(url).hostname or ''
    selector_info = PRICE_SELECTORS.get(domain.removeprefix('www.'))
    if selector_info is None:
        log.error(NO_SELECTOR_ERROR_LOG, url)
        return None

    html = await fetch_page_source(url)
    price = extract_price(html, selector_info[0])

    if price is None:
        log.warning(PRICE_NOT_FOUND_ERROR_LOG, url)
        return None
    return price, selector_info[1]
