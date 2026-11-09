"""CLI: python -m engine <command> ...   (run from the repo root)"""
from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys
from collections import Counter
from datetime import date, datetime, timedelta

from . import approval, gitsync, publisher, quality, schedule, store
from .config import CATEGORY_BY_WEEKDAY, POSTS_DIR, load_settings, now_ist, save_settings
from .linkedin import Client

PILLARS = ["thyroid_hashimotos", "pcos_insulin", "perimenopause", "gut", "iron_b12_vitd",
           "strength_fatloss", "sleep_stress", "mental_emotional", "self_advocacy", "founder_life"]


def _date(s: str) -> date:
    if s == "today":
        return now_ist().date()
    if s == "tomorrow":
        return now_ist().date() + timedelta(days=1)
    if s == "next":
        return schedule.next_publish_day(now_ist().date(), load_settings())
    return date.fromisoformat(s)


def _git_persist(enabled: bool):
    def persist(rec: dict, msg: str) -> None:
        p = store.save(rec)
        if enabled:
            gitsync.commit_and_push(msg, [str(p.relative_to(p.parents[2]))])
    return persist


def _print(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def cmd_new(a):
    s = load_settings()
    d = _date(a.date)
    if not schedule.is_publish_day(d, s):
        sys.exit(f"{d} is not a publishing day")
    if store.load(schedule.post_id_for(d)):
        sys.exit(f"record for {d} already exists (duplicate prevention); edit it instead")
    rec = store.new_record(d, s)
    print(store.save(rec))


def cmd_check(a):
    s = load_settings()
    rec = store.load(schedule.post_id_for(_date(a.date))) or sys.exit("no record")
    issues = quality.check(rec, s, store.all_records())
    ok = quality.passed(issues)
    rec["quality"] = {"passed": ok, "issues": issues, "checked_at": now_ist().isoformat(timespec="seconds")}
    rec["hook"] = quality.first_line(rec.get("final") or "")
    if ok and rec["approval_status"] == "draft":
        rec["approval_status"] = "pending"
        store.log_event(rec, "ready_for_approval")
    store.save(rec)
    _print({"passed": ok, "issues": issues, "approval_status": rec["approval_status"]})
    sys.exit(0 if ok else 1)


def cmd_email_body(a):
    rec = store.load(schedule.post_id_for(_date(a.date))) or sys.exit("no record")
    s = load_settings()
    lines = [
        f"LinkedIn post for {rec['weekday']} {rec['date']}, 08:00 IST",
        f"Category: {rec['category']}   Pillar: {rec['pillar']}   Topic: {rec['topic']}",
        "",
        "Reply with ONE of these as the first line:",
        "  APPROVE                (publish as written)",
        "  APPROVE WITH EDIT      (then paste your full edited post below; published as you wrote it)",
        "  EDIT                   (then paste the full post or describe changes; I'll revise and re-send)",
        "  SKIP                   (no post in this slot)",
        f"If it isn't approved by {s['publish_deadline']} IST it will be skipped automatically.",
        "", "=" * 60, "", rec["final"], "", "=" * 60, "",
    ]
    if rec.get("image_path"):
        lines.append(f"Image: {rec['image_path']}")
        if rec.get("drive_file_id"):
            lines.append(f"  Google Drive: https://drive.google.com/file/d/{rec['drive_file_id']}/view")
        lines.append(f"  GitHub: https://github.com/pearlshweta4u-svg/linkedin-content-engine/blob/main/{rec['image_path']}")
        lines.append(f"  Alt text: {rec.get('image_alt')}")
    if rec.get("story_ids"):
        lines.append("Story/case refs: " + ", ".join(rec["story_ids"]))
    if rec.get("sources"):
        lines.append("Sources:")
        lines += [f"  - {x.get('title')}: {x.get('url')}" for x in rec["sources"]]
    if rec.get("questions_for_shweta"):
        lines.append("Please check:")
        lines += [f"  - {q}" for q in rec["questions_for_shweta"]]
    warns = [i for i in rec["quality"].get("issues", []) if i.startswith("WARN")]
    if warns:
        lines.append("Quality notes: " + "; ".join(warns))
    lines.append(f"\nPost ID: {rec['post_id']}")
    print("\n".join(lines))


def cmd_mark(a):
    rec = store.load(schedule.post_id_for(_date(a.date))) or sys.exit("no record")
    ts = now_ist().isoformat(timespec="seconds")
    if a.what == "approval-requested":
        rec["approval"]["requested_at"] = ts
    elif a.what == "reminded":
        rec["approval"]["reminder_sent_at"] = ts
    store.log_event(rec, a.what)
    _git_persist(a.git)(rec, f"{rec['post_id']}: {a.what}")
    print("ok")


def cmd_decide(a):
    rec = store.load(schedule.post_id_for(_date(a.date))) or sys.exit("no record")
    body = open(a.reply_file, encoding="utf-8").read() if a.reply_file else sys.stdin.read()
    res = approval.parse_reply(body)
    ts = now_ist().isoformat(timespec="seconds")
    if rec["publish_status"] == "published":
        res["applied"] = False
        res["note"] = "already published; decision ignored"
        _print(res)
        return
    if res["decision"] == "approve":
        if res["text"]:
            rec["final"] = res["text"]
            store.log_event(rec, "replaced_by_shweta")
        rec["approval_status"] = "approved"
        rec["approval"].update(decided_at=ts, decided_by=a.by, channel="email", note=res["note"])
        if rec["publish_status"] == "failed":
            pass  # retry allowed in window
        else:
            rec["publish_status"] = "not_ready"
    elif res["decision"] == "skip":
        rec["approval_status"] = "skipped"
        rec["publish_status"] = "skipped"
        rec["approval"].update(decided_at=ts, decided_by=a.by, channel="email", note=res["note"])
    elif res["decision"] == "edit":
        rec["final"] = res["text"]
        rec["approval_status"] = "draft"   # must be re-humanized lightly, re-checked, re-approved
        rec["humanizer"]["applied"] = False
    store.log_event(rec, f"decision_{res['decision']}", by=a.by)
    _git_persist(a.git)(rec, f"{rec['post_id']}: {res['decision']}")
    res["applied"] = res["decision"] != "unclear"
    _print(res)


def cmd_publish(a):
    s = load_settings()
    d = _date(a.date)
    now = datetime.fromisoformat(a.now) if a.now else now_ist()
    if a.git and not a.dry_run:
        gitsync.pull()
    res = publisher.run(d, now, s, dry_run=a.dry_run, persist=_git_persist(a.git and not a.dry_run),
                        external=(a.via == "composio"))
    warn = publisher.token_warning(s, now.date()) if (a.via == "api" and s.get("publisher", "api") == "api") else None
    if warn:
        res["token_warning"] = warn
    _print(res)
    sys.exit(0 if res["result"] in ("published", "already_published", "dry_run_ok", "too_early", "ready_external",
                                    "awaiting_approval", "weekend", "paused", "skipped") else 2)


def cmd_record(a):
    res = publisher.record_outcome(_date(a.date), now_ist(), a.outcome, urn=a.urn, error=a.error,
                                   persist=_git_persist(a.git))
    _print(res)


def cmd_resolve(a):
    rec = store.load(schedule.post_id_for(_date(a.date))) or sys.exit("no record")
    if a.url:
        urn = a.url.rstrip("/").split("/")[-1]
        rec["linkedin"].update(urn=urn, url=a.url)
        rec["publish_status"] = "published"
        rec["published_at"] = rec["published_at"] or now_ist().isoformat(timespec="seconds")
        store.log_event(rec, "manually_marked_published", url=a.url)
    else:
        if rec["linkedin"].get("urn"):
            sys.exit("record has a LinkedIn URN; refusing to reset (it was published)")
        rec["publish_status"] = "failed"
        store.log_event(rec, "publish_lock_reset_after_manual_check")
    _git_persist(a.git)(rec, f"{rec['post_id']}: manual resolve")
    print(rec["publish_status"])


def cmd_mode(a):
    s = load_settings()
    if a.mode == "auto" and a.confirmation != "SHWETA-CONFIRMED-AUTO":
        sys.exit("Automatic publishing needs Shweta's explicit confirmation: "
                 "--confirmation SHWETA-CONFIRMED-AUTO")
    if a.mode in ("approval", "auto"):
        s["mode"] = a.mode
    elif a.mode == "pause":
        s["paused"] = True
    elif a.mode == "resume":
        s["paused"] = False
    save_settings(s)
    if a.git:
        gitsync.commit_and_push(f"settings: {a.mode}", ["config/settings.json"])
    print(f"mode={s['mode']} paused={s['paused']}")


def cmd_whoami(a):
    s = load_settings()
    info = Client(s["linkedin"]["api_version"]).userinfo()
    urn = f"urn:li:person:{info['sub']}"
    _print({"name": info.get("name"), "person_urn": urn})
    if a.save:
        s["linkedin"]["person_urn"] = urn
        save_settings(s)


def cmd_status(a):
    recs = store.all_records()
    if a.last:
        recs = recs[-a.last:]
    for r in recs:
        print(f"{r['post_id']:<16} {r['category']:<16} appr={r['approval_status']:<9} "
              f"pub={r['publish_status']:<11} {(r['linkedin'] or {}).get('url') or ''}  {r['topic'][:50]}")


def cmd_history(a):
    """Content index for the generator: what's been used and what's missing."""
    s = load_settings()
    recs = [r for r in store.all_records() if r["approval_status"] in ("approved", "pending")
            or r["publish_status"] == "published"]
    recs.sort(key=lambda r: r["date"])
    today = now_ist().date()
    q = s["quality"]
    pillar_counts = Counter(r.get("pillar") for r in recs if date.fromisoformat(r["date"]) >= today - timedelta(days=28))
    out = {
        "recent_hooks": [{"post_id": r["post_id"], "hook": r.get("hook") or quality.first_line(r.get("final", "")),
                          "shape": quality.hook_shape(r.get("final", ""))} for r in recs[-q["hook_lookback_posts"]:]],
        "stories_on_cooldown": sorted({sid for r in recs for sid in r.get("story_ids", [])
                                       if date.fromisoformat(r["date"]) >= today - timedelta(days=q["story_cooldown_days"])}),
        "topics_on_cooldown": [r["topic"] for r in recs
                               if date.fromisoformat(r["date"]) >= today - timedelta(days=q["topic_cooldown_days"])],
        "pillars_last_5": [r.get("pillar") for r in recs[-5:]],
        "pillars_missing_last_28d": [p for p in PILLARS[:9] if pillar_counts.get(p, 0) == 0],
        "formats_last_8": [r.get("format") for r in recs[-8:]],
    }
    con = store.build_index()
    rows = con.execute("SELECT category, COUNT(*), AVG(impressions), AVG(reactions), AVG(comments) "
                       "FROM posts WHERE publish_status='published' GROUP BY category").fetchall()
    out["performance_by_category"] = [dict(zip(["category", "posts", "avg_impr", "avg_react", "avg_comments"], r)) for r in rows]
    _print(out)


def cmd_image(a):
    from . import images
    rec = store.load(schedule.post_id_for(_date(a.date))) or sys.exit("no record")
    if not rec.get("image_spec"):
        sys.exit("record has no image_spec")
    try:
        path = images.render(rec)
    except images.ImageError as e:
        _print({"ok": False, "error": str(e)})
        sys.exit(1)
    rec["image_path"] = path
    rec["image_alt"] = rec["image_spec"]["alt"]
    store.log_event(rec, "image_rendered", path=path)
    _git_persist(a.git)(rec, f"{rec['post_id']}: image")
    if a.git:
        gitsync.commit_and_push(f"{rec['post_id']}: image file", [path])
    _print({"ok": True, "image_path": path})


def cmd_image_url(a):
    """Upload the post image to Zernio media storage and print a public HTTPS URL
    (used to copy images into Google Drive; the URL is saved on the record)."""
    from . import zernio
    from .config import ROOT
    rec = store.load(schedule.post_id_for(_date(a.date))) or sys.exit("no record")
    if not rec.get("image_path"):
        sys.exit("record has no image_path; run `engine image` first")
    if rec.get("image_public_url") and not a.force:
        _print({"post_id": rec["post_id"], "url": rec["image_public_url"], "name": Path(rec["image_path"]).name})
        return
    path = ROOT / rec["image_path"]
    url = zernio.Client().upload_image("", path.read_bytes(), zernio.guess_type(str(path)), path.name)
    rec["image_public_url"] = url
    store.log_event(rec, "image_public_url", url=url)
    _git_persist(a.git)(rec, f"{rec['post_id']}: image public url")
    _print({"post_id": rec["post_id"], "url": url, "name": path.name})


def cmd_validate(a):
    """Verification test: Zernio dry-run of text + image (nothing is published)."""
    from . import zernio
    from .config import ROOT
    s = load_settings()
    acct = (s.get("zernio") or {}).get("account_id")
    rec = store.load(schedule.post_id_for(_date(a.date))) or sys.exit("no record")
    c = zernio.Client()
    url = None
    if rec.get("image_path"):
        path = ROOT / rec["image_path"]
        url = c.upload_image("", path.read_bytes(), zernio.guess_type(str(path)), path.name)
        rec["image_public_url"] = url
    res = c.validate_post(acct, rec["final"], url)
    media = c.validate_media(url) if url else None
    ok = res["valid"] and (media is None or media.get("valid", False))
    rec["zernio_validation"] = {"valid": ok, "post_errors": res["errors"], "post_warnings": res["warnings"],
                                "media": {k: (media or {}).get(k) for k in ("valid", "format", "width", "height", "size", "code")},
                                "checked_at": now_ist().isoformat(timespec="seconds"),
                                "text_sha": __import__("hashlib").sha256(rec["final"].encode()).hexdigest()[:16],
                                "image_path": rec.get("image_path")}
    store.log_event(rec, "zernio_validated", detail="ok" if ok else "FAILED")
    _git_persist(a.git)(rec, f"{rec['post_id']}: zernio validation {'ok' if ok else 'FAILED'}")
    _print(rec["zernio_validation"])
    sys.exit(0 if ok else 1)


def cmd_import_history(a):
    from . import history_import
    _print(history_import.import_export(Path(a.source), download=not a.no_download))


def cmd_mark_drive(a):
    rec = store.load(schedule.post_id_for(_date(a.date))) or sys.exit("no record")
    rec["drive_file_id"] = a.file_id
    store.log_event(rec, "copied_to_drive", file_id=a.file_id)
    _git_persist(a.git)(rec, f"{rec['post_id']}: copied to Drive")
    print("ok")


def cmd_fetch_analytics(a):
    """Pull impressions/reactions/comments/etc. for recently published posts via Zernio."""
    from . import zernio
    s = load_settings()
    acct = (s.get("zernio") or {}).get("account_id")
    if not acct:
        sys.exit("zernio.account_id not set")
    client = zernio.Client()
    since = now_ist().date() - timedelta(days=a.days)
    out = []
    for rec in store.all_records():
        urn = (rec.get("linkedin") or {}).get("urn")
        if rec["publish_status"] != "published" or not urn or date.fromisoformat(rec["date"]) < since:
            continue
        try:
            m = client.post_analytics(acct, urn)
        except Exception as e:  # keep going; one bad post shouldn't stop the rest
            out.append({"post_id": rec["post_id"], "error": str(e)})
            continue
        rec["analytics"].update({k: m.get(k) for k in ("impressions", "reach", "likes", "comments", "shares",
                                                       "saves", "sends", "engagementRate")})
        rec["analytics"]["reactions"] = m.get("likes")
        rec["analytics"]["reposts"] = m.get("shares")
        rec["analytics"]["updated_at"] = now_ist().isoformat(timespec="seconds")
        store.save(rec)
        out.append({"post_id": rec["post_id"], **rec["analytics"]})
    if a.git and out:
        gitsync.commit_and_push("analytics refresh", ["content/posts"])
    _print(out)


def cmd_analytics(a):
    rec = store.load(schedule.post_id_for(_date(a.date))) or sys.exit("no record")
    for k in ("impressions", "reactions", "comments", "reposts"):
        v = getattr(a, k)
        if v is not None:
            rec["analytics"][k] = v
    a_ = rec["analytics"]
    if a_.get("impressions"):
        eng = sum(a_.get(k, 0) or 0 for k in ("reactions", "comments", "reposts"))
        a_["engagement_rate"] = round(eng / a_["impressions"], 4)
    a_["updated_at"] = now_ist().isoformat(timespec="seconds")
    _git_persist(a.git)(rec, f"{rec['post_id']}: analytics")
    _print(a_)


def main(argv=None):
    p = argparse.ArgumentParser(prog="engine")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = lambda sp: sp.add_argument("--git", action="store_true", help="commit+push the change")

    sp = sub.add_parser("new"); sp.add_argument("date"); sp.set_defaults(f=cmd_new)
    sp = sub.add_parser("check"); sp.add_argument("date"); sp.set_defaults(f=cmd_check)
    sp = sub.add_parser("email-body"); sp.add_argument("date"); sp.set_defaults(f=cmd_email_body)
    sp = sub.add_parser("mark"); sp.add_argument("date"); sp.add_argument("what", choices=["approval-requested", "reminded"]); g(sp); sp.set_defaults(f=cmd_mark)
    sp = sub.add_parser("decide"); sp.add_argument("date"); sp.add_argument("--reply-file"); sp.add_argument("--by", default="shweta"); g(sp); sp.set_defaults(f=cmd_decide)
    sp = sub.add_parser("publish"); sp.add_argument("date"); sp.add_argument("--dry-run", action="store_true"); sp.add_argument("--now"); sp.add_argument("--via", choices=["api", "composio"], default="api"); g(sp); sp.set_defaults(f=cmd_publish)
    sp = sub.add_parser("record"); sp.add_argument("date"); sp.add_argument("outcome", choices=["published", "failed", "ambiguous"]); sp.add_argument("--urn"); sp.add_argument("--error"); g(sp); sp.set_defaults(f=cmd_record)
    sp = sub.add_parser("mark-published"); sp.add_argument("date"); sp.add_argument("--url", required=True); g(sp); sp.set_defaults(f=cmd_resolve)
    sp = sub.add_parser("reset-publish"); sp.add_argument("date"); sp.set_defaults(url=None); g(sp); sp.set_defaults(f=cmd_resolve)
    sp = sub.add_parser("mode"); sp.add_argument("mode", choices=["approval", "auto", "pause", "resume"]); sp.add_argument("--confirmation"); g(sp); sp.set_defaults(f=cmd_mode)
    sp = sub.add_parser("whoami"); sp.add_argument("--save", action="store_true"); sp.set_defaults(f=cmd_whoami)
    sp = sub.add_parser("status"); sp.add_argument("--last", type=int); sp.set_defaults(f=cmd_status)
    sp = sub.add_parser("history"); sp.set_defaults(f=cmd_history)
    sp = sub.add_parser("analytics"); sp.add_argument("date")
    for k in ("impressions", "reactions", "comments", "reposts"):
        sp.add_argument(f"--{k}", type=int)
    g(sp); sp.set_defaults(f=cmd_analytics)
    sp = sub.add_parser("image"); sp.add_argument("date"); g(sp); sp.set_defaults(f=cmd_image)
    sp = sub.add_parser("image-url"); sp.add_argument("date"); sp.add_argument("--force", action="store_true"); g(sp); sp.set_defaults(f=cmd_image_url)
    sp = sub.add_parser("validate"); sp.add_argument("date"); g(sp); sp.set_defaults(f=cmd_validate)
    sp = sub.add_parser("import-history"); sp.add_argument("source", help="LinkedIn data-export ZIP or folder"); sp.add_argument("--no-download", action="store_true"); sp.set_defaults(f=cmd_import_history)
    sp = sub.add_parser("mark-drive"); sp.add_argument("date"); sp.add_argument("file_id"); g(sp); sp.set_defaults(f=cmd_mark_drive)
    sp = sub.add_parser("fetch-analytics"); sp.add_argument("--days", type=int, default=30); g(sp); sp.set_defaults(f=cmd_fetch_analytics)
    sp = sub.add_parser("next-slot"); sp.set_defaults(f=lambda a: print(schedule.next_publish_day(now_ist().date(), load_settings())))
    a = p.parse_args(argv)
    a.f(a)


if __name__ == "__main__":
    main()
