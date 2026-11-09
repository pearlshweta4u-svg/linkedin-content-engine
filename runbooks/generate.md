# Runbook: evening generation (19:00 IST, Sunday–Thursday)

Goal: produce tomorrow's post, humanized and quality-checked, and email it to Shweta for approval.

0. **Setup**
   - `cd` to the repo (clone `pearlshweta4u-svg/linkedin-content-engine` if missing), then `git pull --rebase`.
   - `D=$(python3 -m engine next-slot)`. If the file `content/posts/$D-*.json` already exists and isn't `draft`, stop: it has already been generated (duplicate prevention).
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

5. **Humanize (mandatory)**
   - Apply the Humanizer skill to the draft. Write the result to `final`.
   - Then check `final` against `draft` line by line. Any fact, number, name or claim that is new in `final` is an error: remove it.
   - Set `humanizer = {"applied": true, "at": <now>, "version": "3.1.0", "changes_summary": "<the 2-4 main patterns removed>"}`.

6. **Quality gate**
   - Run `python3 -m engine check $D`.
   - Fix every `BLOCK` (re-apply the Humanizer to the changed passage) and re-run. Up to 3 rounds.
   - If it still fails, email Shweta "No post ready for <D>: <issues>" and stop. A missed day is better than a weak post.

7. **Image**: only if `images_enabled` is true (currently false; see `docs/TODO.md`).

8. **Approval email** (Gmail tool, from trainwithshweta@gmail.com):
   - To both addresses in `notify_emails`.
   - Subject: `[LinkedIn] Approve: <Weekday> <D>: <topic>`
   - Body: the output of `python3 -m engine email-body $D`
   - In auto mode, use the subject `[LinkedIn] Scheduled: …` and add "Reply SKIP to stop it".

9. Run `python3 -m engine mark $D approval-requested --git`. This commits the record and pushes. Confirm the push succeeded.
