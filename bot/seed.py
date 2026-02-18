"""Seed the database with MiniMelts product catalog.

Run once: python -m bot.seed
Products sourced from minimelts.eu European catalog.
"""
from __future__ import annotations

import asyncio

from bot.db import init_db, get_db, get_active_products

# European MiniMelts catalog
PRODUCTS = [
    # Classic Ice Cream
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
    # Sorbets
    "Lemon Lime (sorbet)",
    "Mango (sorbet)",
    # Big Balls
    "Big Balls — Coconut & Chocolate",
    "Big Balls — Banana & Chocolate",
    "Big Balls — Strawberry",
    "Big Balls — Cherry",
    "Big Balls — Mango",
]


async def seed() -> None:
    await init_db()

    existing = await get_active_products()
    if existing:
        print(f"Catalog already has {len(existing)} products. Skipping seed.")
        print("To re-seed, clear the products table first.")
        return

    db = await get_db()
    try:
        for idx, name in enumerate(PRODUCTS, start=1):
            await db.execute(
                "INSERT INTO products (name, sort_order, is_active) VALUES (?, ?, 1)",
                (name, idx),
            )
        await db.commit()
        print(f"Seeded {len(PRODUCTS)} products into catalog:")
        for i, name in enumerate(PRODUCTS, 1):
            print(f"  {i:2d}. {name}")
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(seed())
