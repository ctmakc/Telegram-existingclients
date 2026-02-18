"""MiniMelts Order Bot — entry point."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import config
from bot.db import init_db
from bot.handlers.client import router as client_router
from bot.handlers.admin import router as admin_router
from bot.scheduler import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not config.bot_token:
        logger.error("BOT_TOKEN is not set! Copy .env.example to .env and fill in your token.")
        return

    await init_db()
    logger.info("Database initialized")

    bot = Bot(token=config.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    # Register routers — admin first so admin commands take priority
    dp.include_router(admin_router)
    dp.include_router(client_router)

    # Start scheduler if configured
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
