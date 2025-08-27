import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.i18n import I18n
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    setup_application,
)
from aiohttp import web

from bot.db import init_db
from bot.handler import main_router
from bot.log_message import BOT_STOPPED_LOG
from bot.middleware import AdminOnlyMiddleware, DBI18nMiddleware
from bot.scheduller import set_bot, start_scheduler
from config import config

LOCALE_DIR = Path(__file__).resolve().parent.parent.parent / 'locales'
i18n = I18n(path=LOCALE_DIR, default_locale='en', domain='messages')


def setup_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    """Bot and Dispatcher setup."""
    dp = Dispatcher()
    DBI18nMiddleware(i18n).setup(dp)
    dp.message.middleware(AdminOnlyMiddleware(set(config.service.admins)))
    dp.include_router(main_router)

    bot = Bot(
        token=config.secrets.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    set_bot(bot)
    return bot, dp


async def on_startup(bot: Bot) -> None:
    """Actions to perform on bot startup."""
    await bot.set_webhook(
        config.webhook_url,
        secret_token=config.secrets.webhook_secret.get_secret_value(),
    )


async def create_app() -> web.Application:
    """Create and configure the aiohttp web application."""
    bot, dp = setup_bot_and_dispatcher()

    dp.startup.register(on_startup)

    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=config.secrets.webhook_secret.get_secret_value(),
    )
    webhook_requests_handler.register(app, path=config.service.webhook_path)

    setup_application(app, dp, bot=bot)

    return app


async def start_polling():
    """Start the bot with polling."""
    bot, dp = setup_bot_and_dispatcher()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def main():
    """Main function to start the bot."""
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await init_db()
    await start_scheduler()
    if config.service.webhook:
        app = await create_app()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(
            runner,
            host=config.service.web_server_host,
            port=config.service.web_server_port,
        )
        await site.start()
        await asyncio.Event().wait()
    else:
        await start_polling()


if __name__ == '__main__':
    """Main entry point for the bot."""
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info(BOT_STOPPED_LOG)
