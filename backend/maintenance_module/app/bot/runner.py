"""
Telegram Bot Runner for Maintenance Module.

Supports two modes:
1. Polling mode (local development) - uses long polling, no webhook needed
2. Webhook mode (production) - requires public HTTPS URL

Usage:
    python -m app.bot.runner          # Uses config.BOT_USE_POLLING
    python -m app.bot.runner --polling  # Force polling mode
    python -m app.bot.runner --webhook  # Force webhook mode
"""

import argparse
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.bot import router
from app.bot.middlewares import TechnicianAuthMiddleware, ApparatusBindMiddleware
from app.core.config import settings
from app.db.session import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def create_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    """Create bot and dispatcher with middlewares."""
    if not settings.BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set in configuration")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()

    # Register middlewares
    dp.update.middleware(TechnicianAuthMiddleware())
    dp.update.middleware(ApparatusBindMiddleware())

    # Include routers
    dp.include_router(router)

    return bot, dp


async def run_polling(bot: Bot, dp: Dispatcher) -> None:
    """Run bot in long polling mode (for local development)."""
    logger.info("Starting bot in POLLING mode...")

    # Initialize database
    await init_db()

    # Delete webhook if exists (to ensure polling works)
    await bot.delete_webhook(drop_pending_updates=True)

    # Start polling
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


async def run_webhook(bot: Bot, dp: Dispatcher) -> None:
    """Run bot in webhook mode (for production)."""
    if not settings.BOT_WEBHOOK_URL:
        raise ValueError("BOT_WEBHOOK_URL is not set in configuration")

    logger.info(f"Starting bot in WEBHOOK mode: {settings.BOT_WEBHOOK_URL}")

    # Initialize database
    await init_db()

    # Set webhook
    await bot.set_webhook(
        url=settings.BOT_WEBHOOK_URL,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
    )

    # Create aiohttp app for webhook
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    # Start server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

    logger.info("Webhook server started on http://0.0.0.0:8080/webhook")

    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        await bot.delete_webhook()
        await runner.cleanup()
        await bot.session.close()


async def main(polling: bool | None = None) -> None:
    """Main entry point."""
    # Determine mode
    use_polling = polling if polling is not None else settings.BOT_USE_POLLING

    bot, dp = await create_bot_and_dispatcher()

    try:
        if use_polling:
            await run_polling(bot, dp)
        else:
            await run_webhook(bot, dp)
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Telegram Bot Runner")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--polling", action="store_true", help="Force polling mode")
    group.add_argument("--webhook", action="store_true", help="Force webhook mode")
    args = parser.parse_args()

    polling_mode = None
    if args.polling:
        polling_mode = True
    elif args.webhook:
        polling_mode = False

    asyncio.run(main(polling=polling_mode))