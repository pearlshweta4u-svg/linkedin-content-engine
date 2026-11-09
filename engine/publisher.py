"""Publishing state machine for one slot. Safe to run any number of times: it
publishes at most once per slot and never retries an outcome it can't verify."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Callable

from . import quality, schedule, store
from .config import ROOT
from .linkedin import Client, LinkedInError, post_url

Persist = Callable[[dict, str], None]  # (record, commit message) -> durable save


def _default_persist(posts_dir: Path | None) -> Persist:
    def persist(record: dict, message: str) -> None:
        store.save(record, posts_dir)
    return persist


def token_warning(settings: dict, today: date) -> str | None:
    li = settings["linkedin"]
    if not li.get("token_issued_on"):
        return "LinkedIn token issue date unknown; set linkedin.token_issued_on after connecting"
    issued = date.fromisoformat(li["token_issued_on"])
    left = li["token_lifetime_days"] - (today - issued).days
    if left <= 0:
        return f"LinkedIn token EXPIRED {-left} day(s) ago; reconnect (docs/SETUP.md step 4)"
    if left <= li["token_warn_days_before"]:
        return f"LinkedIn token expires in {left} day(s); reconnect soon (docs/SETUP.md step 4)"
    return None


def run(d: date, now: datetime, settings: dict, client: Client | None = None,
        dry_run: bool = False, posts_dir: Path | None = None,
        persist: Persist | None = None, external: bool = False) -> dict:
    """Returns {"result": <code>, "message": str, ...}. Result codes:
    weekend, paused, missing, already_published, needs_check, skipped, too_early,
    expired, awaiting_approval, quality_failed, config_missing, dry_run_ok,
    published, failed, auth_failed."""
    persist = persist or _default_persist(posts_dir)
    out = lambda code, msg, **kw: {"result": code, "message": msg, "post_id": schedule.post_id_for(d), **kw}

    if not schedule.is_publish_day(d, settings):
        return out("weekend", "No publishing on this day")
    if settings.get("paused"):
        return out("paused", "Publishing is paused in config/settings.json")

    rec = store.load(schedule.post_id_for(d), posts_dir)
    if rec is None:
        return out("missing", "No post was generated for this slot")

    # --- idempotency guards: checked before anything else -------------------
    if rec["publish_status"] == "published" or rec["linkedin"].get("urn"):
        return out("already_published", "Already published", url=rec["linkedin"].get("url"))
    backend = "composio" if external else settings.get("publisher", "api")
    if backend not in ("api", "zernio", "composio"):
        backend = "api"
    resume = False
    if rec["publish_status"] == "publishing" and backend == "zernio":
        # Zernio de-duplicates by Idempotency-Key, so re-sending the same slot is safe.
        resume = True
        store.log_event(rec, "resume_after_stale_lock", detail="re-sending with the same idempotency key")
    elif rec["publish_status"] in ("publishing", "needs_check"):
        if rec["publish_status"] == "publishing":
            rec["publish_status"] = "needs_check"
            store.log_event(rec, "stale_publishing_lock", detail="previous run did not finish; not retrying")
            persist(rec, f"{rec['post_id']}: stale publish lock -> needs_check")
        return out("needs_check", "A previous attempt's outcome is unknown. Check LinkedIn manually, "
                   "then run `python -m engine mark-published` or `python -m engine reset-publish`.")
    if rec["approval_status"] in ("skipped", "rejected") or rec["publish_status"] in ("skipped", "expired"):
        return out("skipped", f"Slot is {rec['approval_status']}/{rec['publish_status']}")

    state = schedule.window_state(d, now, settings)
    if state == "early":
        return out("too_early", "Before the 08:00 IST slot")
    if state == "closed" and not resume:
        rec["publish_status"] = "expired"
        store.log_event(rec, "expired", detail=f"not published by {settings['publish_deadline']} IST")
        persist(rec, f"{rec['post_id']}: expired")
        return out("expired", "Publishing window closed; slot skipped")

    # --- approval ------------------------------------------------------------
    issues = quality.check(rec, settings, store.all_records(posts_dir))
    if settings.get("mode") == "auto" and rec["approval_status"] == "pending" and quality.passed(issues):
        rec["approval_status"] = "approved"
        rec["approval"].update(decided_at=now.isoformat(timespec="seconds"), decided_by="auto-mode", channel="auto")
        store.log_event(rec, "auto_approved")
    if rec["approval_status"] != "approved":
        return out("awaiting_approval", "Not approved yet")
    if not quality.passed(issues):
        rec["quality"] = {"passed": False, "issues": issues, "checked_at": now.isoformat(timespec="seconds")}
        store.log_event(rec, "quality_failed_at_publish", detail="; ".join(issues))
        persist(rec, f"{rec['post_id']}: quality gate failed at publish")
        return out("quality_failed", "Quality gate failed: " + "; ".join(i for i in issues if i.startswith("BLOCK")))

    if backend == "zernio":
        author = (settings.get("zernio") or {}).get("account_id")
        if not author:
            return out("config_missing", "zernio.account_id not set in config/settings.json")
    else:
        author = settings["linkedin"].get("person_urn")
        if not author and backend == "api":
            return out("config_missing", "linkedin.person_urn not set (run `python -m engine whoami`)")

    if dry_run:
        return out("dry_run_ok", "All checks passed; would publish now", chars=len(rec["final"]))

    # --- take the lock durably BEFORE the irreversible call ----------------
    attempt = {"at": now.isoformat(timespec="seconds"), "outcome": None}
    rec["attempts"].append(attempt)
    rec["publish_status"] = "publishing"
    store.log_event(rec, "publish_started")
    persist(rec, f"{rec['post_id']}: publishing")  # raises if not durable -> we stop here

    if external:
        # Another tool (e.g. Composio LINKEDIN_CREATE_LINKED_IN_POST) makes the call;
        # it MUST report back with record_outcome(). The lock stays until then.
        return out("ready_external", "Lock taken. Publish exactly this text once, then record the outcome.",
                   commentary=rec["final"], author=author, image_path=rec.get("image_path"))

    if client is None:
        if backend == "zernio":
            from . import zernio
            client = zernio.Client()
        else:
            client = Client(settings["linkedin"]["api_version"])
    try:
        image_ref = None
        if rec.get("image_path") and settings.get("images_enabled"):
            ipath = ROOT / rec["image_path"]
            img = ipath.read_bytes()
            if backend == "zernio":
                from . import zernio
                image_ref = client.upload_image(author, img, zernio.guess_type(str(ipath)), ipath.name)
            else:
                image_ref = client.upload_image(author, img)
            rec["linkedin"]["image_urn"] = image_ref
        if backend == "zernio":
            from . import zernio
            urn, url = client.create_post(author, rec["final"], image_ref, rec.get("image_alt"),
                                          idempotency_key=zernio.idempotency_key(rec["post_id"]))
        else:
            urn = client.create_post(author, rec["final"], image_ref, rec.get("image_alt"))
            url = post_url(urn)
    except LinkedInError as e:
        rec["errors"].append({"at": now.isoformat(timespec="seconds"), "status": e.status,
                              "message": str(e), "body": e.body[:500]})
        if e.ambiguous and not getattr(client, "idempotent_create", False):
            rec["publish_status"] = "needs_check"
            attempt["outcome"] = "ambiguous"
            code = "needs_check"
        elif e.status in (401, 403):
            rec["publish_status"] = "failed"
            attempt["outcome"] = "auth_failed"
            code = "auth_failed"
        else:
            rec["publish_status"] = "failed"  # safe: request definitely not accepted
            attempt["outcome"] = "failed"
            code = "failed"
        store.log_event(rec, f"publish_{code}", detail=str(e))
        persist(rec, f"{rec['post_id']}: publish {code}")
        return out(code, str(e))

    rec["linkedin"]["urn"] = urn
    rec["linkedin"]["url"] = url
    rec["linkedin"]["via"] = backend
    rec["publish_status"] = "published"
    rec["published_at"] = now.isoformat(timespec="seconds")
    attempt["outcome"] = "published"
    store.log_event(rec, "published", urn=urn)
    persist(rec, f"{rec['post_id']}: published {urn}")
    return out("published", "Published", url=rec["linkedin"]["url"], urn=urn)


def record_outcome(d: date, now: datetime, outcome: str, urn: str | None = None,
                   error: str | None = None, posts_dir: Path | None = None,
                   persist: Persist | None = None) -> dict:
    """Close an external publish started with run(..., external=True).
    outcome: published | failed (request certainly rejected) | ambiguous (unknown)."""
    persist = persist or _default_persist(posts_dir)
    rec = store.load(schedule.post_id_for(d), posts_dir)
    if rec is None:
        raise ValueError("no record")
    if rec["publish_status"] != "publishing":
        raise ValueError(f"no publish in progress (status {rec['publish_status']})")
    ts = now.isoformat(timespec="seconds")
    attempt = rec["attempts"][-1] if rec["attempts"] else {}
    if outcome == "published":
        if not urn:
            raise ValueError("published needs --urn")
        rec["linkedin"].update(urn=urn, url=post_url(urn))
        rec["publish_status"] = "published"
        rec["published_at"] = ts
    elif outcome == "failed":
        rec["publish_status"] = "failed"
        rec["errors"].append({"at": ts, "status": None, "message": error or "external publish failed"})
    elif outcome == "ambiguous":
        rec["publish_status"] = "needs_check"
        rec["errors"].append({"at": ts, "status": None, "message": error or "external publish outcome unknown"})
    else:
        raise ValueError("outcome must be published|failed|ambiguous")
    attempt["outcome"] = outcome
    store.log_event(rec, f"external_{outcome}", urn=urn, detail=error)
    persist(rec, f"{rec['post_id']}: external publish {outcome}")
    return {"result": rec["publish_status"], "url": rec["linkedin"].get("url")}
