# Runbook: evening generation (19:00 IST, Sunday–Thursday)

Goal: produce tomorrow's post, humanized and quality-checked, and email it to Shweta for approval.

0. **Setup**
   - `cd` to the repo (clone `pearlshweta4u-svg/linkedin-content-engine` if missing), then `git fetch origin main && git rebase FETCH_HEAD`.
   - **Always save to `main`.** Scheduled sessions start on their own `claude/...` branch; the engine's `--git` already pushes to `main` (`HEAD:main`). If you ever push by hand, use `git push origin HEAD:main`, never the session branch (16 Nov 2026: runs pushed to side branches and `main` went stale for 4 days).
   - `D=$(python3 -m engine next-slot)`. If the file `content/posts/$D-*.json` already exists:
     - status `pending` with `approval.requested_at` empty → run `python3 -m engine alerts $D`. If it reports an old post or a wrong/missing image (e.g. an early sample card instead of her album/scene photo), redo step 7 (image) and 7b before emailing; otherwise skip to step 8. Don't rewrite the text.
     - otherwise (already emailed, approved, skipped) → stop. Duplicate prevention.
   - If `config/settings.json` has `"paused": true`, stop.

0b. **Image look-ahead (Monday and Tuesday evening runs)** (Shweta, 10 Nov 2026: "let me know 24 hours before"). Check `engine history` → `scenes_unused_28d` and plan this week's Thursday and Friday topics. If fewer than 2 scenes are unused, or none fits a planned topic, email both addresses **now** (at least 24 hours before the Thursday post is generated):
    - subject `[LinkedIn] Need more scene photos for Thursday/Friday`;
    - say which topics, what kind of people-free scene would fit (e.g. "a glass of water on a table", "morning walk path", "kitchen spices"), and how many.
    She'll send photos; save them to `content/photos/scenes/` and add a row to its README.

1. **Context**
   - Read `knowledge/` (all files) and the category for D (Mon `personal_story`, Tue `client_story`, Wed `educational`, Thu `save_worthy`, Fri `health_wellness`).
   - Run `python3 -m engine history`. Also read `published_before_engine` (her own earlier LinkedIn posts, from `history/posts.json`): don't repeat a topic or story she posted in the last 6 weeks, and treat her top performers as signals of what resonates. Respect `stories_on_cooldown`, `topics_on_cooldown` and `pillars_last_5`, prefer `pillars_missing_last_28d`, avoid the hook shapes in `recent_hooks`, and rotate `formats_last_8`.

1b. **Learn from what performed** (auto-improve, Shweta, 20 Nov 2026). The learning system lives in a separate repo.
   - If `/home/user/Linkedin-auto-improve` is missing, attach GitHub repo `pearlshweta4u-svg/Linkedin-auto-improve` (push access) with the add_repo tool and clone it there; otherwise `git -C /home/user/Linkedin-auto-improve pull --rebase origin main`.
   - `cd /home/user/Linkedin-auto-improve && python3 -m autoimprove refresh --git` (fresh impressions and comments for the last 30 days, re-ranks the top 10, rewrites `insights/PLAYBOOK.md`, pushes to its `main`).
   - `python3 -m autoimprove brief $D`, then read `insights/PLAYBOOK.md` and `insights/LEARNINGS.md`.
   - Use the reference posts to choose the hook shape, opening, structure, memorable line and image text for today's post. **Learn the shape, never the content**: every rule in CLAUDE.md, the cool-downs and this runbook still win, and no text is copied from a past post.
   - If the repo or Zernio is unavailable, carry on without it and add one line to the approval email: "Auto-improve skipped: <reason>".

2. **Pick the topic**
   - Mon: one story from `story-bank-personal.md` that isn't on cool-down. Use only its verified facts. Put any missing detail into `questions_for_shweta`.
   - Tue: one case from `case-bank-clients.md`. Respect its confounders and caveats. Fathom (if the connector works) may add verbatim phrasing; anonymize it.
   - Wed: one concept from `beliefs-and-methodology.md` / the pillars, **explained through a client example** from `case-bank-clients.md` (anonymized, verified facts only; put its id in `story_ids`). The idea leads; the client example shows it in real life. Research any factual claim. (Shweta, 18 Nov 2026.) A case used as a Wed/Thu example rests 14 days (`example_cooldown_days`); a full Tuesday story still rests 56.
   - Thu: **use the `deep-research` skill** (anthropic-skills:deep-research). Find a development from the last 7–30 days relevant to her pillars (a new study, guideline, Indian health news). Pick a save-worthy format (checklist, step-by-step, mistakes).
     **In the post (Shweta, 18 Nov 2026): no exact numbers, no links, no study or journal names.** Say what the research means in plain words ("most women", "in your forties", "newer guidance says") and relate it to a client problem or her own story (add the C/P id to `story_ids`). The research goes in `sources` and the approval email only. List numbering (1. 2. 3.) is fine. `engine check` blocks digits, links and citation phrases on Thursdays.
   - Fri: **use the `deep-research` skill**. Pick one general-health topic (see the Friday pool), sourced from credible bodies. State evidence strength honestly.
   - If research doesn't support the planned angle, change the angle. Never stretch the evidence.

3. **Create the record**
   - Run `python3 -m engine new $D`.
   - Fill in `pillar` (one of the keys in `engine/__main__.py` PILLARS), `topic`, `angle`, `format`, `story_ids`, `sources` (`{title, url, publisher, published, accessed, claim}`), `claims_checked`, and `questions_for_shweta`.
   - Also fill `learning` (from step 1b): `{"references": [<post ids from the brief>], "reused": "<what shape you took from them>", "improved": "<what you are doing better>"}`. The auto-improve refresh reads it to check whether the playbook is helping. Put the same two lines at the end of the approval email under "What this post learned from".

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
   - Body: the output of `python3 -m engine email-body $D`. If it starts with an **ALERT** block, keep it at the top and add ` (⚠ check image)` to the subject.
   - The body already links the image on GitHub (push the image before sending so the link works). Don't attach the PNG: encoded images are too large to pass through the mail tool.
   - In auto mode, use the subject `[LinkedIn] Scheduled: …` and add "Reply SKIP to stop it".

9. Run `python3 -m engine mark $D approval-requested --git`. This commits the record and pushes. Confirm the push succeeded.
