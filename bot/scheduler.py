"""APScheduler-based scheduler for automatic order session management.

Handles:
- Auto-open order sessions on configured days/times
- Auto-remind clients who haven't ordered (N hours before deadline)
- Auto-close sessions at deadline and send summary to admin
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot import db
from bot.config import config, ScheduleEntry

logger = logging.getLogger(__name__)

DAY_MAP = {
    "MON": "mon",
    "TUE": "tue",
    "WED": "wed",
    "THU": "thu",
    "FRI": "fri",
    "SAT": "sat",
    "SUN": "sun",
}

DAY_NAME_ES = {
    "MON": "lunes",
    "TUE": "martes",
    "WED": "miercoles",
    "THU": "jueves",
    "FRI": "viernes",
    "SAT": "sabado",
    "SUN": "domingo",
}


def _find_next_close(open_entry: ScheduleEntry) -> ScheduleEntry | None:
    """Find the closest close entry after the given open entry."""
    if not config.schedule_close:
        return None

    day_order = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    open_idx = day_order.index(open_entry.day) if open_entry.day in day_order else 0

    best = None
    best_dist = 8  # > 7

    for close in config.schedule_close:
        close_idx = day_order.index(close.day) if close.day in day_order else 0
        dist = (close_idx - open_idx) % 7
        if dist == 0 and (close.hour, close.minute) <= (open_entry.hour, open_entry.minute):
            dist = 7
        if dist < best_dist:
            best_dist = dist
            best = close

    return best


async def _auto_open(bot: Bot, open_entry: ScheduleEntry) -> None:
    """Automatically open order session and notify all approved clients."""
    try:
        existing = await db.get_active_session()
        if existing:
            logger.info("Session already open, skipping auto-open")
            return

        close_entry = _find_next_close(open_entry)
        deadline_text = ""
        if close_entry:
            day_name = DAY_NAME_ES.get(close_entry.day, close_entry.day)
            deadline_text = f" Haz tu pedido antes del {day_name} a las {close_entry.hour:02d}:{close_entry.minute:02d}."

        deadline_str = None
        if close_entry:
            deadline_str = f"{close_entry.day}:{close_entry.hour:02d}:{close_entry.minute:02d}"

        session_id = await db.open_session(deadline=deadline_str)
        clients = await db.get_approved_clients()

        sent = 0
        for client in clients:
            try:
                await bot.send_message(
                    client["telegram_id"],
                    f"Buenos dias! Pedidos abiertos.{deadline_text}",
                )
                sent += 1
            except Exception:
                logger.warning("Failed to notify client %s", client["telegram_id"])

        logger.info("Auto-opened session #%d, notified %d/%d clients", session_id, sent, len(clients))

        for admin_id in config.admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    f"Sesion #{session_id} abierta automaticamente. Notificados: {sent}/{len(clients)}.",
                )
            except Exception:
                pass

    except Exception:
        logger.exception("Error in auto-open")


async def _auto_remind(bot: Bot) -> None:
    """Remind clients who haven't ordered yet."""
    try:
        session = await db.get_active_session()
        if not session:
            return

        clients = await db.get_clients_without_order(session["id"])
        if not clients:
            return

        sent = 0
        for client in clients:
            try:
                await bot.send_message(
                    client["telegram_id"],
                    "Recordatorio: los pedidos se cierran pronto. No olvides hacer tu pedido!",
                )
                sent += 1
            except Exception:
                logger.warning("Failed to remind client %s", client["telegram_id"])

        logger.info("Auto-reminder sent to %d/%d clients", sent, len(clients))

    except Exception:
        logger.exception("Error in auto-remind")


async def _auto_close(bot: Bot) -> None:
    """Automatically close order session and send summary to admin."""
    try:
        session = await db.get_active_session()
        if not session:
            return

        session_id = session["id"]
        await db.close_session()

        count = await db.count_session_orders(session_id)
        total_clients = len(await db.get_approved_clients())
        summary_data = await db.get_session_summary(session_id)

        lines = [f"Sesion #{session_id} cerrada automaticamente.\n"]
        lines.append(f"Pedidos: {count}/{total_clients} clientes\n")

        grand_total = 0
        for item in summary_data:
            lines.append(f"  {item['name']:.<30} {item['total']}")
            grand_total += item["total"]
        lines.append(f"\nTOTAL unidades: {grand_total}")

        text = "\n".join(lines)
        for admin_id in config.admin_ids:
            try:
                await bot.send_message(admin_id, text)
            except Exception:
                pass

        logger.info("Auto-closed session #%d, %d orders", session_id, count)

    except Exception:
        logger.exception("Error in auto-close")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler | None:
    """Configure and return the scheduler. Returns None if no schedule configured."""
    if not config.schedule_open and not config.schedule_close:
        logger.info("No schedule configured, scheduler disabled")
        return None

    scheduler = AsyncIOScheduler(timezone=config.timezone)

    # Schedule auto-open jobs
    for entry in config.schedule_open:
        cron_day = DAY_MAP.get(entry.day)
        if not cron_day:
            continue
        trigger = CronTrigger(
            day_of_week=cron_day,
            hour=entry.hour,
            minute=entry.minute,
            timezone=config.timezone,
        )
        scheduler.add_job(
            _auto_open,
            trigger,
            args=[bot, entry],
            id=f"auto_open_{entry.day}_{entry.hour}_{entry.minute}",
            replace_existing=True,
        )
        logger.info("Scheduled auto-open: %s %02d:%02d", entry.day, entry.hour, entry.minute)

    # Schedule auto-close jobs
    for entry in config.schedule_close:
        cron_day = DAY_MAP.get(entry.day)
        if not cron_day:
            continue
        trigger = CronTrigger(
            day_of_week=cron_day,
            hour=entry.hour,
            minute=entry.minute,
            timezone=config.timezone,
        )
        scheduler.add_job(
            _auto_close,
            trigger,
            args=[bot],
            id=f"auto_close_{entry.day}_{entry.hour}_{entry.minute}",
            replace_existing=True,
        )
        logger.info("Scheduled auto-close: %s %02d:%02d", entry.day, entry.hour, entry.minute)

        # Schedule reminder N hours before close
        if config.reminder_hours_before > 0:
            remind_hour = entry.hour - config.reminder_hours_before
            remind_day = cron_day
            if remind_hour < 0:
                remind_hour += 24
                # Go to previous day
                days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
                idx = days.index(cron_day)
                remind_day = days[(idx - 1) % 7]

            trigger_remind = CronTrigger(
                day_of_week=remind_day,
                hour=remind_hour,
                minute=entry.minute,
                timezone=config.timezone,
            )
            scheduler.add_job(
                _auto_remind,
                trigger_remind,
                args=[bot],
                id=f"auto_remind_{entry.day}_{entry.hour}_{entry.minute}",
                replace_existing=True,
            )
            logger.info("Scheduled auto-remind: %s %02d:%02d", remind_day, remind_hour, entry.minute)

    return scheduler
