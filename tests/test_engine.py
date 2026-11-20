import io
import json
import tempfile
import unittest
import urllib.error
from datetime import date, datetime
from pathlib import Path

from engine import approval, publisher, quality, schedule, store
from engine.config import IST, load_settings
from engine.linkedin import Client, LinkedInError, escape_commentary

MON = date(2026, 11, 16)
GOOD_TEXT = (
    "Last month a client told me her reports were normal and she still felt awful every afternoon.\n\n"
    + "We looked at ferritin first because her TSH alone was not telling the whole story. " * 6
    + "\n\nWhat would you ask your doctor first?"
)


def settings(**over):
    s = load_settings()
    s["linkedin"]["person_urn"] = "urn:li:person:abc"
    s["linkedin"]["token_issued_on"] = "2026-11-01"
    s["publisher"] = "api"  # tests choose their backend explicitly
    s.update(over)
    return s


def at(d, hh, mm=0):
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=IST)


def make(tmp, d=MON, **fields):
    s = settings()
    r = store.new_record(d, s)
    r.update(final=GOOD_TEXT, draft=GOOD_TEXT, topic="normal reports", pillar="self_advocacy", category="educational",
             hook_style="relatable_moment")
    r["humanizer"]["applied"] = True
    r.update(fields)
    store.save(r, tmp)
    return r


class FakeClient:
    def __init__(self, error=None):
        self.calls = 0
        self.error = error

    def create_post(self, author, text, image_urn=None, alt=None):
        self.calls += 1
        if self.error:
            raise self.error
        return "urn:li:share:123"

    def upload_image(self, *a):
        return "urn:li:image:1"


class TestSchedule(unittest.TestCase):
    def test_categories_and_weekend(self):
        s = settings()
        self.assertEqual(schedule.category_for(date(2026, 11, 10)), "client_story")
        self.assertEqual(schedule.category_for(date(2026, 11, 13)), "health_wellness")
        self.assertFalse(schedule.is_publish_day(date(2026, 11, 14), s))
        self.assertEqual(schedule.next_publish_day(date(2026, 11, 13), s), MON)
        with self.assertRaises(ValueError):
            schedule.category_for(date(2026, 11, 15))

    def test_slot_is_0800_ist(self):
        self.assertEqual(schedule.slot_datetime(MON, settings()).isoformat(), "2026-11-16T08:00:00+05:30")

    def test_window(self):
        s = settings()
        self.assertEqual(schedule.window_state(MON, at(MON, 7, 59), s), "early")
        self.assertEqual(schedule.window_state(MON, at(MON, 8), s), "open")
        self.assertEqual(schedule.window_state(MON, at(MON, 12, 1), s), "closed")


