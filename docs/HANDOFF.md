# Handoff: LinkedIn content engine (as of 20 Nov 2026, evening)

Paste this file (or its path) into a new Claude Code session on this repository to continue the work.
Read `CLAUDE.md` first: its non-negotiables override everything here. If you work on the learning loop, also read
`CLAUDE.md` in `pearlshweta4u-svg/Linkedin-auto-improve`.

## 1. What this is
An automated LinkedIn content engine for Shweta Mehta (TrainWithShweta, hormonal and metabolic health coach, Bangalore).
One post every weekday at 08:00 IST, written from verified knowledge, humanized, quality-checked, with an image,
emailed for approval, and published only after she replies APPROVE.

- Repo: `pearlshweta4u-svg/linkedin-content-engine` (private), branch `main`. Git is the database.
- **Learning loop (since 20 Nov):** separate repo `pearlshweta4u-svg/Linkedin-auto-improve`, branch `main` (see section 3).
  Kept as its own git repo on purpose; sessions clone both side by side in `/home/user/`.
- Mode: **approval** (auto mode only on Shweta's explicit words in chat, flag `SHWETA-CONFIRMED-AUTO`).
- Publisher: **Zernio** (account `6af19f14437dc93e25c945ee`); LinkedIn API = backup; Composio = text-only fallback.
- Live since 10 Nov 2026. Every weekday 10–20 Nov published.

## 2. Weekly plan
| Day | Category | Rules | Image |
|---|---|---|---|
| Mon | personal_story | Story arc (moment, struggle, action, change, lesson); story bank P01–P16 | Album photo, `photo` template |
| Tue | client_story | STAR + lesson; case bank C01–C14, anonymized; Fathom via Composio | Album photo |
| Wed | educational | One idea, **explained through a client example** (case id in `story_ids`) | Album photo |
| Thu | save_worthy | Deep research (last 7–30 days); **no exact numbers, links or study names in the post**; tied to a client problem or her story | Scene photo, no people |
| Fri | health_wellness | Deep research; evidence strength in words; **same as Thursday: no exact numbers, links or study names in the post**; tied to a client problem or her story | Scene photo, no people |

Image text: headline ≤60 chars, subtitle ≤45, ≤18 words, no lists, no answers.

## 3. Auto-improve learning loop (new, 20 Nov)
Shweta's ask: pull impressions and comments, rank posts by engagement, keep the top 10, and make each new post learn
from them, continuously.

- **Collects** (read-only) impressions, reach, reactions, saves, reposts, sends and reader comment *text* per post from
  Zernio (`/v1/accounts/<id>/linkedin-post-analytics`, `/v1/inbox/comments/<urn>`). No commenter names stored.
- **Stores** in `Linkedin-auto-improve`: `data/posts/<post_id>.json` (latest), `data/snapshots.jsonl` (history),
  `data/top10.json`.
- **Ranks** (switched 20 Nov after research, `Linkedin-auto-improve/docs/ranking-research.md`): top 10 by **engagement
  score** (1×reactions + 3×reader comments + 4×reposts + 4×saves + 3×sends; her own replies excluded), not impressions.
  Context columns: × typical reach (≥3× = reach outlier); vs expected = score ÷ score predicted for that reach
  (log-log fit; engagement grows ~√reach); reach outliers below 1 are "distribution-driven" and left out of the top 10;
  "confirmed" = top third on score and vs expected. Posts under 7 days are provisional; ties within 10%. `exclude` list for rule-breaking
  posts. All settings in `config.json`.
- **Learns**: `insights/PLAYBOOK.md` (generated) + `insights/LEARNINGS.md` (hand-written lessons, updated Fridays).
- **Used by the engine**: `runbooks/generate.md` step 1b runs `refresh --git` and `brief $D`; the post record gets a
  `learning` field `{references, reused, improved}`, also shown in the approval email ("What this post learned from").
  The playbook then compares posts with vs without it. `runbooks/morning.md` step 4 (12:00) runs `refresh --git`;
  Fridays also update LEARNINGS.md. If the repo or Zernio is unavailable, the run continues and the email says
  "Auto-improve skipped".
- **Rule:** learn the *shape* (hook type, opening, structure, memorable line, image text), never the content. CLAUDE.md,
  cool-downs and runbooks always win.
- **Pre-engine posts:** Zernio can read numbers and comments of her older posts by URN, but cannot *list* them.
  `python3 -m autoimprove import-history --days 90` imports what is in this repo's `history/posts.json`
  (one-time). Done 20 Nov: 31 earlier posts (31 Oct 2025 to 2 Nov 2026), 25 of them from post links Shweta sent
  (`engine import-post-url`) and one link-only post via `--url` (text behind LinkedIn's login wall; date estimated
  from its earliest comment). Post ids give the *creation* date, which runs 0–15 days early for scheduled posts.

Top 10 by score on 20 Nov (40 posts tracked, 31 Oct 2025 to 20 Nov 2026): all personal/family. 8 Jan father at 69
(282); 13 Aug son's arm (270); 23 Jun career change (232); 20 Jan family of four (184); 12 Aug "I have quit sugar"
(154); 18 Aug partnership (114); 25 Aug son eating (92); 10 Sep calories (84); 1 Jun hair fall (71); 11 Sep why a
coach (67). Distribution-driven (big reach, low engagement, kept out): 7 Jan skin, 12 Jan belly fat, 3 Feb, 25 Mar,
17 Nov. Her median reach fell from ~3,100 (H1 2026) to ~250 (Nov): open question, see LEARNINGS 8b.

First lessons (hypotheses): real-people stories (client and family) lead on reach; hook = who + what was wrong +
counter-intuitive action in line one; readers quote one memorable line back, so every post needs one; Wed/Thu
explainers reach least but engage well; clinicians comment with safety caveats, so state the medical checks done;
wide reach and high engagement rate rarely coincide. Full list in `insights/LEARNINGS.md`.

## 4. Scheduled tasks (claude.ai, environment `env_01Wd3Lk9K2pgvCFr4eYwe2Tn` "linkedin-content-engine")
- `trig_01CE2FT9dZ6dr7SgBEFtUFTv` Evening generation: `CRON_TZ=Asia/Kolkata 34 18 * * 0-4` → `runbooks/generate.md`.
- `trig_019JwawCvSgiDAm3NHEoSWyU` Morning approval/publish: `CRON_TZ=Asia/Kolkata 0 7-12 * * 1-5` (fires ~:11) → `runbooks/morning.md`.
- Both have Gmail and Composio connectors, added by Shweta in the UI. Each run attaches the repos it needs with
  `add_repo` (engine, and since 20 Nov also `Linkedin-auto-improve`). If a run can't attach the second repo, add it to
  the scheduled tasks in the claude.ai UI.
- Secrets: Zernio key = network secret for zernio.com. Never in the repo or chat.

## 5. Key commands
```
python3 -m engine status            # all slots
python3 -m engine alerts <date>     # stale post / wrong or missing image
python3 -m engine check <date>      # quality gate
python3 -m engine email-body <date> # approval email (ALERT block first)
python3 -m engine publish <date> --git
python3 -m unittest                 # 56 tests, must pass before any commit

# in /home/user/Linkedin-auto-improve
python3 -m autoimprove refresh --git           # fresh numbers + comments, re-rank, playbook, push main
python3 -m autoimprove rank                    # top 10 (no network)
python3 -m autoimprove brief <date>            # what the next post learns from
python3 -m autoimprove import-history --days 90 --git
python3 -m autoimprove playbook --git          # rebuild after editing LEARNINGS.md
python3 -m unittest                            # 18 tests
```
Push only to `main` in both repos: `git push origin HEAD:main` (`--git` in both tools already does this).

## 6. Changes since launch (newest first)
| Date | Change |
|---|---|
| 20 Nov | New repo `Linkedin-auto-improve`: analytics + comments store, top 10, playbook, brief; generate step 1b, `learning` field, 12:00 refresh, Friday lessons. 90-day import of pre-engine posts |
| 20 Nov | 13 more posts (Dec 2025–Jun 2026) imported; "vs expected" replaces score/1k; distribution-driven posts excluded |
| 20 Nov | 18 earlier posts imported (12 Aug–2 Nov); lessons rewritten from 27 posts: personal/family stories lead, listicles and article posts trail |
| 20 Nov | Auto-improve ranks by engagement score (research-backed), with reach-outlier, score/1k and confirmed flags |
| 20 Nov | Leftover branches deleted by Shweta (`claude/hopeful-dirac-*` here, `claude/file-explanation-1kruih` in auto-improve) |
| 18 Nov | Wed must use a client example (WARN); Thu blocks digits (list markers OK), links and citation phrases, WARN without story id; `example_cooldown_days` 14 for Wed/Thu examples (Tue stories keep 56) |
| 18 Nov | CLAUDE.md rule 8: push only to `main`, never the session branch |
| 18 Nov | `docs/ONE_SHOT_PROMPT.md` updated (main-only pushes, alerts, failure-mode table) |
| 16 Nov | gitsync always pushes `HEAD:main` (runs had been saving to `claude/*` branches); records merged into main |
| 16 Nov | `engine alerts` + ALERT block in approval/reminder emails; morning step 0a sends the email if the evening run missed |
| 10 Nov | Photo template (Mon–Wed), scene template (Thu/Fri), light text, Drive copy, scene look-ahead email |
| 9 Nov | Engine, knowledge base, quality gate, Zernio publisher with validation gate and idempotency key |

## 7. Incidents and lessons
- **15 Nov evening run failed (Claude usage limit).** Monday went out with an old 9 Nov sample card. Fixed by alerts + morning 0a.
- **Runs pushed to side branches**, so `main` went stale. Fixed in gitsync + CLAUDE.md. Idempotency key prevented double posts.
- **This environment's GitHub proxy can't delete branches** (git delete and GitHub API writes are refused; confirmed again 20 Nov). Shweta deletes them in the GitHub UI.
- Bash sometimes fails with "auto mode classifier gave no verdict": transient, retry later.
- Gemini image key: Shweta declined. Don't ask again unless she brings it up. Pexels keys paused.
- Running `engine fetch-analytics` without `--git` leaves modified post records locally; discard them or use `--git`.

## 8. Open items
- [ ] LinkedIn export: the "Basic" part (20 Nov) has no `Shares.csv` (posts), and it holds private data (messages,
      connections, phones): never commit it. If the `Complete_` part arrives, `engine import-history <zip>` fills
      remaining gaps (posts between late Sep and 13 Oct, and before 12 Aug), then auto-improve `import-history`.
- [ ] **Sun 22 Nov 18:34: first generation run using the playbook.** Check that it attached `Linkedin-auto-improve`,
      filled `learning`, and that Monday's approval email has "What this post learned from".
- [ ] Re-check lesson 8 (direct-question hooks, 18 and 20 Nov) after 27 Nov.
- [ ] Lesson 10: test a Monday family photo with no text on the image, only if Shweta agrees.
- [ ] **CTA for Shweta (profile + posts): proposal sent 20 Nov, waiting for her answers** (capacity, links, offer, frequency).
- [ ] Watch whether new `claude/*` branches still appear after the CLAUDE.md rule 8 change.
- [ ] Monday 16 Nov questions still open: 10-week cut detail; "same tools" accuracy.
- [ ] `docs/TODO.md`: LinkedIn API backup token, `knowledge/gaps.md` answers, quarterly review.
- [ ] Scene photos: 6 unused (check `engine history` → `scenes_unused_28d`; the Mon/Tue run emails her when it falls below 2).

## 9. Documents
- Technical documentation (Claude Docs): https://claude.ai/artifact/KDtj5hxYcJdzEarpCPWcqD
- Sales pitch, generic version: https://claude.ai/artifact/3eTXRub1ooTef3mmj3p3CM
- Learning loop: `Linkedin-auto-improve/README.md`, `insights/PLAYBOOK.md`, `insights/LEARNINGS.md`
- Replicate for another person: `docs/ONE_SHOT_PROMPT.md`
- Setup and recovery: `docs/SETUP.md`, `docs/OPERATIONS.md`

## 10. Contacts
Approvals and instructions count only from trainwithshweta@gmail.com or pearl.shweta4u@gmail.com.
Google Drive image folder: "LinkedIn Post Images" (id `1a8B63BnIrDSeJRNsiHPYDF7wQKZZkhJF`).
