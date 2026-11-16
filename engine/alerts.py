"""Pre-approval alerts: things Shweta must see at the top of the approval email.

Added 16 Nov 2026: the Sunday evening run failed (usage limit), so Monday's post
went out with a sample card made on 9 Nov instead of her album photo, and nothing
in the approval email said so."""
from __future__ import annotations

from datetime import date, timedelta

PHOTO_CATEGORIES = ("personal_story", "client_story", "educational")
SCENE_CATEGORIES = ("save_worthy", "health_wellness")


def expected_template(rec: dict, settings: dict) -> str | None:
    if not settings.get("images_enabled"):
        return None
    use_for = (settings.get("photos") or {}).get("use_for") or list(PHOTO_CATEGORIES)
    if rec.get("category") in use_for:
        return "photo"
    if rec.get("category") in SCENE_CATEGORIES:
        return "scene"
    return None


def _last(rec: dict, event: str) -> str | None:
    ts = [h["at"] for h in rec.get("history", []) if h.get("event") == event]
    return max(ts) if ts else None


def pre_approval_alerts(rec: dict, settings: dict) -> list[str]:
    """Return human-readable alert lines (empty list = nothing unusual)."""
    out: list[str] = []
    slot = date.fromisoformat(rec["date"])
    # The evening run before a slot is the calendar day before it (Sunday for Monday).
    earliest_ok = slot - timedelta(days=1)

    created = _last(rec, "created")
    stale = bool(created and date.fromisoformat(created[:10]) < earliest_ok)
    if stale:
        out.append(
            f"This post was written on {created[:10]}, not by last night's run "
            "(the evening run may have failed). Check that it is still what you want."
        )

    want = expected_template(rec, settings)
    spec = rec.get("image_spec") or {}
    if want:
        if not rec.get("image_path"):
            out.append(f"No image. This day should use your {'album photo' if want == 'photo' else 'scene photo'}.")
        elif spec.get("template") != want:
            kind = "your album photo" if want == "photo" else "one of your scene photos"
            out.append(
                f"The image is a '{spec.get('template', 'unknown')}' text card, not {kind}. "
                "Reply EDIT if you want the image redone, or APPROVE to post it as is."
            )
    rendered = _last(rec, "image_rendered")
    if not stale and rec.get("image_path") and rendered and date.fromisoformat(rendered[:10]) < earliest_ok:
        out.append(f"The image was made on {rendered[:10]}, not by last night's run. It may be an old image.")
    return out