class TestQuality(unittest.TestCase):
    def rec(self, text, **kw):
        r = store.new_record(MON, settings())
        r["final"] = text
        r["humanizer"]["applied"] = True
        r["category"] = "educational"
        r["hook_style"] = "relatable_moment"
        r.update(kw)
        return r

    def test_good_passes(self):
        self.assertTrue(quality.passed(quality.check(self.rec(GOOD_TEXT), settings())))

    def test_blocks(self):
        s = settings()
        cases = {
            "em dash": GOOD_TEXT + " This — that.",
            "banned phrase": GOOD_TEXT + " Let's delve in.",
            "medical": GOOD_TEXT + " This will cure your thyroid.",
            "dose": GOOD_TEXT + " Take 60000 IU weekly.",
            "detox": GOOD_TEXT + " Try this detox.",
            "miracle": GOOD_TEXT + " A miracle drink.",
            "hashtags": GOOD_TEXT + " #a #b #c #d",
        }
        for name, text in cases.items():
            with self.subTest(name):
                self.assertFalse(quality.passed(quality.check(self.rec(text), s)))

    def test_lab_units_are_not_doses(self):
        r = self.rec(GOOD_TEXT + " Fasting glucose of 100 to 125 mg/dL is prediabetes.")
        self.assertTrue(quality.passed(quality.check(r, settings())))
        r = self.rec(GOOD_TEXT + " Take 500 mg daily.")
        self.assertFalse(quality.passed(quality.check(r, settings())))

    def test_negated_medical_phrase_ok(self):
        r = self.rec(GOOD_TEXT + " She was optimal on dose, not cured.")
        self.assertTrue(quality.passed(quality.check(r, settings())))

    def test_story_posts_need_structure_and_plain_language(self):
        s = settings()
        r = self.rec(GOOD_TEXT, category="client_story")
        self.assertIn("STAR", " ".join(quality.check(r, s)))
        r["story_structure"] = {k: "x" for k in ["situation", "task", "action", "result", "lesson"]}
        self.assertTrue(quality.passed(quality.check(r, s)))
        r["final"] = GOOD_TEXT + " TSH, ferritin, B12, selenium, ashwagandha and cortisol."
        self.assertIn("too clinical", " ".join(quality.check(r, s)))
        p = self.rec(GOOD_TEXT, category="personal_story")
        self.assertIn("story_arc", " ".join(quality.check(p, s)))

    def test_hook_rules(self):
        s = settings()
        weak = self.rec("Tomorrow is a big day for all of us.\n\n" + GOOD_TEXT)
        self.assertIn("generic opener", " ".join(quality.check(weak, s)))
        long_hook = self.rec("word " * 50 + "\n\n" + GOOD_TEXT)
        self.assertFalse(quality.passed(quality.check(long_hook, s)))
        no_style = self.rec(GOOD_TEXT, hook_style="")
        self.assertIn("hook_style", " ".join(quality.check(no_style, s)))

    def test_humanizer_mandatory(self):
        r = self.rec(GOOD_TEXT)
        r["humanizer"]["applied"] = False
        self.assertIn("Humanizer", " ".join(quality.check(r, settings())))

    def test_research_days_need_sources(self):
        r = self.rec(GOOD_TEXT, category="health_wellness")
        self.assertFalse(quality.passed(quality.check(r, settings())))
        r["sources"] = [{"title": "NIH", "url": "https://ods.od.nih.gov/"}]
        self.assertTrue(quality.passed(quality.check(r, settings())))

    def test_story_and_hook_repetition(self):
        old = store.new_record(date(2026, 11, 9 + 1), settings())
        old.update(final=GOOD_TEXT, story_ids=["P02"], approval_status="approved", topic="x")
        r = self.rec(GOOD_TEXT, story_ids=["P02"])
        issues = quality.check(r, settings(), [old])
        self.assertTrue(any("story" in i for i in issues))
        self.assertTrue(any("identical hook" in i for i in issues))


