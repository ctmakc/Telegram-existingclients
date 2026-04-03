"""Database layer (SQLite + aiosqlite)."""
from __future__ import annotations

import aiosqlite

from bot.config import config


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(str(config.db_path))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    # Some restricted environments block file journal creation; keep journal in memory.
    await db.execute("PRAGMA journal_mode = MEMORY")
    await db.execute("PRAGMA synchronous = NORMAL")
    return db


async def init_db() -> None:
    db = await get_db()
    try:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL UNIQUE,
                name TEXT NOT NULL,
                company TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                group_id INTEGER,
                language TEXT NOT NULL DEFAULT 'ru',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES client_groups(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS client_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                note TEXT,
                reminder_day TEXT,
                reminder_hour INTEGER,
                reminder_minute INTEGER,
                reminder_enabled INTEGER NOT NULL DEFAULT 0,
                last_reminded_session_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_prefs (
                telegram_id INTEGER PRIMARY KEY,
                language TEXT NOT NULL DEFAULT 'ru',
                ui_mode TEXT NOT NULL DEFAULT 'client',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS admins (
                telegram_id INTEGER PRIMARY KEY,
                added_by INTEGER,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sort_order INTEGER NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS order_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opened_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                closed_at TEXT,
                status TEXT NOT NULL DEFAULT 'open',
                deadline TEXT
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                session_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES order_sessions(id) ON DELETE CASCADE,
                UNIQUE (client_id, session_id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity >= 0),
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            );
            """
        )

        # Lightweight migrations for older databases
        cur = await db.execute("PRAGMA table_info(clients)")
        cols = [r["name"] for r in await cur.fetchall()]
        if cols and "language" not in cols:
            await db.execute("ALTER TABLE clients ADD COLUMN language TEXT NOT NULL DEFAULT 'ru'")
        if cols and "group_id" not in cols:
            await db.execute("ALTER TABLE clients ADD COLUMN group_id INTEGER")

        cur = await db.execute("PRAGMA table_info(client_groups)")
        cols = [r["name"] for r in await cur.fetchall()]
        if cols and "reminder_day" not in cols:
            await db.execute("ALTER TABLE client_groups ADD COLUMN reminder_day TEXT")
        if cols and "reminder_hour" not in cols:
            await db.execute("ALTER TABLE client_groups ADD COLUMN reminder_hour INTEGER")
        if cols and "reminder_minute" not in cols:
            await db.execute("ALTER TABLE client_groups ADD COLUMN reminder_minute INTEGER")
        if cols and "reminder_enabled" not in cols:
            await db.execute(
                "ALTER TABLE client_groups ADD COLUMN reminder_enabled INTEGER NOT NULL DEFAULT 0"
            )
        if cols and "last_reminded_session_id" not in cols:
            await db.execute("ALTER TABLE client_groups ADD COLUMN last_reminded_session_id INTEGER")

        cur = await db.execute("PRAGMA table_info(order_sessions)")
        cols = [r["name"] for r in await cur.fetchall()]
        if cols and "deadline" not in cols:
            await db.execute("ALTER TABLE order_sessions ADD COLUMN deadline TEXT")

        await db.commit()
    finally:
        await db.close()


async def ensure_user_pref(telegram_id: int) -> None:
    db = await get_db()
    try:
        await db.execute(
            """
            INSERT INTO user_prefs (telegram_id, language, ui_mode)
            VALUES (?, ?, 'client')
            ON CONFLICT(telegram_id) DO NOTHING
            """,
            (telegram_id, config.default_language),
        )
        await db.commit()
    finally:
        await db.close()


async def get_user_pref(telegram_id: int) -> dict:
    await ensure_user_pref(telegram_id)
    db = await get_db()
    try:
        cur = await db.execute("SELECT * FROM user_prefs WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        return dict(row)
    finally:
        await db.close()


async def set_user_language(telegram_id: int, language: str) -> None:
    await ensure_user_pref(telegram_id)
    db = await get_db()
    try:
        await db.execute(
            """
            UPDATE user_prefs
            SET language = ?, updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
            """,
            (language, telegram_id),
        )
        await db.execute(
            "UPDATE clients SET language = ? WHERE telegram_id = ?",
            (language, telegram_id),
        )
        await db.commit()
    finally:
        await db.close()


async def set_user_mode(telegram_id: int, ui_mode: str) -> None:
    await ensure_user_pref(telegram_id)
    db = await get_db()
    try:
        await db.execute(
            """
            UPDATE user_prefs
            SET ui_mode = ?, updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
            """,
            (ui_mode, telegram_id),
        )
        await db.commit()
    finally:
        await db.close()


async def get_user_language(telegram_id: int) -> str:
    pref = await get_user_pref(telegram_id)
    return pref.get("language") or config.default_language


async def get_user_mode(telegram_id: int) -> str:
    pref = await get_user_pref(telegram_id)
    return pref.get("ui_mode") or "client"


def _base_admin_ids() -> set[int]:
    return set(config.superadmin_ids) | set(config.admin_ids)


async def get_dynamic_admin_ids() -> set[int]:
    db = await get_db()
    try:
        cur = await db.execute("SELECT telegram_id FROM admins WHERE is_active = 1")
        rows = await cur.fetchall()
        return {int(r["telegram_id"]) for r in rows}
    finally:
        await db.close()


async def get_admin_telegram_ids() -> set[int]:
    ids = _base_admin_ids()
    try:
        ids.update(await get_dynamic_admin_ids())
    except Exception:
        # Graceful fallback for older DB files before migration/initialization.
        pass
    return ids


async def is_admin_user(telegram_id: int | None) -> bool:
    if not telegram_id:
        return False
    if telegram_id in _base_admin_ids():
        return True

    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT 1 FROM admins WHERE telegram_id = ? AND is_active = 1 LIMIT 1",
            (telegram_id,),
        )
        return await cur.fetchone() is not None
    finally:
        await db.close()


async def add_dynamic_admin(telegram_id: int, added_by: int | None = None) -> None:
    if telegram_id in _base_admin_ids():
        return

    db = await get_db()
    try:
        await db.execute(
            """
            INSERT INTO admins (telegram_id, added_by, is_active, updated_at)
            VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(telegram_id) DO UPDATE SET
                is_active = 1,
                added_by = COALESCE(excluded.added_by, admins.added_by),
                updated_at = CURRENT_TIMESTAMP
            """,
            (telegram_id, added_by),
        )
        await db.commit()
    finally:
        await db.close()


async def remove_dynamic_admin(telegram_id: int) -> bool:
    if telegram_id in _base_admin_ids():
        return False

    db = await get_db()
    try:
        cur = await db.execute(
            """
            UPDATE admins
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ? AND is_active = 1
            """,
            (telegram_id,),
        )
        await db.commit()
        return (cur.rowcount or 0) > 0
    finally:
        await db.close()


async def list_admin_profiles() -> list[dict]:
    dynamic_ids = await get_dynamic_admin_ids()
    all_ids = _base_admin_ids() | dynamic_ids
    if not all_ids:
        return []

    details: dict[int, dict] = {}
    db = await get_db()
    try:
        placeholders = ",".join("?" for _ in all_ids)
        cur = await db.execute(
            f"""
            SELECT telegram_id, name, company, status
            FROM clients
            WHERE telegram_id IN ({placeholders})
            """,
            tuple(all_ids),
        )
        for row in await cur.fetchall():
            details[int(row["telegram_id"])] = dict(row)
    finally:
        await db.close()

    result: list[dict] = []
    for telegram_id in sorted(all_ids):
        role = "admin"
        if telegram_id in config.superadmin_ids:
            role = "superadmin"
        elif telegram_id in config.admin_ids:
            role = "admin_env"

        info = details.get(telegram_id) or {}
        result.append(
            {
                "telegram_id": telegram_id,
                "role": role,
                "is_dynamic": telegram_id in dynamic_ids,
                "name": info.get("name"),
                "company": info.get("company"),
                "status": info.get("status"),
            }
        )

    role_rank = {"superadmin": 0, "admin_env": 1, "admin": 2}
    result.sort(key=lambda item: (role_rank.get(item["role"], 9), item["telegram_id"]))
    return result


async def add_client(telegram_id: int, name: str, company: str | None) -> int:
    db = await get_db()
    try:
        cur = await db.execute(
            """
            INSERT INTO clients (telegram_id, name, company, status, language)
            VALUES (?, ?, ?, 'pending', ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                name = excluded.name,
                company = excluded.company
            """,
            (telegram_id, name.strip(), company, config.default_language),
        )
        await db.commit()

        cur = await db.execute("SELECT id FROM clients WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        return int(row["id"])
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


async def get_all_clients() -> list[dict]:
    db = await get_db()
    try:
        cur = await db.execute(
            """
            SELECT c.*, g.name AS group_name
            FROM clients c
            LEFT JOIN client_groups g ON g.id = c.group_id
            ORDER BY c.created_at DESC
            """
        )
        return [dict(r) for r in await cur.fetchall()]
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


async def get_approved_clients() -> list[dict]:
    db = await get_db()
    try:
        cur = await db.execute(
            """
            SELECT c.*, g.name AS group_name
            FROM clients c
            LEFT JOIN client_groups g ON g.id = c.group_id
            WHERE c.status = 'approved'
            ORDER BY c.id
            """
        )
        return [dict(r) for r in await cur.fetchall()]
    finally:
        await db.close()


async def get_client_groups() -> list[dict]:
    db = await get_db()
    try:
        cur = await db.execute(
            """
            SELECT g.*,
                   (SELECT COUNT(*) FROM clients c WHERE c.group_id = g.id) AS clients_total,
                   (SELECT COUNT(*) FROM clients c WHERE c.group_id = g.id AND c.status = 'approved') AS approved_total
            FROM client_groups g
            ORDER BY g.name COLLATE NOCASE, g.id
            """
        )
        return [dict(r) for r in await cur.fetchall()]
    finally:
        await db.close()


async def add_client_group(name: str, note: str | None = None) -> int:
    db = await get_db()
    try:
        cur = await db.execute(
            "INSERT INTO client_groups (name, note) VALUES (?, ?)",
            (name.strip(), note.strip() if note else None),
        )
        await db.commit()
        return int(cur.lastrowid)
    finally:
        await db.close()


async def get_client_group(group_id: int) -> dict | None:
    db = await get_db()
    try:
        cur = await db.execute(
            """
            SELECT g.*,
                   (SELECT COUNT(*) FROM clients c WHERE c.group_id = g.id) AS clients_total,
                   (SELECT COUNT(*) FROM clients c WHERE c.group_id = g.id AND c.status = 'approved') AS approved_total
            FROM client_groups g
            WHERE g.id = ?
            """,
            (group_id,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_group_clients(group_id: int) -> list[dict]:
    db = await get_db()
    try:
        cur = await db.execute(
            """
            SELECT c.*, g.name AS group_name
            FROM clients c
            LEFT JOIN client_groups g ON g.id = c.group_id
            WHERE c.group_id = ?
            ORDER BY c.name COLLATE NOCASE, c.id
            """,
            (group_id,),
        )
        return [dict(r) for r in await cur.fetchall()]
    finally:
        await db.close()


async def set_client_group(client_id: int, group_id: int | None) -> None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE clients SET group_id = ? WHERE id = ?",
            (group_id, client_id),
        )
        await db.commit()
    finally:
        await db.close()


async def set_group_reminder_schedule(
    group_id: int,
    day: str | None,
    hour: int | None,
    minute: int | None,
    enabled: bool,
) -> None:
    db = await get_db()
    try:
        await db.execute(
            """
            UPDATE client_groups
            SET reminder_day = ?,
                reminder_hour = ?,
                reminder_minute = ?,
                reminder_enabled = ?,
                last_reminded_session_id = NULL
            WHERE id = ?
            """,
            (day, hour, minute, 1 if enabled else 0, group_id),
        )
        await db.commit()
    finally:
        await db.close()


async def get_groups_due_for_reminder(
    day: str,
    hour: int,
    minute: int,
    session_id: int,
) -> list[dict]:
    db = await get_db()
    try:
        cur = await db.execute(
            """
            SELECT *
            FROM client_groups
            WHERE reminder_enabled = 1
              AND reminder_day = ?
              AND reminder_hour = ?
              AND reminder_minute = ?
              AND COALESCE(last_reminded_session_id, 0) != ?
            ORDER BY name COLLATE NOCASE, id
            """,
            (day, hour, minute, session_id),
        )
        return [dict(r) for r in await cur.fetchall()]
    finally:
        await db.close()


async def mark_group_reminder_sent(group_id: int, session_id: int) -> None:
    db = await get_db()
    try:
        await db.execute(
            """
            UPDATE client_groups
            SET last_reminded_session_id = ?
            WHERE id = ?
            """,
            (session_id, group_id),
        )
        await db.commit()
    finally:
        await db.close()


async def get_active_products() -> list[dict]:
    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT * FROM products WHERE is_active = 1 ORDER BY sort_order, id"
        )
        return [dict(r) for r in await cur.fetchall()]
    finally:
        await db.close()


async def add_product(name: str) -> int:
    db = await get_db()
    try:
        cur = await db.execute("SELECT COALESCE(MAX(sort_order), 0) AS m FROM products")
        row = await cur.fetchone()
        sort_order = int(row["m"]) + 1

        cur = await db.execute(
            "INSERT INTO products (name, sort_order, is_active) VALUES (?, ?, 1)",
            (name.strip(), sort_order),
        )
        await db.commit()
        return int(cur.lastrowid)
    finally:
        await db.close()


def _product_key(name: str) -> str:
    return " ".join((name or "").split()).strip().casefold()


async def sync_products_catalog(names: list[str]) -> dict:
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in names:
        name = " ".join((raw or "").split()).strip()
        if not name:
            continue
        key = _product_key(name)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(name)

    if not cleaned:
        return {"total_incoming": 0, "matched": 0, "added": 0, "reactivated": 0, "kept_extra": 0}

    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT id, name, sort_order, is_active FROM products ORDER BY sort_order, id"
        )
        rows = [dict(r) for r in await cur.fetchall()]

        # Prefer active rows for matching; keep one candidate per normalized name.
        active_by_key: dict[str, dict] = {}
        inactive_by_key: dict[str, dict] = {}
        for row in rows:
            key = _product_key(row["name"])
            if not key:
                continue
            if row["is_active"] and key not in active_by_key:
                active_by_key[key] = row
            elif not row["is_active"] and key not in inactive_by_key:
                inactive_by_key[key] = row

        used_ids: set[int] = set()
        next_order = 1
        added = 0
        reactivated = 0
        matched = 0

        for name in cleaned:
            key = _product_key(name)
            row = active_by_key.get(key)
            if row and row["id"] not in used_ids:
                matched += 1
                used_ids.add(int(row["id"]))
                await db.execute(
                    "UPDATE products SET name = ?, sort_order = ?, is_active = 1 WHERE id = ?",
                    (name, next_order, row["id"]),
                )
                next_order += 1
                continue

            row = inactive_by_key.get(key)
            if row and row["id"] not in used_ids:
                reactivated += 1
                used_ids.add(int(row["id"]))
                await db.execute(
                    "UPDATE products SET name = ?, sort_order = ?, is_active = 1 WHERE id = ?",
                    (name, next_order, row["id"]),
                )
                next_order += 1
                continue

            cur = await db.execute(
                "INSERT INTO products (name, sort_order, is_active) VALUES (?, ?, 1)",
                (name, next_order),
            )
            used_ids.add(int(cur.lastrowid))
            added += 1
            next_order += 1

        # Keep any other currently active products after the synced site catalog.
        extra_active = [r for r in rows if r["is_active"] and int(r["id"]) not in used_ids]
        for row in extra_active:
            await db.execute(
                "UPDATE products SET sort_order = ? WHERE id = ?",
                (next_order, row["id"]),
            )
            next_order += 1

        await db.commit()
        return {
            "total_incoming": len(cleaned),
            "matched": matched,
            "added": added,
            "reactivated": reactivated,
            "kept_extra": len(extra_active),
        }
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
    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT id, sort_order FROM products WHERE id = ? AND is_active = 1",
            (product_id,),
        )
        src = await cur.fetchone()
        if not src:
            return

        if direction == "up":
            cur = await db.execute(
                """
                SELECT id, sort_order FROM products
                WHERE is_active = 1 AND sort_order < ?
                ORDER BY sort_order DESC LIMIT 1
                """,
                (src["sort_order"],),
            )
        else:
            cur = await db.execute(
                """
                SELECT id, sort_order FROM products
                WHERE is_active = 1 AND sort_order > ?
                ORDER BY sort_order ASC LIMIT 1
                """,
                (src["sort_order"],),
            )

        dst = await cur.fetchone()
        if not dst:
            return

        await db.execute(
            "UPDATE products SET sort_order = ? WHERE id = ?",
            (dst["sort_order"], src["id"]),
        )
        await db.execute(
            "UPDATE products SET sort_order = ? WHERE id = ?",
            (src["sort_order"], dst["id"]),
        )
        await db.commit()
    finally:
        await db.close()


async def get_active_session() -> dict | None:
    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT * FROM order_sessions WHERE status = 'open' ORDER BY id DESC LIMIT 1"
        )
        row = await cur.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def open_session(deadline: str | None = None) -> int:
    db = await get_db()
    try:
        cur = await db.execute(
            "INSERT INTO order_sessions (status, deadline) VALUES ('open', ?)",
            (deadline,),
        )
        await db.commit()
        return int(cur.lastrowid)
    finally:
        await db.close()


async def close_session() -> None:
    db = await get_db()
    try:
        await db.execute(
            """
            UPDATE order_sessions
            SET status = 'closed', closed_at = CURRENT_TIMESTAMP
            WHERE status = 'open'
            """
        )
        await db.commit()
    finally:
        await db.close()


async def create_order(client_id: int, session_id: int, items: list[tuple[int, int]]) -> int:
    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT id FROM orders WHERE client_id = ? AND session_id = ?",
            (client_id, session_id),
        )
        existing = await cur.fetchone()

        if existing:
            order_id = int(existing["id"])
            await db.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        else:
            cur = await db.execute(
                "INSERT INTO orders (client_id, session_id) VALUES (?, ?)",
                (client_id, session_id),
            )
            order_id = int(cur.lastrowid)

        for product_id, qty in items:
            await db.execute(
                "INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)",
                (order_id, product_id, qty),
            )

        await db.commit()
        return order_id
    finally:
        await db.close()


async def get_order_for_client_session(client_id: int, session_id: int) -> dict | None:
    db = await get_db()
    try:
        cur = await db.execute(
            """
            SELECT *
            FROM orders
            WHERE client_id = ? AND session_id = ?
            LIMIT 1
            """,
            (client_id, session_id),
        )
        row = await cur.fetchone()
        if not row:
            return None

        order = dict(row)
        cur = await db.execute(
            """
            SELECT oi.product_id, oi.quantity, p.name
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
            ORDER BY p.sort_order, p.id
            """,
            (order["id"],),
        )
        order["items"] = [dict(r) for r in await cur.fetchall()]
        return order
    finally:
        await db.close()


async def get_client_orders(client_id: int, limit: int = 5) -> list[dict]:
    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT * FROM orders WHERE client_id = ? ORDER BY id DESC LIMIT ?",
            (client_id, limit),
        )
        orders = [dict(r) for r in await cur.fetchall()]

        for order in orders:
            cur = await db.execute(
                """
                SELECT p.name, oi.quantity
                FROM order_items oi
                JOIN products p ON p.id = oi.product_id
                WHERE oi.order_id = ?
                ORDER BY p.sort_order, p.id
                """,
                (order["id"],),
            )
            order["items"] = [dict(r) for r in await cur.fetchall()]

        return orders
    finally:
        await db.close()


async def count_session_orders(session_id: int) -> int:
    db = await get_db()
    try:
        cur = await db.execute("SELECT COUNT(*) AS c FROM orders WHERE session_id = ?", (session_id,))
        row = await cur.fetchone()
        return int(row["c"])
    finally:
        await db.close()


async def get_session_summary(session_id: int) -> list[dict]:
    db = await get_db()
    try:
        cur = await db.execute(
            """
            SELECT p.id, p.name, COALESCE(SUM(oi.quantity), 0) AS total
            FROM products p
            LEFT JOIN order_items oi ON oi.product_id = p.id
            LEFT JOIN orders o ON o.id = oi.order_id AND o.session_id = ?
            WHERE p.is_active = 1
            GROUP BY p.id, p.name, p.sort_order
            ORDER BY p.sort_order, p.id
            """,
            (session_id,),
        )
        rows = [dict(r) for r in await cur.fetchall()]
        return [r for r in rows if int(r["total"]) > 0]
    finally:
        await db.close()


async def get_clients_without_order(session_id: int, group_id: int | None = None) -> list[dict]:
    db = await get_db()
    try:
        if group_id is None:
            cur = await db.execute(
                """
                SELECT c.*, g.name AS group_name
                FROM clients c
                LEFT JOIN client_groups g ON g.id = c.group_id
                WHERE c.status = 'approved'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM orders o
                      WHERE o.client_id = c.id AND o.session_id = ?
                  )
                ORDER BY c.id
                """,
                (session_id,),
            )
        else:
            cur = await db.execute(
                """
                SELECT c.*, g.name AS group_name
                FROM clients c
                LEFT JOIN client_groups g ON g.id = c.group_id
                WHERE c.status = 'approved'
                  AND c.group_id = ?
                  AND NOT EXISTS (
                      SELECT 1
                      FROM orders o
                      WHERE o.client_id = c.id AND o.session_id = ?
                  )
                ORDER BY c.id
                """,
                (group_id, session_id),
            )
        return [dict(r) for r in await cur.fetchall()]
    finally:
        await db.close()


async def get_session_orders(session_id: int) -> list[dict]:
    db = await get_db()
    try:
        cur = await db.execute(
            """
            SELECT o.id, o.created_at, c.name AS client_name, c.company
            FROM orders o
            JOIN clients c ON c.id = o.client_id
            WHERE o.session_id = ?
            ORDER BY c.name COLLATE NOCASE
            """,
            (session_id,),
        )
        orders = [dict(r) for r in await cur.fetchall()]

        for order in orders:
            cur = await db.execute(
                """
                SELECT oi.product_id, oi.quantity, p.name
                FROM order_items oi
                JOIN products p ON p.id = oi.product_id
                WHERE oi.order_id = ?
                ORDER BY p.sort_order, p.id
                """,
                (order["id"],),
            )
            order["items"] = [dict(r) for r in await cur.fetchall()]

        return orders
    finally:
        await db.close()
