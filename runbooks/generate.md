# Runbook: evening generation (19:00 IST, Sunday–Thursday)

Goal: produce tomorrow's post, humanized and quality-checked, and email it to Shweta for approval.

0. **Setup**
   - `cd` to the repo (clone `pearlshweta4u-svg/linkedin-content-engine` if missing), then `git pull --rebase`.
   - `D=$(python3 -m engine next-slot)`. If the file `content/posts/$D-*.json` already exists:
     - status `pending` with `approval.requested_at` empty → skip to step 7 (image, if missing) and step 8 (send the approval email). Don't regenerate.
     - otherwise (already emailed, approved, skipped) → stop. Duplicate prevention.
   - If `config/settings.json` has `"paused": true`, stop.

0b. **Image look-ahead (Monday and Tuesday evening runs)** (Shweta, 10 Nov 2026: "let me know 24 hours before"). Check `engine history` → `scenes_unused_28d` and plan this week's Thursday and Friday topics. If fewer than 2 scenes are unused, or none fits a planned topic, email both addresses **now** (at least 24 hours before the Thursday post is generated):
    - subject `[LinkedIn] Need more scene photos for Thursday/Friday`;
    - say which topics, what kind of people-free scene would fit (e.g. "a glass of water on a table", "morning walk path", "kitchen spices"), and how many.
    She'll send photos; save them to `content/photos/scenes/` and add a row to its README.

1. **Context**
   - Read `knowledge/` (all files) and the category for D (Mon `personal_story`, Tue `client_story`, Wed `educational`, Thu `save_worthy`, Fri `health_wellness`).
   - Run `python3 -m engine history`. Also read `published_before_engine` (her own earlier LinkedIn posts, from `history/posts.json`): don't repeat a topic or story she posted in the last 6 weeks, and treat her top performers as signals of what resonates. Respect `stories_on_cooldown`, `topics_on_cooldown` and `pillars_last_5`, prefer `pillars_missing_last_28d`, avoid the hook shapes in `recent_hooks`, and rotate `formats_last_8`.

2. **Pick the topic**
   - Mon: one story from `story-bank-personal.md` that isn't on cool-down. Use only its verified facts. Put any missing detail into `questions_for_shweta`.
   - Tue: one case from `case-bank-clients.md`. Respect its confounders and caveats. Fathom (if the connector works) may add verbatim phrasing; anonymize it.
   - Wed: one concept from `beliefs-and-methodology.md` / the pillars. Research any factual claim.
   - Thu: **use the `deep-research` skill** (anthropic-skills:deep-research). Find a development from the last 7–30 days relevant to her pillars (a new study, guideline, Indian health news). Connect it to a case or her method. Pick a save-worthy format.
   - Fri: **use the `deep-research` skill**. Pick one general-health topic (see the Friday pool), sourced from credible bodies. State evidence strength honestly.
   - If research doesn't support the planned angle, change the angle. Never stretch the evidence.

3. **Create the record**
   - Run `python3 -m engine new $D`.
   - Fill in `pillar` (one of the keys in `engine/__main__.py` PILLARS), `topic`, `angle`, `format`, `story_ids`, `sources` (`{title, url, publisher, published, accessed, claim}`), `claims_checked`, and `questions_for_shweta`.

4. **Draft** following `knowledge/voice-and-style.md`. Write it to `draft`.
   - Hook first: write 3 opening options per the Hooks section, pick the most curiosity-driving one that is fully supported by the post's facts, and set `hook_style` (rotate; check `engine history` → recent_hooks).
   - Mon/Tue: first fill `story_structure` (Tue STAR: situation, task, action, result, lesson; Mon story arc: moment, struggle, action, change, lesson), one or two lines per beat from verified facts only, then write the post in that order. Keep it plain: max 4 medical terms, max 3 numbers.
   - Tue: also check the client's recent Fathom calls (Composio tools `FATHOM_LIST_MEETINGS`, `FATHOM_GET_RECORDING_SUMMARY`, `FATHOM_GET_RECORDING_TRANSCRIPT`) for fresh, verified details and her own phrasing. Anonymize everything.

5. **Humanize (mandatory)**
   - Apply the Humanizer skill to the draft. Write the result to `final`.
   - Then check `final` against `draft` line by line. Any fact, number, name or claim that is new in `final` is an error: remove it.
   - Set `humanizer = {"applied": true, "at": <now>, "version": "3.1.0", "changes_summary": "<the 2-4 main patterns removed>"}`.

6. **Quality gate**
   - Run `python3 -m engine check $D`.
   - Fix every `BLOCK` (re-apply the Humanizer to the changed passage) and re-run. Up to 3 rounds.
   - If it still fails, email Shweta "No post ready for <D>: <issues>" and stop. A missed day is better than a weak post.