class TestApproval(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(approval.parse_reply("Approve\n\nOn Mon, X wrote:\n> old")["decision"], "approve")
        self.assertEqual(approval.parse_reply("ok")["decision"], "approve")
        self.assertEqual(approval.parse_reply("SKIP.")["decision"], "skip")
        self.assertEqual(approval.parse_reply("Looks nice but change line 2")["decision"], "unclear")
        long = "word " * 30
        r = approval.parse_reply("APPROVE WITH EDIT\n" + long)
        self.assertEqual((r["decision"], r["text"]), ("approve", long.strip()))
        self.assertEqual(approval.parse_reply("EDIT\n" + long)["decision"], "edit")
        self.assertEqual(approval.parse_reply("EDIT\nshorter please")["decision"], "unclear")
        self.assertEqual(approval.parse_reply("")["decision"], "unclear")


class TestEscaping(unittest.TestCase):
    def test_reserved_and_hashtags(self):
        out = escape_commentary("TSH (thyroid) 50% #Hashimotos *bold* email@x")
        self.assertEqual(out, "TSH \\(thyroid\\) 50% {hashtag|\\#|Hashimotos} \\*bold\\* email\\@x")


class TestPublisher(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def run_pub(self, now, client=None, s=None, **kw):
        return publisher.run(MON, now, s or settings(), client=client or FakeClient(), posts_dir=self.tmp, **kw)

    def test_requires_approval(self):
        make(self.tmp, approval_status="pending")
        c = FakeClient()
        self.assertEqual(self.run_pub(at(MON, 8), c)["result"], "awaiting_approval")
        self.assertEqual(c.calls, 0)

    def test_publishes_once(self):
        make(self.tmp, approval_status="approved")
        c = FakeClient()
        r = self.run_pub(at(MON, 8, 1), c)
        self.assertEqual(r["result"], "published")
        self.assertEqual(r["url"], "https://www.linkedin.com/feed/update/urn:li:share:123/")
        self.assertEqual(self.run_pub(at(MON, 9), c)["result"], "already_published")
        self.assertEqual(c.calls, 1)

    def test_too_early_and_expiry(self):
        make(self.tmp, approval_status="pending")
        self.assertEqual(self.run_pub(at(MON, 7, 30))["result"], "too_early")
        self.assertEqual(self.run_pub(at(MON, 12, 30))["result"], "expired")
        self.assertEqual(store.load(schedule.post_id_for(MON), self.tmp)["publish_status"], "expired")

    def test_late_approval_inside_window_publishes(self):
        make(self.tmp, approval_status="approved")
        self.assertEqual(self.run_pub(at(MON, 11, 0))["result"], "published")

    def test_ambiguous_error_never_retried(self):
        make(self.tmp, approval_status="approved")
        c = FakeClient(LinkedInError("timeout", None, ambiguous=True))
        self.assertEqual(self.run_pub(at(MON, 8), c)["result"], "needs_check")
        c.error = None
        self.assertEqual(self.run_pub(at(MON, 9), c)["result"], "needs_check")
        self.assertEqual(c.calls, 1)

    def test_safe_failure_retries_next_run(self):
        make(self.tmp, approval_status="approved")
        c = FakeClient(LinkedInError("HTTP 429", 429))
        self.assertEqual(self.run_pub(at(MON, 8), c)["result"], "failed")
        c.error = None
        self.assertEqual(self.run_pub(at(MON, 9), c)["result"], "published")

    def test_crash_mid_publish_becomes_needs_check(self):
        make(self.tmp, approval_status="approved", publish_status="publishing")
        c = FakeClient()
        self.assertEqual(self.run_pub(at(MON, 9), c)["result"], "needs_check")
        self.assertEqual(c.calls, 0)

    def test_auth_failure(self):
        make(self.tmp, approval_status="approved")
        r = self.run_pub(at(MON, 8), FakeClient(LinkedInError("auth", 401)))
        self.assertEqual(r["result"], "auth_failed")

    def test_paused_weekend_dryrun_missing(self):
        self.assertEqual(self.run_pub(at(MON, 8))["result"], "missing")
        make(self.tmp, approval_status="approved")
        self.assertEqual(self.run_pub(at(MON, 8), s=settings(paused=True))["result"], "paused")
        c = FakeClient()
        self.assertEqual(self.run_pub(at(MON, 8), c, dry_run=True)["result"], "dry_run_ok")
        self.assertEqual(c.calls, 0)
        sat = date(2026, 11, 14)
        self.assertEqual(publisher.run(sat, at(sat, 8), settings(), posts_dir=self.tmp)["result"], "weekend")

    def test_auto_mode_approves_only_passing_pending(self):
        make(self.tmp, approval_status="pending")
        self.assertEqual(self.run_pub(at(MON, 8), s=settings(mode="auto"))["result"], "published")

    def test_auto_mode_does_not_publish_draft(self):
        make(self.tmp, approval_status="draft")
        self.assertEqual(self.run_pub(at(MON, 8), s=settings(mode="auto"))["result"], "awaiting_approval")

    def test_lock_persisted_before_api_call(self):
        make(self.tmp, approval_status="approved")
        seen = []
        persist = lambda rec, msg: (seen.append(rec["publish_status"]), store.save(rec, self.tmp))
        self.run_pub(at(MON, 8), persist=persist)
        self.assertEqual(seen, ["publishing", "published"])

    def test_lock_failure_stops_publish(self):
        make(self.tmp, approval_status="approved")
        c = FakeClient()

        def persist(rec, msg):
            raise RuntimeError("push rejected")
        with self.assertRaises(RuntimeError):
            self.run_pub(at(MON, 8), c, persist=persist)
        self.assertEqual(c.calls, 0)


class TestExternalPublish(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_two_phase_and_no_double_publish(self):
        make(self.tmp, approval_status="approved")
        s = settings()
        r = publisher.run(MON, at(MON, 8), s, posts_dir=self.tmp, external=True)
        self.assertEqual(r["result"], "ready_external")
        self.assertEqual(r["commentary"], GOOD_TEXT)
        # a second run while the lock is held must not hand out the text again
        self.assertEqual(publisher.run(MON, at(MON, 9), s, posts_dir=self.tmp, external=True)["result"], "needs_check")

    def test_record_published(self):
        make(self.tmp, approval_status="approved")
        publisher.run(MON, at(MON, 8), settings(), posts_dir=self.tmp, external=True)
        out = publisher.record_outcome(MON, at(MON, 8, 1), "published", urn="urn:li:share:7", posts_dir=self.tmp)
        self.assertEqual(out["result"], "published")
        self.assertEqual(publisher.run(MON, at(MON, 9), settings(), posts_dir=self.tmp, external=True)["result"], "already_published")

    def test_record_failed_allows_retry(self):
        make(self.tmp, approval_status="approved")
        publisher.run(MON, at(MON, 8), settings(), posts_dir=self.tmp, external=True)
        publisher.record_outcome(MON, at(MON, 8, 1), "failed", error="429", posts_dir=self.tmp)
        self.assertEqual(publisher.run(MON, at(MON, 9), settings(), posts_dir=self.tmp, external=True)["result"], "ready_external")


def validated(rec_fields, final=GOOD_TEXT, image_path=None):
    import hashlib
    rec_fields["zernio_validation"] = {"valid": True, "text_sha": hashlib.sha256(final.encode()).hexdigest()[:16],
                                       "image_path": image_path}
    return rec_fields


class FakeZernio:
    idempotent_create = True

    def __init__(self, error=None):
        self.calls, self.keys, self.error, self.uploads = 0, [], error, 0

    def upload_image(self, owner, data, ctype, name):
        self.uploads += 1
        return "https://media.zernio.com/x.png"

    def create_post(self, acct, text, image_url=None, alt=None, idempotency_key=None):
        self.calls += 1
        self.keys.append(idempotency_key)
        if self.error:
            raise self.error
        return "urn:li:share:55", "https://www.linkedin.com/feed/update/urn:li:share:55/"


class TestZernioBackend(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.s = settings(publisher="zernio", zernio={"account_id": "acc1"})

    def test_publish_once_with_stable_key(self):
        make(self.tmp, **validated({"approval_status": "approved"}))
        z = FakeZernio(LinkedInError("timeout", None, ambiguous=True))
        self.assertEqual(publisher.run(MON, at(MON, 8), self.s, client=z, posts_dir=self.tmp)["result"], "failed")
        z.error = None
        r = publisher.run(MON, at(MON, 9), self.s, client=z, posts_dir=self.tmp)
        self.assertEqual(r["result"], "published")
        self.assertEqual(len(set(z.keys)), 1)  # same idempotency key on the retry
        self.assertEqual(publisher.run(MON, at(MON, 10), self.s, client=z, posts_dir=self.tmp)["result"], "already_published")
        self.assertEqual(z.calls, 2)

    def test_stale_lock_resumes_safely(self):
        make(self.tmp, **validated({"approval_status": "approved", "publish_status": "publishing"}))
        z = FakeZernio()
        self.assertEqual(publisher.run(MON, at(MON, 9), self.s, client=z, posts_dir=self.tmp)["result"], "published")

    def test_image_uploaded_when_enabled(self):
        img = self.tmp / "img.png"
        img.write_bytes(b"png")
        make(self.tmp, **validated({"approval_status": "approved", "image_path": str(img)}, image_path=str(img)))
        z = FakeZernio()
        s = dict(self.s, images_enabled=True)
        publisher.run(MON, at(MON, 8), s, client=z, posts_dir=self.tmp)
        self.assertEqual(z.uploads, 1)

    def test_validation_required_and_stale(self):
        make(self.tmp, approval_status="approved")
        z = FakeZernio()
        self.assertEqual(publisher.run(MON, at(MON, 8), self.s, client=z, posts_dir=self.tmp)["result"], "validation_required")
        r = store.load(schedule.post_id_for(MON), self.tmp)
        validated(r, final="old text")  # validated a different text -> stale
        store.save(r, self.tmp)
        self.assertEqual(publisher.run(MON, at(MON, 8), self.s, client=z, posts_dir=self.tmp)["result"], "validation_required")
        self.assertEqual(z.calls, 0)

    def test_missing_account_id(self):
        make(self.tmp, approval_status="approved")
        s = settings(publisher="zernio", zernio={})
        self.assertEqual(publisher.run(MON, at(MON, 8), s, client=FakeZernio(), posts_dir=self.tmp)["result"], "config_missing")


class TestZernioClient(unittest.TestCase):
    def test_create_post_request_and_parse(self):
        from engine import zernio
        seen = {}

        def opener(req, timeout):
            seen["url"], seen["headers"], seen["body"] = req.full_url, dict(req.header_items()), json.loads(req.data)
            body = {"post": {"_id": "p1", "status": "published", "platforms": [
                {"platform": "linkedin", "status": "published", "platformPostId": "urn:li:share:9",
                 "platformPostUrl": "https://www.linkedin.com/feed/update/urn:li:share:9/"}]}}
            return _Resp(201, {}, json.dumps(body).encode())
        c = zernio.Client(key="k", opener=opener, sleep=lambda s: None)
        pid, url = c.create_post("acc1", "Hi (x) #Tag", "https://m/x.png", "alt", idempotency_key="key-1")
        self.assertEqual(pid, "urn:li:share:9")
        self.assertEqual(seen["url"], "https://zernio.com/api/v1/posts")
        self.assertEqual(seen["headers"]["Idempotency-key"], "key-1")
        self.assertEqual(seen["body"]["content"], "Hi (x) #Tag")  # raw text: Zernio formats for LinkedIn
        self.assertTrue(seen["body"]["publishNow"])
        self.assertEqual(seen["body"]["mediaItems"][0]["url"], "https://m/x.png")
        self.assertEqual(seen["body"]["platforms"], [{"platform": "linkedin", "accountId": "acc1"}])

    def test_failed_auth_category(self):
        from engine import zernio
        body = {"post": {"status": "failed", "platforms": [{"platform": "linkedin", "status": "failed",
                 "errorCategory": "auth_expired", "errorMessage": "token expired"}]}}
        c = zernio.Client(key="k", opener=lambda r, timeout: _Resp(201, {}, json.dumps(body).encode()))
        with self.assertRaises(LinkedInError) as cm:
            c.create_post("acc1", "x")
        self.assertEqual(cm.exception.status, 401)

    def test_key_is_stable_per_slot(self):
        from engine import zernio
        self.assertEqual(zernio.idempotency_key("2026-11-10-tue"), zernio.idempotency_key("2026-11-10-tue"))
        self.assertNotEqual(zernio.idempotency_key("2026-11-10-tue"), zernio.idempotency_key("2026-11-11-wed"))


class TestImageSpec(unittest.TestCase):
    def test_validate(self):
        from engine import images
        ok = {"template": "checklist", "title": "T", "items": ["a", "b"], "alt": "x"}
        self.assertEqual(images.validate(ok), [])
        self.assertTrue(images.validate({"template": "nope", "title": "T", "alt": "x"}))
        self.assertTrue(images.validate({"template": "story", "title": "T"}))  # alt required
        self.assertTrue(images.validate({"template": "stat", "title": "T", "alt": "x", "stat": "123456789"}))
        self.assertTrue(images.validate(dict(ok, items=["a"] * 8)))
        self.assertTrue(images.validate(dict(ok, title="x" * 91)))


class TestHistoryImport(unittest.TestCase):
    def test_import_from_export_zip(self):
        import zipfile
        from engine import history_import
        tmp = Path(tempfile.mkdtemp())
        z = tmp / "export.zip"
        shares = ('Date,ShareLink,ShareCommentary,SharedUrl,MediaUrl,Visibility\n'
                  '2025-12-18 09:00:00,https://www.linkedin.com/feed/update/urn:li:share:1,'
                  '"Hook line here\nSecond line",,https://media.licdn.com/x.jpg,MEMBER_NETWORK\n'
                  '2025-11-01 08:00:00,https://www.linkedin.com/feed/update/urn:li:share:2,Text only,,,PUBLIC\n')
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("Basic_LinkedInDataExport/Shares.csv", shares)

        def opener(req, timeout):
            return _Resp(200, {"Content-Type": "image/jpeg"}, b"jpg")
        out = tmp / "history"
        summary = history_import.import_export(z, out_dir=out, opener=opener)
        self.assertEqual((summary["posts"], summary["with_media_links"]), (2, 1))
        data = json.loads((out / "posts.json").read_text())
        self.assertEqual(data["posts"][1]["hook"], "Hook line here")
        self.assertEqual(data["posts"][0]["date"][:10], "2025-11-01")
        self.assertTrue(any(p.suffix == ".jpg" for p in (out / "images").iterdir()))


class TestPhotoTemplate(unittest.TestCase):
    def test_photo_validation(self):
        from engine import images
        base = {"template": "photo", "title": "Normal report. Still exhausted.", "alt": "x"}
        self.assertTrue(any("photo" in e for e in images.validate(dict(base, photo="content/photos/missing.jpg"))))
        self.assertEqual(images.validate(dict(base, photo="content/photos/album-61.jpg")), [])
        self.assertTrue(any("solution" in e for e in images.validate(dict(base, photo="content/photos/album-61.jpg", items=["a"]))))
        wordy = dict(base, photo="content/photos/album-61.jpg", subtitle="here are many many words that explain everything")
        self.assertTrue(images.validate(wordy))
        self.assertTrue(any("not an image" in e for e in images.validate(dict(base, photo="README.md"))))


class TestSceneTemplate(unittest.TestCase):
    def test_scene_validation(self):
        from engine import images
        ok = {"template": "scene", "photo": "content/photos/scenes/pink-sunset-sea.jpg", "title": "It doesn't hurt.", "alt": "x"}
        self.assertEqual(images.validate(ok), [])
        self.assertTrue(images.validate(dict(ok, photo="content/photos/album-61.jpg")))  # must come from scenes/
        self.assertTrue(images.validate(dict(ok, items=["a"])))


class _Resp:
    def __init__(self, status=201, headers=None, body=b""):
        self.status, self.headers, self._b = status, headers or {}, body

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestClientTransport(unittest.TestCase):
    def http_error(self, code):
        return urllib.error.HTTPError("u", code, "x", {}, io.BytesIO(b"{}"))

    def test_create_post_headers_and_urn(self):
        seen = {}

        def opener(req, timeout):
            seen["headers"] = dict(req.header_items())
            seen["body"] = json.loads(req.data)
            return _Resp(201, {"x-restli-id": "urn:li:share:9"})
        c = Client("202606", token="t", opener=opener, sleep=lambda s: None)
        self.assertEqual(c.create_post("urn:li:person:a", "Hi (x)"), "urn:li:share:9")
        self.assertEqual(seen["headers"]["Linkedin-version"], "202606")
        self.assertEqual(seen["body"]["commentary"], "Hi \\(x\\)")
        self.assertEqual(seen["body"]["lifecycleState"], "PUBLISHED")

    def test_429_retried_then_ok(self):
        calls = []

        def opener(req, timeout):
            calls.append(1)
            if len(calls) < 3:
                raise self.http_error(429)
            return _Resp(201, {"X-RestLi-Id": "urn:li:share:1"})  # mixed-case header
        c = Client("202606", token="t", opener=opener, sleep=lambda s: None)
        self.assertEqual(c.create_post("urn:li:person:a", "x"), "urn:li:share:1")
        self.assertEqual(len(calls), 3)

    def test_network_error_on_post_is_ambiguous_and_not_retried(self):
        calls = []

        def opener(req, timeout):
            calls.append(1)
            raise urllib.error.URLError("reset")
        c = Client("202606", token="t", opener=opener, sleep=lambda s: None)
        with self.assertRaises(LinkedInError) as cm:
            c.create_post("urn:li:person:a", "x")
        self.assertTrue(cm.exception.ambiguous)
        self.assertEqual(len(calls), 1)

    def test_401_not_retried(self):
        calls = []

        def opener(req, timeout):
            calls.append(1)
            raise self.http_error(401)
        c = Client("202606", token="t", opener=opener, sleep=lambda s: None)
        with self.assertRaises(LinkedInError) as cm:
            c.create_post("urn:li:person:a", "x")
        self.assertEqual((cm.exception.status, len(calls)), (401, 1))


if __name__ == "__main__":
    unittest.main()


class PreApprovalAlertTests(unittest.TestCase):
    """16 Nov 2026: a failed evening run let an old sample card go out unnoticed."""
    S = {"images_enabled": True, "photos": {"use_for": ["personal_story", "client_story", "educational"]}}

    def rec(self, created, template, category="personal_story", d="2026-11-16"):
        return {"date": d, "category": category, "image_path": "x.png", "image_spec": {"template": template},
                "history": [{"at": created, "event": "created"}, {"at": created, "event": "image_rendered"}]}

    def test_fresh_photo_post_has_no_alerts(self):
        from engine import alerts
        self.assertEqual(alerts.pre_approval_alerts(self.rec("2026-11-15T18:40:00+05:30", "photo"), self.S), [])

    def test_stale_card_is_flagged_twice(self):
        from engine import alerts
        al = alerts.pre_approval_alerts(self.rec("2026-11-09T14:31:05+05:30", "story"), self.S)
        self.assertEqual(len(al), 2)
        self.assertIn("2026-11-09", al[0])
        self.assertIn("album photo", al[1])

    def test_thursday_needs_scene(self):
        from engine import alerts
        r = self.rec("2026-11-18T18:40:00+05:30", "checklist", category="save_worthy", d="2026-11-19")
        self.assertIn("scene", alerts.pre_approval_alerts(r, self.S)[0])

    def test_missing_image_flagged(self):
        from engine import alerts
        r = self.rec("2026-11-15T18:40:00+05:30", "photo"); r["image_path"] = None
        self.assertIn("No image", alerts.pre_approval_alerts(r, self.S)[0])


class GitSyncBranchTests(unittest.TestCase):
    def test_always_targets_main(self):
        from engine import gitsync
        self.assertEqual(gitsync.DATA_BRANCH, "main")
        src = Path(gitsync.__file__).read_text()
        self.assertIn('f"HEAD:refs/heads/{b}"', src)
        self.assertNotIn('"push", "-u", "origin", b)', src)


class WedThuRuleTests(unittest.TestCase):
    """Shweta, 18 Nov 2026: Wednesday uses a client example; Thursday has no exact
    numbers, links or study citations and is tied to a client or personal story."""
    SRC = [{"title": "Guideline", "url": "https://example.org/g", "claim": "x"}]

    def rec(self, text, category, **kw):
        r = store.new_record(MON, settings())
        r.update(final=text, category=category, hook_style="relatable_moment", sources=self.SRC)
        r["humanizer"]["applied"] = True
        r.update(kw)
        return quality.check(r, settings())

    def test_wednesday_without_client_example_warns(self):
        self.assertTrue(any("client example" in i for i in self.rec(GOOD_TEXT, "educational")))
        self.assertFalse(any("client example" in i for i in self.rec(GOOD_TEXT, "educational", story_ids=["C05"])))

    def test_thursday_blocks_numbers_links_and_citations(self):
        bad = GOOD_TEXT + "\n\nA 2025 study published in a journal found 38% of women at https://x.com/a."
        issues = [i for i in self.rec(bad, "save_worthy", story_ids=["C02"]) if i.startswith("BLOCK")]
        self.assertTrue(any("link" in i for i in issues))
        self.assertTrue(any("cites studies" in i for i in issues))
        self.assertTrue(any("exact numbers" in i for i in issues))

    def test_thursday_list_markers_allowed(self):
        text = GOOD_TEXT + "\n\n1. Ask for the full panel\n2. Ask what normal means for you"
        issues = self.rec(text, "save_worthy", story_ids=["C02"])
        self.assertFalse(any("exact numbers" in i for i in issues), issues)

    def test_thursday_without_story_warns(self):
        self.assertTrue(any("client problem or personal story" in i for i in self.rec(GOOD_TEXT, "save_worthy")))

    def test_example_cooldown_is_shorter(self):
        hist = [{"post_id": "2026-10-27-tue", "date": "2026-10-27", "category": "client_story",
                 "story_ids": ["C05"], "publish_status": "published", "final": "x", "topic": "other"}]
        r = store.new_record(MON, settings())
        r.update(final=GOOD_TEXT, category="educational", hook_style="relatable_moment", story_ids=["C05"], topic="t")
        r["humanizer"]["applied"] = True
        self.assertFalse(any("C05" in i for i in quality.check(r, settings(), hist)))
        r.update(category="client_story")
        self.assertTrue(any("C05" in i for i in quality.check(r, settings(), hist)))


class FridayAndMessageIdTests(unittest.TestCase):
    SRC = [{"title": "Guideline", "url": "https://example.org/g", "claim": "x"}]

    def test_friday_follows_thursday_rule(self):
        """Shweta, 20 Nov 2026: Friday posts carry no numbers, links or study names either."""
        r = store.new_record(MON, settings())
        r.update(final=GOOD_TEXT + "\n\nA 2023 meta-analysis found 3.5 times the odds.", category="health_wellness",
                 hook_style="relatable_moment", sources=self.SRC, story_ids=["C02"])
        r["humanizer"]["applied"] = True
        issues = quality.check(r, settings())
        self.assertTrue(any(i.startswith("BLOCK: Friday post has exact numbers") for i in issues), issues)
        self.assertTrue(any("cites studies" in i for i in issues), issues)

    def test_mark_records_gmail_message_id(self):
        """20 Nov 2026: Gmail hid a sent approval email from the connector; the send result is the proof."""
        from engine.__main__ import main
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            make(tmp, d=date(2026, 11, 20))
            import engine.store as st
            old = st.POSTS_DIR if hasattr(st, "POSTS_DIR") else None
            try:
                st.POSTS_DIR = tmp
                main(["mark", "2026-11-20", "approval-requested", "--message-id", "abc123"])
                rec = store.load("2026-11-20-fri", tmp)
            finally:
                if old is not None:
                    st.POSTS_DIR = old
        self.assertEqual(rec["approval"]["message_id"], "abc123")
        self.assertEqual(rec["history"][-1]["message_id"], "abc123")
