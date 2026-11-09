"""Slot arithmetic: which date gets which category, and when a slot is publishable."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from .config import CATEGORY_BY_WEEKDAY, IST, WEEKDAY_NAMES


def _hm(value: str) -> time:
    h, m = value.split(":")
    return time(int(h), int(m))


def is_publish_day(d: date, settings: dict) -> bool:
    return d.weekday() in settings["publish_weekdays"]


def slot_datetime(d: date, settings: dict) -> datetime:
    return datetime.combine(d, _hm(settings["publish_time"]), tzinfo=IST)


def deadline_datetime(d: date, settings: dict) -> datetime:
    return datetime.combine(d, _hm(settings["publish_deadline"]), tzinfo=IST)


def post_id_for(d: date) -> str:
    return f"{d.isoformat()}-{WEEKDAY_NAMES[d.weekday()][:3].lower()}"


def category_for(d: date) -> str:
    if d.weekday() not in CATEGORY_BY_WEEKDAY:
        raise ValueError(f"{d} is a weekend; no post is scheduled")
    return CATEGORY_BY_WEEKDAY[d.weekday()]


def next_publish_day(after: date, settings: dict) -> date:
    d = after + timedelta(days=1)
    while not is_publish_day(d, settings):
        d += timedelta(days=1)
    return d


def window_state(d: date, now: datetime, settings: dict) -> str:
    """'early' before 08:00, 'open' from 08:00 to the deadline, 'closed' after."""
    if now < slot_datetime(d, settings):
        return "early"
    if now <= deadline_datetime(d, settings):
        return "open"
    return "closed"
