from __future__ import annotations

import aiosqlite

from bot.config import DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    company TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS order_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    deadline TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    session_id INTEGER NOT NULL REFERENCES order_sessions(id),
    status TEXT NOT NULL DEFAULT 'confirmed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL DEFAULT 0
);
"""


async def get_db() -> aiosqlite.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db() -> None:
    db = await get_db()
    try:
        await db.executescript(_SCHEMA)
        await db.commit()
    finally:
        await db.close()


# --------------- Clients ---------------

async def add_client(telegram_id: int, name: str, company: str | None) -> int:
    db = await get_db()
    try:
        cur = await db.execute(
            "INSERT INTO clients (telegram_id, name, company) VALUES (?, ?, ?)",
            (telegram_id, name, company),
        )
        await db.commit()
        return cur.lastrowid  # type: ignore[return-value]
    finally:
        await db.close()


async def get_client_by_tg(telegram_id: int) -> dict | None:
    db = await get_db()
    try:
        cur = await db.execute("SELECT * FROM clients WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def approve_client(client_id: int) -> None:
    db = await get_db()
    try:
        await db.execute("UPDATE clients SET status = 'approved' WHERE id = ?", (client_id,))
        await db.commit()
    finally:
        await db.close()


async def block_client(client_id: int) -> None:
    db = await get_db()
    try:
        await db.execute("UPDATE clients SET status = 'blocked' WHERE id = ?", (client_id,))
        await db.commit()
    finally:
        await db.close()


async def get_all_clients(status: str | None = None) -> list[dict]:
    db = await get_db()
    try:
        if status:
            cur = await db.execute("SELECT * FROM clients WHERE status = ?", (status,))
        else:
            cur = await db.execute("SELECT * FROM clients")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def get_pending_clients() -> list[dict]:
    return await get_all_clients(status="pending")


async def get_approved_clients() -> list[dict]:
    return await get_all_clients(status="approved")


# --------------- Products ---------------

async def add_product(name: str) -> int:
    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT COALESCE(MAX(sort_order), 0) + 1 AS next_order FROM products"
        )
        row = await cur.fetchone()
        next_order = row["next_order"]
        cur = await db.execute(
            "INSERT INTO products (name, sort_order) VALUES (?, ?)",
            (name, next_order),
        )
        await db.commit()
        return cur.lastrowid  # type: ignore[return-value]
    finally:
        await db.close()


async def get_active_products() -> list[dict]:
    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT * FROM products WHERE is_active = 1 ORDER BY sort_order"
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def get_all_products() -> list[dict]:
    db = await get_db()
    try:
        cur = await db.execute("SELECT * FROM products ORDER BY sort_order")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def delete_product(product_id: int) -> None:
    db = await get_db()
    try:
        await db.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))
        await db.commit()
    finally:
        await db.close()


async def move_product(product_id: int, direction: str) -> None:
    """Move product up or down in sort order."""
    db = await get_db()
    try:
        cur = await db.execute("SELECT id, sort_order FROM products WHERE is_active = 1 ORDER BY sort_order")
        products = [dict(r) for r in await cur.fetchall()]
        idx = next((i for i, p in enumerate(products) if p["id"] == product_id), None)
        if idx is None:
            return
        swap_idx = idx - 1 if direction == "up" and idx > 0 else idx + 1 if direction == "down" and idx < len(products) - 1 else None
        if swap_idx is None:
            return
        a, b = products[idx], products[swap_idx]
        await db.execute("UPDATE products SET sort_order = ? WHERE id = ?", (b["sort_order"], a["id"]))
        await db.execute("UPDATE products SET sort_order = ? WHERE id = ?", (a["sort_order"], b["id"]))
        await db.commit()
    finally:
        await db.close()


# --------------- Order Sessions ---------------

async def open_session(deadline: str | None = None) -> int:
    db = await get_db()
    try:
        # Close any currently active session first
        await db.execute(
            "UPDATE order_sessions SET is_active = 0, closed_at = CURRENT_TIMESTAMP WHERE is_active = 1"
        )
        cur = await db.execute(
            "INSERT INTO order_sessions (deadline) VALUES (?)",
            (deadline,),
        )
        await db.commit()
        return cur.lastrowid  # type: ignore[return-value]
    finally:
        await db.close()


async def close_session() -> None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE order_sessions SET is_active = 0, closed_at = CURRENT_TIMESTAMP WHERE is_active = 1"
        )
        await db.commit()
    finally:
        await db.close()


async def get_active_session() -> dict | None:
    db = await get_db()
    try:
        cur = await db.execute("SELECT * FROM order_sessions WHERE is_active = 1 LIMIT 1")
        row = await cur.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


# --------------- Orders ---------------

async def create_order(client_id: int, session_id: int, items: list[tuple[int, int]]) -> int:
    """Create order with items: list of (product_id, quantity)."""
    db = await get_db()
    try:
        # Cancel any previous order by this client in this session
        await db.execute(
            "UPDATE orders SET status = 'cancelled' WHERE client_id = ? AND session_id = ? AND status = 'confirmed'",
            (client_id, session_id),
        )
        cur = await db.execute(
            "INSERT INTO orders (client_id, session_id) VALUES (?, ?)",
            (client_id, session_id),
        )
        order_id = cur.lastrowid
        for product_id, quantity in items:
            if quantity > 0:
                await db.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)",
                    (order_id, product_id, quantity),
                )
        await db.commit()
        return order_id  # type: ignore[return-value]
    finally:
        await db.close()


async def get_client_orders(client_id: int, limit: int = 5) -> list[dict]:
    db = await get_db()
    try:
        cur = await db.execute(
            """SELECT o.id, o.created_at, o.status, os.deadline
               FROM orders o
               JOIN order_sessions os ON o.session_id = os.id
               WHERE o.client_id = ? AND o.status = 'confirmed'
               ORDER BY o.created_at DESC LIMIT ?""",
            (client_id, limit),
        )
        orders = [dict(r) for r in await cur.fetchall()]
        for order in orders:
            cur2 = await db.execute(
                """SELECT p.name, oi.quantity
                   FROM order_items oi
                   JOIN products p ON oi.product_id = p.id
                   WHERE oi.order_id = ?""",
                (order["id"],),
            )
            order["items"] = [dict(r) for r in await cur2.fetchall()]
        return orders
    finally:
        await db.close()


async def get_session_orders(session_id: int) -> list[dict]:
    """Get all confirmed orders for a session with client info."""
    db = await get_db()
    try:
        cur = await db.execute(
            """SELECT o.id, o.client_id, c.name AS client_name, c.company, o.created_at
               FROM orders o
               JOIN clients c ON o.client_id = c.id
               WHERE o.session_id = ? AND o.status = 'confirmed'
               ORDER BY c.name""",
            (session_id,),
        )
        orders = [dict(r) for r in await cur.fetchall()]
        for order in orders:
            cur2 = await db.execute(
                """SELECT p.id AS product_id, p.name, oi.quantity
                   FROM order_items oi
                   JOIN products p ON oi.product_id = p.id
                   WHERE oi.order_id = ?""",
                (order["id"],),
            )
            order["items"] = [dict(r) for r in await cur2.fetchall()]
        return orders
    finally:
        await db.close()


async def get_session_summary(session_id: int) -> list[dict]:
    """Aggregate quantities per product for a session."""
    db = await get_db()
    try:
        cur = await db.execute(
            """SELECT p.name, SUM(oi.quantity) AS total
               FROM order_items oi
               JOIN orders o ON oi.order_id = o.id
               JOIN products p ON oi.product_id = p.id
               WHERE o.session_id = ? AND o.status = 'confirmed'
               GROUP BY p.id
               ORDER BY p.sort_order""",
            (session_id,),
        )
        return [dict(r) for r in await cur.fetchall()]
    finally:
        await db.close()


async def get_clients_without_order(session_id: int) -> list[dict]:
    """Get approved clients who haven't placed an order in this session."""
    db = await get_db()
    try:
        cur = await db.execute(
            """SELECT c.* FROM clients c
               WHERE c.status = 'approved'
               AND c.id NOT IN (
                   SELECT o.client_id FROM orders o
                   WHERE o.session_id = ? AND o.status = 'confirmed'
               )""",
            (session_id,),
        )
        return [dict(r) for r in await cur.fetchall()]
    finally:
        await db.close()


async def count_session_orders(session_id: int) -> int:
    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT COUNT(*) AS cnt FROM orders WHERE session_id = ? AND status = 'confirmed'",
            (session_id,),
        )
        row = await cur.fetchone()
        return row["cnt"]
    finally:
        await db.close()
