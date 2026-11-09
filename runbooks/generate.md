# Runbook: evening generation (19:00 IST, Sunday–Thursday)

Goal: produce tomorrow's post, humanized and quality-checked, and email it to Shweta for approval.

0. **Setup**
   - `cd` to the repo (clone `pearlshweta4u-svg/linkedin-content-engine` if missing), then `git pull --rebase`.
   - `D=$(python3 -m engine next-slot)`. If the file `content/posts/$D-*.json` already exists:
     - status `pending` with `approval.requested_at` empty → skip to step 7 (image, if missing) and step 8 (send the approval email). Don't regenerate.
     - otherwise (already emailed, approved, skipped) → stop. Duplicate prevention.
   - If `config/settings.json` has `"paused": true`, stop.

1. **Context**
   - Read `knowledge/` (all files) and the category for D (Mon `personal_story`, Tue `client_story`, Wed `educational`, Thu `save_worthy`, Fri `health_wellness`).
   - Run `python3 -m engine history`. Respect `stories_on_cooldown`, `topics_on_cooldown` and `pillars_last_5`, prefer `pillars_missing_last_28d`, avoid the hook shapes in `recent_hooks`, and rotate `formats_last_8`.

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
   - Template by day: Mon/Tue `story` (a headline from the post plus a one-line takeaway), Wed `steps` (2–4 short steps), Thu `checklist` (portrait, up to 7 items), Fri `stat` (one verified number, with `source`).
   - The image must only contain words and numbers that are already in the post or its sources. It must add structure (steps, a checklist, a key number), not repeat the first line. Always set `alt`.
   - If the command says the text doesn't fit, shorten the copy and re-run. Never accept a clipped image.
   - Look at the PNG (Read tool) before emailing. Check the layout, that nothing is cut off, and that it's readable at phone size.
   - Output: `content/images/<post-id>.png` (2× resolution).
   - **Copy to Google Drive** (Shweta's local folder via Drive for desktop):
     1. Push the image.
     2. Run `python3 -m engine image-url $D --git` to get a public URL.
     3. Call Composio `GOOGLEDRIVE_UPLOAD_FROM_URL` with `source_url` = that URL, `name` = `<post-id>.png`, `mime_type` image/png, and `parent_folder_id` = `google_drive.images_folder_id` from config/settings.json.
     4. Run `python3 -m engine mark-drive $D <drive file id> --git`.
     5. If the image is re-rendered later, upload the new file with the same name (Drive keeps both; the newer one is the current image).
     6. If Composio is unavailable, skip this step; the image is still in the repo, and say so in the approval email.

8. **Approval email** (Gmail tool, from trainwithshweta@gmail.com):
   - To both addresses in `notify_emails`.
   - Subject: `[LinkedIn] Approve: <Weekday> <D>: <topic>`
   - Body: the output of `python3 -m engine email-body $D`.
   - The body already links the image on GitHub (push the image before sending so the link works). Don't attach the PNG: encoded images are too large to pass through the mail tool.
   - In auto mode, use the subject `[LinkedIn] Scheduled: …` and add "Reply SKIP to stop it".

9. Run `python3 -m engine mark $D approval-requested --git`. This commits the record and pushes. Confirm the push succeeded.
