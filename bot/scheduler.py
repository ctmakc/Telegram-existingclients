"""APScheduler-based automation for order sessions."""
from __future__ import annotations

import logging

from aiogram import Bot

from bot import db
from bot.config import ScheduleEntry, config
from bot.locales import day_name, t

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
except Exception:  # pragma: no cover
    AsyncIOScheduler = None
    CronTrigger = None

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


def _find_next_close(open_entry: ScheduleEntry) -> ScheduleEntry | None:
    if not config.schedule_close:
        return None

    order = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    open_idx = order.index(open_entry.day) if open_entry.day in order else 0

    best: ScheduleEntry | None = None
    best_dist = 8
    for close in config.schedule_close:
        close_idx = order.index(close.day) if close.day in order else 0
        dist = (close_idx - open_idx) % 7
        if dist == 0 and (close.hour, close.minute) <= (open_entry.hour, open_entry.minute):
            dist = 7
        if dist < best_dist:
            best_dist = dist
            best = close
    return best


async def _auto_open(bot: Bot, open_entry: ScheduleEntry) -> None:
    try:
        if await db.get_active_session():
            logger.info("Session already open, skipping auto-open")
            return

        close_entry = _find_next_close(open_entry)
        deadline_str = None
        if close_entry:
            deadline_str = f"{close_entry.day}:{close_entry.hour:02d}:{close_entry.minute:02d}"

        session_id = await db.open_session(deadline=deadline_str)
        clients = await db.get_approved_clients()

        sent = 0
        for client in clients:
            try:
                lang = await db.get_user_language(client["telegram_id"])
                deadline = ""
                if close_entry:
                    deadline = t(
                        lang,
                        "deadline_suffix",
                        day=day_name(lang, close_entry.day),
                        time=f"{close_entry.hour:02d}:{close_entry.minute:02d}",
                    )
                await bot.send_message(client["telegram_id"], t(lang, "auto_open_client", deadline=deadline))
                sent += 1
            except Exception:
                logger.warning("Failed to notify client %s", client["telegram_id"])

        for admin_id in await db.get_admin_telegram_ids():
            try:
                lang = await db.get_user_language(admin_id)
                await bot.send_message(
                    admin_id,
                    t(lang, "session_opened", id=session_id, sent=sent, total=len(clients)),
                )
            except Exception:
                continue

        logger.info("Auto-opened session #%d, notified %d/%d", session_id, sent, len(clients))
    except Exception:
        logger.exception("Error in auto-open")


async def _auto_remind(bot: Bot) -> None:
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
                lang = await db.get_user_language(client["telegram_id"])
                await bot.send_message(client["telegram_id"], t(lang, "admin_remind_notice"))
                sent += 1
            except Exception:
                logger.warning("Failed to remind client %s", client["telegram_id"])

        logger.info("Auto-reminder sent to %d/%d", sent, len(clients))
    except Exception:
        logger.exception("Error in auto-remind")


async def _auto_close(bot: Bot) -> None:
    try:
        session = await db.get_active_session()
        if not session:
            return

        session_id = session["id"]
        await db.close_session()

        count = await db.count_session_orders(session_id)
        total_clients = len(await db.get_approved_clients())
        summary_data = await db.get_session_summary(session_id)

        for admin_id in await db.get_admin_telegram_ids():
            try:
                lang = await db.get_user_language(admin_id)
                lines = [
                    f"📊 {t(lang, 'summary_title', id=session_id)}",
                    t(lang, "summary_orders", count=count, total=total_clients),
                    "",
                ]
                grand_total = 0
                for item in summary_data:
                    lines.append(f"• {item['name']}: {item['total']}")
                    grand_total += item["total"]
                lines.append(t(lang, "summary_grand", total=grand_total))
                await bot.send_message(admin_id, "\n".join(lines))
            except Exception:
                continue

        logger.info("Auto-closed session #%d", session_id)
    except Exception:
        logger.exception("Error in auto-close")


def setup_scheduler(bot: Bot):
    if not config.schedule_open and not config.schedule_close:
        logger.info("No schedule configured, scheduler disabled")
        return None

    if AsyncIOScheduler is None or CronTrigger is None:
        logger.warning("apscheduler is not installed; scheduler disabled")
        return None

    scheduler = AsyncIOScheduler(timezone=config.timezone)

    for entry in config.schedule_open:
        day = DAY_MAP.get(entry.day)
        if not day:
            continue
        scheduler.add_job(
            _auto_open,
            CronTrigger(day_of_week=day, hour=entry.hour, minute=entry.minute, timezone=config.timezone),
            args=[bot, entry],
            id=f"auto_open_{entry.day}_{entry.hour}_{entry.minute}",
            replace_existing=True,
        )

    for entry in config.schedule_close:
        day = DAY_MAP.get(entry.day)
        if not day:
            continue
        scheduler.add_job(
            _auto_close,
            CronTrigger(day_of_week=day, hour=entry.hour, minute=entry.minute, timezone=config.timezone),
            args=[bot],
            id=f"auto_close_{entry.day}_{entry.hour}_{entry.minute}",
            replace_existing=True,
        )

        if config.reminder_hours_before > 0:
            remind_hour = entry.hour - config.reminder_hours_before
            remind_day = day
            if remind_hour < 0:
                remind_hour += 24
                days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
                remind_day = days[(days.index(day) - 1) % 7]

            scheduler.add_job(
                _auto_remind,
                CronTrigger(day_of_week=remind_day, hour=remind_hour, minute=entry.minute, timezone=config.timezone),
                args=[bot],
                id=f"auto_remind_{entry.day}_{entry.hour}_{entry.minute}",
                replace_existing=True,
            )

    return scheduler
