# One-shot prompt: LinkedIn content engine for another person

Copy everything inside the fence into a new Claude Code cloud session. Fill the `{{…}}` placeholders first; anything you don't know, leave as `{{unknown}}` and Claude will list it as missing instead of inventing it.

```text
Act as a senior AI automation engineer, content strategist and full-stack developer. Build, test and launch a
fully automated LinkedIn content engine for the person below. Don't stop at a plan: inspect, build, test, and
go live in APPROVAL MODE. Ask me only what you cannot find yourself, and ask it all in one batch at the start.

## 1. Person (fill in)
- Name / brand: {{Full name}} / {{Brand}}
- Role and expertise: {{e.g. "ACE-certified hormonal-health coach"}}; credentials and EXACT allowed wording: {{…}}
- Audience: {{who, age band, country, pain points}}
- Offer / business (never put prices in posts unless I say): {{…}}
- Languages: {{English; occasional Hinglish OK?}}
- Emails for approvals/alerts: {{primary inbox (connected Gmail)}}, {{second address}}. Only these two can approve.
- Background sources (use ALL; never invent): {{Claude memory export file}}, {{interview/article URLs}},
  {{3–10 past LinkedIn post links (lnkd.in ok)}}, {{Drive docs}}, {{Fathom / call recordings: consent? Y/N}}
- Personal photo album for Mon–Wed: {{Google Photos shared-album link}}
- People-free "scene" photos for Thu/Fri: {{I will upload 5–10 landscape/object photos}}
- GitHub repo (private, created, Claude GitHub app has access): {{owner/repo}}
- Topics that are off-limits / people never to mention: {{…}}

## 2. Content strategy (Mon–Fri, 08:00 {{timezone, e.g. Asia/Kolkata}}; nothing at weekends)
- Mon: personal story. Use a story arc: moment → struggle → action → change → lesson.
- Tue: client story. Use STAR + lesson (situation, task, action, result, lesson). Anonymize everything.
  Only use verified outcomes, and state confounders honestly.
- Wed: educational (one idea, plain language).
- Thu: save-worthy, researched, current (last 7–30 days): checklist / steps / mistakes. Use the deep-research skill.
- Fri: {{domain}} health/wellness, researched, credible sources only. Use the deep-research skill.
Rules for every post:
- Never invent experiences, clients, quotes, numbers or studies.
- Write the person's clinical or professional beliefs as "in my practice/view", not as facts. Cite every statistic.
- Health posts: no doses, no "cure", never discourage medication; say how strong the evidence is.

## 3. Writing quality (enforce in code, not only in prompts)
- HOOK: the first paragraph is what shows before "…see more" (≤~140 chars on mobile). Write 3 options and pick
  the most curiosity-driving one fully supported by the post. Rotate hook styles (curiosity_gap,
  surprising_number, contrarian, story_drop_in, relatable_moment, direct_question). Ban generic openers
  ("Tomorrow is", "Did you know", "Here are", "As a coach").
- Story posts: at most 4 medical/technical terms and at most 3 numbers; lead with how the person felt or lived.
- Run EVERY post through the Humanizer skill (github.com/blader/humanizer; also vendor it into the repo).
  Record that it ran; after humanizing, diff against the draft so no new facts slip in.
- Lint the post: no em dashes, banned AI phrases, ≤3 specific hashtags, no engagement bait, 120–320 words
  (save-worthy up to 450), sources required on Thu/Fri, no repeated hook/story/topic (cooldowns).

## 4. Images (mobile-first; text must be readable at 360px phone width)
- Sizes: 1080×1350 portrait for photo and scene images (1080×1080 square for fallback cards). Render
  HTML → PNG with the pre-installed Playwright at 2×. Bundle the fonts in the repo (Poppins and Playfair
  Display, both open licence). Refuse to save an image whose text overflows; check a 360px phone preview
  before emailing it.
- Mon–Wed: a "photo" template using the person's own album photo: photo right, cream panel left, serif
  headline. Skip videos, alcohol branding and very tall photos; no photo reused within 28 days.
- Thu–Fri: a "scene" template using the uploaded people-free photos: full-bleed photo, dark gradient, white
  serif headline. Keep a catalogue of each scene's mood and the topics it suits. On Monday/Tuesday evenings,
  look ahead and EMAIL ME ≥24h before you run out of suitable scenes.
- LIGHT TEXT ON IMAGES: headline (≤60 chars) plus an optional short question (≤45 chars), ≤18 words in total,
  NO lists or answers on the image. The image raises the question; the post answers it.
- Copy every final image to a Google Drive folder "LinkedIn Post Images" (via the Composio
  GOOGLEDRIVE_UPLOAD_FROM_URL tool, using a public media URL). When an image is replaced, move the old one to
  Drive trash.

## 5. Publishing (learned the hard way; do it this way)
- Primary publisher: Zernio (zernio.com). The person connects their LinkedIn in Zernio, and I paste the API
  key into the secure credential form for zernio.com. Read the API from https://zernio.com/openapi.json.
  Personal-profile image posts and post analytics both work.
  - Send a FIXED Idempotency-Key per slot (UUIDv5 of the post id) on every create, so retries can never
    double-post.
  - Before publishing, run the verification test POST /v1/tools/validate/post (plus validate/media). Store a
    hash of the validated text and image path; refuse to publish if either changed afterwards.
- Backup: LinkedIn official API (Share on LinkedIn, w_member_social, /rest/images + /rest/posts). Needs a
  Company Page and a developer app; tokens last 60 days; escape LinkedIn "little text" reserved characters.
- Don't rely on Composio's LinkedIn tool for images (it only accepts Composio file keys). Pexels API keys are
  paused; Openverse full-size images are rate-limited. Use the person's own photos instead.
- Personal-profile post history and analytics for posts NOT made through your app aren't available from any
  API. To learn from past posts, fetch their public post pages (the JSON-LD on the page has text, date,
  likes, comments and image URL) and save them to history/; or import LinkedIn's data-export ZIP.
- After the FIRST live post, fetch the public page and confirm the text is identical and the image is attached.

## 6. Approval workflow
- APPROVAL MODE by default. Auto mode only after the person says so explicitly in chat; record it with a
  confirmation flag.
- Evening run (Sun–Thu, ~19:00 local; jitter a few minutes earlier to avoid scheduler congestion): generate
  tomorrow's post, humanize, lint, image, Zernio validation, Drive copy, then email both addresses. Subject
  "[LinkedIn] Approve: <Weekday> <date>: <topic>"; body has the full post, image links (Drive + GitHub; don't
  attach large PNGs), sources and questions.
- Replies: first line APPROVE / APPROVE WITH EDIT (+ full text) / EDIT / SKIP. Accept ONLY replies from the
  two addresses, sent AFTER the latest approval request (a changed post or image needs a fresh "(revised)"
  email). Anything unclear → ask again, never publish.
- Morning run (Mon–Fri, hourly 07:00–12:00): 07:00 reminder if still pending; from 08:00 validate, then
  publish if approved; 11:00 last call; at 12:00 the slot expires (skip and email), then fetch analytics.
  Email "Posted ✓ <url>" or a clear alert (auth expired → reconnect in Zernio; unknown outcome → check
  manually, never auto-retry).

## 7. Engineering
- A repo with: CLAUDE.md (non-negotiables + which runbook to follow), runbooks/generate.md,
  runbooks/morning.md, knowledge/ (profile with source keys, voice and style, beliefs/methodology, personal
  story bank, anonymized client case bank with confounders and exclusions, content pillars, brand-visual,
  gaps), content/posts/<date>.json (one record per slot = source of truth), content/images/,
  content/photos/{album,scenes}/, history/, research/, engine/ (Python stdlib + Playwright for rendering),
  tests/.
- Git is the database: write a durable "publishing" lock (commit + push) BEFORE the irreversible call. Pull
  with `git fetch origin main && git rebase FETCH_HEAD`, since fresh clones have no origin/main tracking ref.
  Commit only when the tests pass.
- CLI commands: new, check, image, image-url, validate, email-body, decide, mark, publish (--dry-run),
  record, mark-published / reset-publish, mode (approval/auto/pause/resume), history, fetch-analytics,
  import-post-url, import-history, status. Unit-test duplicate prevention, the window and expiry, approval
  parsing, escaping, idempotency, the validation gate, hooks and image rules.
- Secrets only through the secure credential form (network secrets per host); never in the repo or chat.
  Ask for network hosts only when a request is actually blocked.
- Scheduled tasks (claude.ai): two tasks (evening, morning) on the project's cloud environment. AFTER
  creating them, the person MUST add in the claude.ai UI (1) the repo (with push) and (2) the Gmail and
  Composio connectors to BOTH tasks. Then force-run the morning task with a "git push --dry-run" check and
  confirm "REPO PUSH: OK" before relying on it. Until that's verified, schedule a one-off backup check
  ~5 min after the first publish slot.

## 8. Order of work
1. Discovery (sources, connectors, past posts, gaps), then ask me one batch of questions.
2. Knowledge base with a source for every fact.
3. Engine + tests.
4. 5 sample posts (one per weekday) with images, shown to me with phone previews.
5. Zernio validation of all 5.
6. Approval emails.
7. Scheduled tasks + verification run.
8. Go live in approval mode.

At each step report what is done, what is blocked (with the exact setting I must change), and what you
assumed. Never publish anything I haven't approved.
```

## What this person still has to do themselves
1. Create a private GitHub repo and install the Claude GitHub app on it ("All repositories" is easiest).
2. Connect LinkedIn in Zernio and paste the Zernio API key into the secure form when asked.
3. Connect Gmail (+ Google Drive / Composio) in claude.ai.
4. After the scheduled tasks are created: add the repo and the Gmail + Composio connectors to both tasks in the claude.ai UI.
5. Share the photo album link and upload 5–10 people-free scene photos.
6. Reply APPROVE to the first emails.