7. **Image** (`images_enabled` is true). Write `image_spec` into the record, then run `python3 -m engine image $D`:
   - **Mon/Tue/Wed: use her real photo** (her best past posts are real photos) with the `photo` template:
     1. Fetch the album in `config/settings.json` → `photos.album_url`: the page lists `lh3.googleusercontent.com/pw/...` URLs. Download small previews (`=w400-h400`) to the scratchpad and look at them.
     2. Pick a photo that fits the post's mood. Never a video (play icon), never alcohol branding, and none in `engine history` → `photos_used_last_28d`.
     3. Download the chosen photo at `=w2000` to `content/photos/album-<n>.jpg`.
     4. `image_spec`: `{"template":"photo","photo":"content/photos/album-<n>.jpg","eyebrow" (1–3 words),"title" (serif headline that raises the question, ≤60 chars),"subtitle" (optional italic tease, ≤45 chars),"photo_right" (px; move until her face is clear of the cream panel, typically -200 to -350),"photo_scale" (~1.1–1.2),"alt"}`.
        **Less text, no answers** (Shweta, 10 Nov 2026): no list items, at most 18 words in total. The image creates curiosity; the solution stays in the post. Good: "Normal report. Still exhausted?" Bad: anything that lists the steps.
     5. Check that her face isn't under the cream panel and that the phone preview is readable.
   - **Thursday and Friday: no photos of Shweta or other people** (Shweta, 10 Nov 2026). Use the `scene` template with a photo from `content/photos/scenes/` (see its README for the mood of each):
     `{"template":"scene","photo":"content/photos/scenes/<file>.jpg","focus":"<css position, e.g. 40% center>","text_position":"top|bottom","eyebrow","title" (≤60),"subtitle" (≤45),"alt"}`, with no list items and at most 18 words. Look at the render: the text must sit on the darker part and stay readable on a phone.
   - Fallback designed cards only when no photo or scene fits (Thu/Fri, or when no suitable photo): Mon/Tue `story` (a headline echoing the hook plus a one-line takeaway), Wed `steps` (2–4 short steps), Thu `checklist` (portrait 1080×1350, up to 7 one-line items of ≤45 characters), Fri `stat` (one verified number, with `source`). Cards are square 1080×1080 so they're readable on phones.
   - Check mobile legibility: `python3 -c "from engine import images; images.phone_preview('content/images/<id>.png','/tmp/p.png')"` and look at /tmp/p.png (360px wide = a phone feed). Body text must be easy to read there.
   - The image must only contain words and numbers that are already in the post or its sources. It must add structure (steps, a checklist, a key number), not repeat the first line. Always set `alt`.
   - If the command says the text doesn't fit, shorten the copy and re-run. Never accept a clipped image.
   - Look at the PNG (Read tool) before emailing. Check the layout, that nothing is cut off, and that it's readable at phone size.
   - Output: `content/images/<post-id>.png` (2× resolution).
   - **Copy to Google Drive** (Shweta's local folder via Drive for desktop):
     1. Push the image.
     2. Run `python3 -m engine image-url $D --git` to get a public URL.
     3. Call Composio `GOOGLEDRIVE_UPLOAD_FROM_URL` with `source_url` = that URL, `name` = `<post-id>.png`, `mime_type` image/png, and `parent_folder_id` = `google_drive.images_folder_id` from config/settings.json.
     4. Run `python3 -m engine mark-drive $D <drive file id> --git`.
     5. If the image is re-rendered later (record already has `drive_file_id`): upload the new file, then move the old one to Drive trash with Composio `GOOGLEDRIVE_TRASH_FILE` (`file_id` = the old `drive_file_id`), then `mark-drive` the new id.
     6. If Composio is unavailable, skip this step; the image is still in the repo, and say so in the approval email.

7b. **Verification test:** `python3 -m engine validate $D --git`, a Zernio dry-run of text and image. If invalid, fix the issue (text length, image format) and re-run; the result goes in the approval email. The Zernio MCP tool `validate_post` (connector "zernio") gives the same check interactively.

8. **Approval email** (Gmail tool, from trainwithshweta@gmail.com):
   - To both addresses in `notify_emails`.
   - Subject: `[LinkedIn] Approve: <Weekday> <D>: <topic>`
   - Body: the output of `python3 -m engine email-body $D`.
   - The body already links the image on GitHub (push the image before sending so the link works). Don't attach the PNG: encoded images are too large to pass through the mail tool.
   - In auto mode, use the subject `[LinkedIn] Scheduled: …` and add "Reply SKIP to stop it".

9. Run `python3 -m engine mark $D approval-requested --git`. This commits the record and pushes. Confirm the push succeeded.
