"""Seed the database with MiniMelts product catalog."""
from __future__ import annotations

import asyncio
import logging

from bot.config import config
from bot.db import get_active_products, get_db, init_db
from bot.utils.catalog_scraper import fetch_flavors_async

PRODUCTS = [
    "Vanilla",
    "Chocolate",
    "Strawberry",
    "Mint Chocolate",
    "Cookie & Cream",
    "Cotton Candy",
    "Banana Split",
    "Bubble Gum",
    "Tiramisu",
    "Rainbow Ice",
    "Birthday Cake",
    "Brownie Blast",
    "Cookie Dough",
    "Lemon Lime (sorbet)",
    "Mango (sorbet)",
    "Big Balls - Coconut & Chocolate",
    "Big Balls - Banana & Chocolate",
    "Big Balls - Strawberry",
    "Big Balls - Cherry",
    "Big Balls - Mango",
]

logger = logging.getLogger(__name__)


async def _get_seed_products() -> list[str]:
    try:
        names = await fetch_flavors_async(config.catalog_source_url)
        if names:
            return names
    except Exception:
        logger.exception("Failed to fetch catalog from site, using fallback seed list")
    return PRODUCTS


async def seed() -> None:
    await init_db()

    existing = await get_active_products()
    if existing:
        print(f"Catalog already has {len(existing)} products. Skipping seed.")
        return

    names = await _get_seed_products()
    db = await get_db()
    try:
        for idx, name in enumerate(names, start=1):
            await db.execute(
                "INSERT INTO products (name, sort_order, is_active) VALUES (?, ?, 1)",
                (name, idx),
            )
        await db.commit()
        print(f"Seeded {len(names)} products into catalog")
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(seed())
