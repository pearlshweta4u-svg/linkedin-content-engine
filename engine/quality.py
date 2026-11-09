"""Mechanical quality gate. It catches the AI tells and policy breaches that a
regex can catch; judgement-based review still happens in the Humanizer pass."""
from __future__ import annotations

import re
from datetime import date, timedelta

BANNED_PHRASES = [
    "delve", "game-changer", "game changer", "unlock", "empower", "transformative",
    "tapestry", "testament to", "pivotal", "in today's fast-paced", "let that sink in",
    "here's the thing", "the truth is", "navigate the", "landscape of", "embark",
    "elevate your", "supercharge", "comment yes", "tag a friend", "agree?",
    "it's not about", "isn't just about", "in conclusion", "at the end of the day",
    "mondaymotivation", "#motivation",
]
# Medical overreach. Matched as whole words / phrases, case-insensitive.
MEDICAL_RED_FLAGS = [
    r"\bcure[sd]?\b", r"\breverse[sd]?\s+(your\s+)?(thyroid|pcos|hashimoto|diabetes)",
    r"\bheal(ed|s)?\s+your\b", r"\bget\s+off\s+(your\s+)?(medication|meds|thyroxine|thyronorm)",
    r"\bstop\s+(taking\s+)?(your\s+)?(medication|meds)\b", r"\bguarantee[sd]?\b",
    r"\b\d+\s?(mg|mcg|iu)\b(?!\s*/)",  # doses; lab units like mg/dL are fine
    r"\bdetox\b", r"\bmiracle\b",
]
REQUIRES_SOURCE_CATEGORIES = {"save_worthy", "health_wellness"}
NUMBER_CLAIM = re.compile(r"\b\d+(\.\d+)?\s?%|\b\d+\s+(in|out of)\s+\d+\b", re.I)


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def first_line(text: str) -> str:
    for line in text.strip().splitlines():
        if line.strip():
            return line.strip()
    return ""


def hook_shape(text: str) -> str:
    """Crude fingerprint of how a post opens, to stop repetitive hooks."""
    h = first_line(text).lower()
    if not h:
        return "empty"
    if re.match(r"^\d", h):
        return "starts_with_number"
    if h.endswith("?"):
        return "question"
    if h.startswith(('"', "“", "'")):
        return "quote"
    if re.match(r"^(she|he|my client|a client)\b", h):
        return "client_third_person"
    if re.match(r"^(i|i'm|i've|last|in \d{4}|when i)\b", h):
        return "first_person_scene"
    if re.match(r"^(most|every|nobody|no one|everyone)\b", h):
        return "sweeping_claim"
    return "statement"


def check(record: dict, settings: dict, history: list[dict] | None = None) -> list[str]:
    """Return a list of issues. Empty list == pass. Strings starting with 'BLOCK:'
    must be fixed; 'WARN:' items are shown to Shweta at approval."""
    q = settings["quality"]
    text = record.get("final") or ""
    issues: list[str] = []
    lower = text.lower()

    if not text.strip():
        return ["BLOCK: final text is empty"]
    if not record.get("humanizer", {}).get("applied"):
        issues.append("BLOCK: Humanizer pass not recorded (mandatory for every post)")

    wc = word_count(text)
    max_words = q["max_words_save_worthy"] if record.get("category") == "save_worthy" else q["max_words"]
    if wc < q["min_words"]:
        issues.append(f"WARN: only {wc} words (guide {q['min_words']}-{max_words})")
    if wc > max_words:
        issues.append(f"BLOCK: {wc} words, over the {max_words}-word limit for this category")
    if len(text) > 3000:
        issues.append("BLOCK: over LinkedIn's 3,000-character limit")

    dashes = text.count("—") + text.count(" – ")
    if dashes:
        issues.append(f"BLOCK: {dashes} em/en dash(es); rewrite without them")

    for phrase in BANNED_PHRASES:
        if phrase in lower:
            issues.append(f"BLOCK: banned phrase '{phrase}'")

    for pat in MEDICAL_RED_FLAGS:
        for m in re.finditer(pat, lower):
            before = lower[max(0, m.start() - 14):m.start()]
            if re.search(r"\b(not|no|never|isn't|aren't|won't|don't)\s+(a\s+)?$", before):
                continue  # "not cured", "no guarantee", "don't stop your medication"
            issues.append(f"BLOCK: medical red flag '{m.group(0)}'")
            break

    tags = re.findall(r"(?<!\w)#\w+", text)
    if len(tags) > q["max_hashtags"]:
        issues.append(f"BLOCK: {len(tags)} hashtags (max {q['max_hashtags']})")

    if record.get("category") in REQUIRES_SOURCE_CATEGORIES and not record.get("sources"):
        issues.append("BLOCK: research-based category with no sources recorded")
    if NUMBER_CLAIM.search(text) and not record.get("sources") and record.get("category") != "client_story":
        issues.append("WARN: statistic-like number in text but no sources recorded")
    for s in record.get("sources") or []:
        if not s.get("url"):
            issues.append(f"BLOCK: source without URL: {s.get('title', '?')}")

    # Repetition against history
    history = [h for h in (history or []) if h.get("post_id") != record.get("post_id")]
    published = [h for h in history if h.get("publish_status") == "published" or h.get("approval_status") == "approved"]
    published.sort(key=lambda h: h["date"])
    recent = published[-q["hook_lookback_posts"]:]
    my_hook = first_line(text).lower()
    for h in recent:
        if first_line(h.get("final") or "").lower() == my_hook:
            issues.append(f"BLOCK: identical hook to {h['post_id']}")
    shape = hook_shape(text)
    last3 = [hook_shape(h.get("final") or "") for h in recent[-3:]]
    if len(last3) == 3 and all(s == shape for s in last3):
        issues.append(f"WARN: hook shape '{shape}' used in each of the last 3 posts")

    try:
        this_day = date.fromisoformat(record["date"])
    except (KeyError, ValueError):
        this_day = None
    if this_day:
        story_cut = this_day - timedelta(days=q["story_cooldown_days"])
        topic_cut = this_day - timedelta(days=q["topic_cooldown_days"])
        for h in published:
            hd = date.fromisoformat(h["date"])
            shared = set(record.get("story_ids") or []) & set(h.get("story_ids") or [])
            if shared and hd >= story_cut:
                issues.append(f"BLOCK: story {sorted(shared)} used on {h['date']} (cool-down {q['story_cooldown_days']}d)")
            if record.get("topic") and h.get("topic", "").strip().lower() == record["topic"].strip().lower() and hd >= topic_cut:
                issues.append(f"BLOCK: topic repeated from {h['post_id']}")
    return issues


def passed(issues: list[str]) -> bool:
    return not any(i.startswith("BLOCK") for i in issues)
