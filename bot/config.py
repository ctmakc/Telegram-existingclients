from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "bot.db"


@dataclass
class ScheduleEntry:
    day: str  # MON, TUE, ...
    hour: int
    minute: int


def _parse_schedule(raw: str) -> list[ScheduleEntry]:
    """Parse 'MON:09:00,THU:09:00' into list of ScheduleEntry."""
    if not raw:
        return []
    entries: list[ScheduleEntry] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        tokens = part.split(":")
        if len(tokens) != 3:
            continue
        entries.append(ScheduleEntry(day=tokens[0].upper(), hour=int(tokens[1]), minute=int(tokens[2])))
    return entries


@dataclass
class Config:
    bot_token: str = ""
    admin_ids: list[int] = field(default_factory=list)
    schedule_open: list[ScheduleEntry] = field(default_factory=list)
    schedule_close: list[ScheduleEntry] = field(default_factory=list)
    reminder_hours_before: int = 4
    timezone: str = "Europe/Madrid"

    @classmethod
    def from_env(cls) -> Config:
        token = os.getenv("BOT_TOKEN", "")
        admin_ids_raw = os.getenv("ADMIN_IDS", "")
        admin_ids = [int(x.strip()) for x in admin_ids_raw.split(",") if x.strip()]
        return cls(
            bot_token=token,
            admin_ids=admin_ids,
            schedule_open=_parse_schedule(os.getenv("SCHEDULE_OPEN", "")),
            schedule_close=_parse_schedule(os.getenv("SCHEDULE_CLOSE", "")),
            reminder_hours_before=int(os.getenv("REMINDER_HOURS_BEFORE", "4")),
            timezone=os.getenv("TIMEZONE", "Europe/Madrid"),
        )

    def is_admin(self, telegram_id: int) -> bool:
        return telegram_id in self.admin_ids


config = Config.from_env()
