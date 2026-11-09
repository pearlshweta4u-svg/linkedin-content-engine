"""Paths and settings. All state lives in the git repository so that every
(ephemeral) run sees the same history."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "content" / "posts"
IMAGES_DIR = ROOT / "content" / "images"
SETTINGS_PATH = ROOT / "config" / "settings.json"
LOG_PATH = ROOT / "logs" / "engine.log"

# Asia/Kolkata has no DST, so a fixed offset is exact and needs no tzdata.
IST = timezone(timedelta(hours=5, minutes=30), name="IST")

CATEGORY_BY_WEEKDAY = {
    0: "personal_story",
    1: "client_story",
    2: "educational",
    3: "save_worthy",
    4: "health_wellness",
}
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def load_settings(path: Path | None = None) -> dict:
    with open(path or SETTINGS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def save_settings(settings: dict, path: Path | None = None) -> None:
    p = path or SETTINGS_PATH
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def now_ist() -> datetime:
    return datetime.now(IST)
