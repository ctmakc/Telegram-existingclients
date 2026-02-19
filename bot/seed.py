"""Seed the database with MiniMelts product catalog."""
from __future__ import annotations

import asyncio

from bot.db import get_active_products, get_db, init_db

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


async def seed() -> None:
    await init_db()

    existing = await get_active_products()
    if existing:
        print(f"Catalog already has {len(existing)} products. Skipping seed.")
        return

    db = await get_db()
    try:
        for idx, name in enumerate(PRODUCTS, start=1):
            await db.execute(
                "INSERT INTO products (name, sort_order, is_active) VALUES (?, ?, 1)",
                (name, idx),
            )
        await db.commit()
        print(f"Seeded {len(PRODUCTS)} products into catalog")
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(seed())
