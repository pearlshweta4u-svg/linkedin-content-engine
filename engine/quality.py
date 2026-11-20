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

# Story posts must follow a named storytelling structure (Shweta, 9 Nov 2026).
STORY_FRAMEWORKS = {
    "client_story": ("STAR", ["situation", "task", "action", "result", "lesson"]),
    "personal_story": ("story_arc", ["moment", "struggle", "action", "change", "lesson"]),
}
# Plain language in story posts: few medical terms, few numbers.
MEDICAL_TERMS = [
    "tsh", "t3", "t4", "ferritin", "b12", "hba1c", "anti-tpo", "antibod", "cortisol",
    "insulin", "homa", "crp", "haemoglobin", "hemoglobin", "levothyroxine", "thyroxine",
    "selenium", "ashwagandha", "magnesium", "berberine", "inositol", "hashimoto",
    "prolactin", "conversion", "deficien", "inflammat", "glucose", "supplement",
]
STORY_MAX_TERMS = 4

# Hook: the text LinkedIn shows before "...see more" (~140 chars on mobile, ~210 desktop).
HOOK_STYLES = {"curiosity_gap", "surprising_number", "story_drop_in", "contrarian", "direct_question", "relatable_moment"}
HOOK_MAX_MOBILE = 140
HOOK_MAX_HARD = 210
WEAK_OPENERS = ("tomorrow is", "today is", "in this post", "let's talk", "lets talk", "here are", "here is",
                "i want to share", "did you know", "i'm excited", "i am excited", "happy ", "as a coach",
                "in today's", "have you ever wondered")
STORY_MAX_NUMBERS = 3
# Thursday save-worthy posts (Shweta, 18 Nov 2026): research shapes the advice, but the
# post itself carries no exact numbers, links or study citations; it is told through a
# client problem or her own story. Sources stay in the record and the approval email.
SAVE_WORTHY_CITATION_PHRASES = (
    "et al", "published in", "journal", "a new study", "a recent study", "the study",
    "this study", "researchers found", "according to a", "according to research",
    "according to the", "meta-analysis", "randomised", "randomized",
)
URL_RE = re.compile(r"https?://|www\.|\b[\w-]+\.(com|org|gov|in|net|io)(/|\b)", re.I)
LIST_MARKER_RE = re.compile(r"^\s*\d{1,2}[.)]\s", re.M)
# A client case (C..) or personal story (P..) used only as a brief example (Wed/Thu)
# rests for this many days; full story posts (Mon/Tue) keep story_cooldown_days.
EXAMPLE_CATEGORIES = {"educational", "save_worthy"}
# Same rule for Friday health posts (Shweta, 20 Nov 2026).
NO_STATS_CATEGORIES = {"save_worthy": "Thursday", "health_wellness": "Friday"}

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

    # Hook quality: the first paragraph is the preview people decide on
    hook = text.strip().split("\n\n", 1)[0].strip()
    if len(hook) > HOOK_MAX_HARD:
        issues.append(f"BLOCK: hook (first paragraph) is {len(hook)} chars; LinkedIn cuts it at ~{HOOK_MAX_HARD} on desktop, ~{HOOK_MAX_MOBILE} on mobile")
    elif len(hook) > HOOK_MAX_MOBILE:
        issues.append(f"WARN: hook is {len(hook)} chars; the curiosity must land in the first ~{HOOK_MAX_MOBILE} for mobile")
    if hook.lower().startswith(WEAK_OPENERS):
        issues.append(f"BLOCK: weak, generic opener ('{hook[:30]}...'); open with the most surprising specific")
    style = record.get("hook_style")
    if style not in HOOK_STYLES:
        issues.append(f"BLOCK: hook_style must be one of {sorted(HOOK_STYLES)}")

    # Storytelling structure + plain language for story categories
    cat = record.get("category")
    if cat in STORY_FRAMEWORKS:
        name, beats = STORY_FRAMEWORKS[cat]
        struct = record.get("story_structure") or {}
        missing = [b for b in beats if not str(struct.get(b, "")).strip()]
        if missing:
            issues.append(f"BLOCK: {name} structure incomplete, missing beats: {', '.join(missing)}")
        body = re.sub(r"(?<!\w)#\w+", "", lower)
        terms = sorted({t for t in MEDICAL_TERMS if t in body})
        if len(terms) > STORY_MAX_TERMS:
            issues.append(f"BLOCK: too clinical for a story post ({len(terms)} medical terms: {', '.join(terms)}; max {STORY_MAX_TERMS})")
        nums = re.findall(r"\b\d+(?:\.\d+)?\b", body)
        if len(nums) > STORY_MAX_NUMBERS:
            issues.append(f"WARN: {len(nums)} numbers in a story post; keep the {STORY_MAX_NUMBERS} that matter most")

    # Wednesday: one idea, shown through a client example
    ids = record.get("story_ids") or []
    if cat == "educational" and not any(str(i).upper().startswith("C") for i in ids):
        issues.append("WARN: Wednesday post has no client example; anchor the idea in a case from case-bank-clients.md (add its id to story_ids)")
    # Thursday: no numbers, links or study citations in the post; relate it to a client or personal story
    if cat in NO_STATS_CATEGORIES:
        day = NO_STATS_CATEGORIES[cat]
        body = re.sub(r"(?<!\w)#\w+", "", text)
        if URL_RE.search(body):
            issues.append(f"BLOCK: {day} post contains a link; keep sources in the record, not the post")
        cites = sorted({p for p in SAVE_WORTHY_CITATION_PHRASES if p in body.lower()})
        if cites:
            issues.append(f"BLOCK: {day} post cites studies ({', '.join(cites)}); explain the finding in plain words instead")
        nums = re.findall(r"\d+(?:[.,]\d+)?", LIST_MARKER_RE.sub("", body))
        if nums:
            issues.append(f"BLOCK: {day} post has exact numbers ({', '.join(nums[:5])}); use plain words (\"most\", \"in your forties\")")
        if not ids:
            issues.append(f"WARN: {day} post isn't linked to a client problem or personal story (story_ids empty)")

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
        example_cut = this_day - timedelta(days=q.get("example_cooldown_days", 14))
        topic_cut = this_day - timedelta(days=q["topic_cooldown_days"])
        for h in published:
            hd = date.fromisoformat(h["date"])
            shared = set(record.get("story_ids") or []) & set(h.get("story_ids") or [])
            # Full story posts (Mon/Tue) rest story_cooldown_days; a story used only as an
            # example in a Wed/Thu post rests example_cooldown_days.
            as_example = cat in EXAMPLE_CATEGORIES or h.get("category") in EXAMPLE_CATEGORIES
            if shared and hd >= (example_cut if as_example else story_cut):
                days = q.get("example_cooldown_days", 14) if as_example else q["story_cooldown_days"]
                issues.append(f"BLOCK: story {sorted(shared)} used on {h['date']} (cool-down {days}d)")
            if record.get("topic") and h.get("topic", "").strip().lower() == record["topic"].strip().lower() and hd >= topic_cut:
                issues.append(f"BLOCK: topic repeated from {h['post_id']}")
    return issues


def passed(issues: list[str]) -> bool:
    return not any(i.startswith("BLOCK") for i in issues)
