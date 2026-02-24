"""MiniMelts Order Bot entry point."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.config import config
from bot.db import get_active_products, init_db
from bot.handlers.admin import router as admin_router
from bot.handlers.client import router as client_router
from bot.scheduler import setup_scheduler
from bot.seed import seed as seed_catalog

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not config.bot_token:
        logger.error("BOT_TOKEN is not set! Copy .env.example to .env and fill in your token.")
        return
    logger.info("Bot version: %s", config.bot_version)

    await init_db()
    logger.info("Database initialized")

    existing = await get_active_products()
    if not existing:
        await seed_catalog()
        logger.info("Catalog seeded with default products")

    bot = Bot(token=config.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Start"),
            BotCommand(command="menu", description="Main menu"),
            BotCommand(command="lang", description="Switch language"),
            BotCommand(command="mode", description="Switch role view"),
            BotCommand(command="version", description="Show bot version"),
            BotCommand(command="sync_catalog", description="Admin: sync catalog from site"),
        ]
    )

    dp.include_router(admin_router)
    dp.include_router(client_router)

    scheduler = setup_scheduler(bot)
    if scheduler:
        scheduler.start()
        logger.info("Scheduler started")

    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot)
    finally:
        if scheduler:
            scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
