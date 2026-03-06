"""Application configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class ScheduleEntry:
    day: str
    hour: int
    minute: int


@dataclass(frozen=True)
class Config:
    bot_token: str
    superadmin_ids: set[int]
    admin_ids: set[int]
    schedule_open: list[ScheduleEntry]
    schedule_close: list[ScheduleEntry]
    reminder_hours_before: int
    timezone: str
    default_language: str
    db_path: Path
    catalog_source_url: str
    bot_version: str
    image_tag: str

    def is_superadmin(self, user_id: int | None) -> bool:
        return bool(user_id) and user_id in self.superadmin_ids

    def is_admin(self, user_id: int | None) -> bool:
        return self.is_superadmin(user_id) or (bool(user_id) and user_id in self.admin_ids)


def _parse_admin_ids(raw: str) -> set[int]:
    result: set[int] = set()
    for part in raw.split(","):
        item = part.strip()
        if not item:
            continue
        try:
            result.add(int(item))
        except ValueError:
            continue
    return result


def _parse_schedule(raw: str) -> list[ScheduleEntry]:
    if not raw.strip():
        return []

    entries: list[ScheduleEntry] = []
    for chunk in raw.split(","):
        item = chunk.strip().upper()
        if not item:
            continue
        try:
            day, hour_s, minute_s = item.split(":")
            if day not in {"MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"}:
                continue
            hour = int(hour_s)
            minute = int(minute_s)
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                continue
            entries.append(ScheduleEntry(day=day, hour=hour, minute=minute))
        except ValueError:
            continue
    return entries


def _build_config() -> Config:
    db_path = Path(os.getenv("DB_PATH", "data/bot.sqlite3")).expanduser()
    if not db_path.is_absolute():
        db_path = (BASE_DIR / db_path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        reminder_hours = int(os.getenv("REMINDER_HOURS_BEFORE", "0") or 0)
    except ValueError:
        reminder_hours = 0

    admin_ids = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
    superadmin_ids = _parse_admin_ids(os.getenv("SUPERADMIN_IDS", ""))
    # Backward-compatible bootstrap: if SUPERADMIN_IDS is empty, treat ADMIN_IDS as superadmins.
    if not superadmin_ids:
        superadmin_ids = set(admin_ids)
        admin_ids = set()

    return Config(
        bot_token=os.getenv("BOT_TOKEN", "").strip(),
        superadmin_ids=superadmin_ids,
        admin_ids=admin_ids,
        schedule_open=_parse_schedule(os.getenv("SCHEDULE_OPEN", "")),
        schedule_close=_parse_schedule(os.getenv("SCHEDULE_CLOSE", "")),
        reminder_hours_before=max(0, reminder_hours),
        timezone=os.getenv("TIMEZONE", "Europe/Madrid").strip() or "Europe/Madrid",
        default_language=(os.getenv("DEFAULT_LANGUAGE", "ru").strip().lower() or "ru"),
        db_path=db_path,
        catalog_source_url=(
            os.getenv("CATALOG_SOURCE_URL", "https://minimelts.es/sabores/").strip()
            or "https://minimelts.es/sabores/"
        ),
        bot_version=(os.getenv("BOT_VERSION", "dev").strip() or "dev"),
        image_tag=(os.getenv("IMAGE_TAG", "latest").strip() or "latest"),
    )


config = _build_config()
