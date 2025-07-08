from logging import getLogger

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

log = getLogger(__name__)


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
            await page.goto(url, timeout=30000)
            await page.wait_for_selector(
                'div.Plugin_Price', state='attached', timeout=10000
            )
            html = await page.content()
        except Exception as exc:
            log.error('Ошибка при загрузке: %s', exc)
            html = ''
        await browser.close()
        return html


def extract_price(html: str) -> str | None:
    soup = BeautifulSoup(html, 'lxml')
    div = soup.find('div', class_='Plugin_Price')
    if div:
        return div.text.strip()
    return None


async def get_price(url: str) -> str | None:
    html = await fetch_page_source(url)
    price = extract_price(html)
    return price
