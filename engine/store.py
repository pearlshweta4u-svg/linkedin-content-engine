"""Post records. One JSON file per slot in content/posts/ is the source of truth
(diff-able and safe in git). `build_index` creates a throwaway SQLite database
for querying history."""
from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

from . import schedule
from .config import POSTS_DIR, WEEKDAY_NAMES, now_ist

APPROVAL_STATUSES = {"draft", "pending", "approved", "rejected", "skipped"}
PUBLISH_STATUSES = {
    "not_ready",     # still a draft / waiting for approval
    "publishing",    # an API call is in flight (or a run crashed mid-call)
    "published",
    "failed",        # last attempt failed in a known-safe way; may retry in window
    "needs_check",   # outcome unknown (e.g. timeout after POST); human must verify
    "skipped",
    "expired",       # window closed without approval
}

SECTIONS = ("draft", "final")


def new_record(d: date, settings: dict) -> dict:
    ts = now_ist().isoformat(timespec="seconds")
    return {
        "post_id": schedule.post_id_for(d),
        "date": d.isoformat(),
        "scheduled_for": schedule.slot_datetime(d, settings).isoformat(),
        "weekday": WEEKDAY_NAMES[d.weekday()],
        "category": schedule.category_for(d),
        "pillar": "",
        "topic": "",
        "angle": "",
        "format": "",
        "story_ids": [],
        "story_structure": {},
        "hook": "",
        "draft": "",
        "final": "",
        "hashtags": [],
        "image_path": None,
        "image_alt": None,
        "sources": [],
        "claims_checked": [],
        "questions_for_shweta": [],
        "humanizer": {"applied": False, "at": None, "version": None, "changes_summary": ""},
        "quality": {"passed": False, "issues": [], "checked_at": None},
        "approval_status": "draft",
        "approval": {"requested_at": None, "reminder_sent_at": None, "decided_at": None,
                     "decided_by": None, "channel": None, "note": None},
        "publish_status": "not_ready",
        "linkedin": {"urn": None, "url": None, "image_urn": None},
        "published_at": None,
        "attempts": [],
        "errors": [],
        "analytics": {},
        "history": [{"at": ts, "event": "created"}],
    }


def path_for(post_id: str, posts_dir: Path | None = None) -> Path:
    return (posts_dir or POSTS_DIR) / f"{post_id}.json"


def load(post_id: str, posts_dir: Path | None = None) -> dict | None:
    p = path_for(post_id, posts_dir)
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def save(record: dict, posts_dir: Path | None = None) -> Path:
    d = posts_dir or POSTS_DIR
    d.mkdir(parents=True, exist_ok=True)
    p = path_for(record["post_id"], d)
    tmp = p.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    tmp.replace(p)  # atomic on POSIX: never a half-written record
    return p


def log_event(record: dict, event: str, **detail) -> None:
    entry = {"at": now_ist().isoformat(timespec="seconds"), "event": event}
    entry.update({k: v for k, v in detail.items() if v is not None})
    record["history"].append(entry)


def all_records(posts_dir: Path | None = None) -> list[dict]:
    d = posts_dir or POSTS_DIR
    if not d.exists():
        return []
    out = []
    for p in sorted(d.glob("*.json")):
        with open(p, encoding="utf-8") as fh:
            out.append(json.load(fh))
    return out


def build_index(posts_dir: Path | None = None, db_path: str = ":memory:") -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    con.execute("DROP TABLE IF EXISTS posts")
    con.execute("""CREATE TABLE posts (
        post_id TEXT PRIMARY KEY, date TEXT, weekday TEXT, category TEXT, pillar TEXT,
        topic TEXT, angle TEXT, format TEXT, hook TEXT, story_ids TEXT,
        approval_status TEXT, publish_status TEXT, linkedin_url TEXT, published_at TEXT,
        word_count INTEGER, impressions INTEGER, reactions INTEGER, comments INTEGER,
        reposts INTEGER)""")
    for r in all_records(posts_dir):
        a = r.get("analytics") or {}
        con.execute("INSERT INTO posts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            r["post_id"], r["date"], r["weekday"], r["category"], r.get("pillar"),
            r.get("topic"), r.get("angle"), r.get("format"), r.get("hook"),
            ",".join(r.get("story_ids") or []), r["approval_status"], r["publish_status"],
            (r.get("linkedin") or {}).get("url"), r.get("published_at"),
            len((r.get("final") or "").split()), a.get("impressions"), a.get("reactions"),
            a.get("comments"), a.get("reposts")))
    con.commit()
    return con
