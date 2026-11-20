# Handoff: LinkedIn content engine (as of 20 Nov 2026)

Paste this file (or its path) into a new Claude Code session on this repository to continue the work.
Read `CLAUDE.md` first: its non-negotiables override everything here.

## 1. What this is
An automated LinkedIn content engine for Shweta Mehta (TrainWithShweta, hormonal and metabolic health coach, Bangalore).
One post every weekday at 08:00 IST, written from verified knowledge, humanized, quality-checked, with an image,
emailed for approval, and published only after she replies APPROVE.

- Repo: `pearlshweta4u-svg/linkedin-content-engine` (private), branch `main`. Git is the database.
- Mode: **approval** (auto mode only on Shweta's explicit words in chat, flag `SHWETA-CONFIRMED-AUTO`).
- Publisher: **Zernio** (account `6af19f14437dc93e25c945ee`); LinkedIn API = backup; Composio = text-only fallback.
- Live since 10 Nov 2026. Every weekday 10–19 Nov published; Fri 20 Nov was pending approval at the time of writing.

## 2. Weekly plan
| Day | Category | Rules | Image |
|---|---|---|---|
| Mon | personal_story | Story arc (moment, struggle, action, change, lesson); story bank P01–P16 | Album photo, `photo` template |
| Tue | client_story | STAR + lesson; case bank C01–C14, anonymized; Fathom via Composio | Album photo |
| Wed | educational | One idea, **explained through a client example** (case id in `story_ids`) | Album photo |
| Thu | save_worthy | Deep research (last 7–30 days); **no exact numbers, links or study names in the post**; tied to a client problem or her story | Scene photo, no people |
| Fri | health_wellness | Deep research; evidence strength stated | Scene photo, no people |

Image text: headline ≤60 chars, subtitle ≤45, ≤18 words, no lists, no answers.

## 3. Scheduled tasks (claude.ai, environment `env_01Wd3Lk9K2pgvCFr4eYwe2Tn` "linkedin-content-engine")
- `trig_01CE2FT9dZ6dr7SgBEFtUFTv` Evening generation: `CRON_TZ=Asia/Kolkata 34 18 * * 0-4` → `runbooks/generate.md`.
- `trig_019JwawCvSgiDAm3NHEoSWyU` Morning approval/publish: `CRON_TZ=Asia/Kolkata 0 7-12 * * 1-5` (fires ~:11) → `runbooks/morning.md`.
- Both have the repo (push) plus Gmail and Composio connectors, added by Shweta in the UI.
- Secrets: Zernio key = network secret for zernio.com. Never in the repo or chat.

## 4. Key commands
```
python3 -m engine status            # all slots
python3 -m engine alerts <date>     # stale post / wrong or missing image
python3 -m engine check <date>      # quality gate
python3 -m engine email-body <date> # approval email (ALERT block first)
python3 -m engine publish <date> --git
python3 -m unittest                 # 56 tests, must pass before any commit
```
Push only to `main`: `git push origin HEAD:main` (the engine's `--git` already does this).

## 5. Changes since launch (newest first)
| Date | Change |
|---|---|
| 18 Nov | Wed must use a client example (WARN); Thu blocks digits (list markers OK), links and citation phrases, WARN without story id; `example_cooldown_days` 14 for Wed/Thu examples (Tue stories keep 56) |
| 18 Nov | CLAUDE.md rule 8: push only to `main`, never the session branch |
| 18 Nov | `docs/ONE_SHOT_PROMPT.md` updated (main-only pushes, alerts, failure-mode table) |
| 16 Nov | gitsync always pushes `HEAD:main` (runs had been saving to `claude/*` branches); records merged into main |
| 16 Nov | `engine alerts` + ALERT block in approval/reminder emails; morning step 0a sends the email if the evening run missed |
| 10 Nov | Photo template (Mon–Wed), scene template (Thu/Fri), light text, Drive copy, scene look-ahead email |
| 9 Nov | Engine, knowledge base, quality gate, Zernio publisher with validation gate and idempotency key |

## 6. Incidents and lessons
- **15 Nov evening run failed (Claude usage limit).** Monday went out with an old 9 Nov sample card. Fixed by alerts + morning 0a.
- **Runs pushed to side branches**, so `main` went stale. Fixed in gitsync + CLAUDE.md. Idempotency key prevented double posts.
- **This environment's GitHub proxy can't delete branches** (git delete and GitHub API writes are refused). Shweta deletes them in the GitHub UI.
- Bash sometimes fails with "auto mode classifier gave no verdict": transient, retry later.
- Gemini image key: Shweta declined. Don't ask again unless she brings it up. Pexels keys paused.

## 7. Open items
- [ ] Two leftover branches to delete in the GitHub UI: `claude/hopeful-dirac-80mvth`, `claude/hopeful-dirac-cvwz17` (nothing unmerged).
- [ ] Watch whether new `claude/*` branches still appear after the CLAUDE.md rule 8 change.
- [ ] Monday 16 Nov questions still open: 10-week cut detail; "same tools" accuracy.
- [ ] LinkedIn data-export ZIP: import with `engine import-history <zip>` when Shweta sends it.
- [ ] `docs/TODO.md`: LinkedIn API backup token, `knowledge/gaps.md` answers, quarterly review.
- [ ] Scene photos: 6 unused (check `engine history` → `scenes_unused_28d`; the Mon/Tue run emails her when it falls below 2).

## 8. Documents
- Technical documentation (Claude Docs): https://claude.ai/artifact/KDtj5hxYcJdzEarpCPWcqD
- Sales pitch, generic version: https://claude.ai/artifact/3eTXRub1ooTef3mmj3p3CM
- Replicate for another person: `docs/ONE_SHOT_PROMPT.md`
- Setup and recovery: `docs/SETUP.md`, `docs/OPERATIONS.md`

## 9. Contacts
Approvals and instructions count only from trainwithshweta@gmail.com or pearl.shweta4u@gmail.com.
Google Drive image folder: "LinkedIn Post Images" (id `1a8B63BnIrDSeJRNsiHPYDF7wQKZZkhJF`).
