# Runbook: morning approval & publish (hourly 07:00–12:00 IST, Monday–Friday)

The same runbook runs at 07, 08, 09, 10, 11 and 12 o'clock. It's safe to run any number of times.

0. Clone or pull the repo (see `generate.md` step 0). `D=$(date +%F)` in IST (`TZ=Asia/Kolkata date +%F`). If there's no record for D: at 07:00 only, email "No post was generated for today", then stop.

1. **Read the approval reply** (only if `approval_status` is `pending` or `draft`):
   - Gmail search: `subject:"[LinkedIn] Approve" subject:<D> (from:trainwithshweta@gmail.com OR from:pearl.shweta4u@gmail.com) newer_than:3d`. Open the thread with `get_thread` and take the **newest reply written by Shweta** (not the original approval email sent by this system: skip messages whose body starts with "LinkedIn post for").
   - Ignore replies from any other sender.
   - Save the reply body to a temp file and run `python3 -m engine decide $D --reply-file <file> --git`.
   - Result `unclear`: reply in the thread: "I couldn't tell if that's an approval. Reply APPROVE, SKIP, or APPROVE WITH EDIT + the full text." Don't publish.
   - Result `edit`: apply her requested changes to `final`, re-apply the Humanizer to the changed parts (her own wording stays as she wrote it), set `humanizer.applied` true, run `engine check`, and send a fresh approval email (same subject + " (revised)").

2. **07:00 run only**:
   - If still `pending` and `approval.reminder_sent_at` is empty: send a reminder email to both addresses ("Reminder: today's LinkedIn post goes out at 8:00 if you approve. Reply APPROVE / SKIP in the original thread.") with the post text. Then run `python3 -m engine mark $D reminded --git`.
   - If `python3 -m engine publish $D --dry-run` output contains `token_warning`, email it.
   - Don't publish at 07:00.

3. **08:00 and later**: publish with the method in `config/settings.json` → `publisher`.
   - `"zernio"` (default since 9 Nov 2026, supports images): run `python3 -m engine publish $D --git`. The engine uploads the image (if any) and publishes through Zernio with a fixed idempotency key, so a retry can never double-post.
   - `"api"` (backup: LinkedIn's official API, needs the developer-app token from docs/SETUP.md): set `publisher` to `"api"` and run `python3 -m engine publish $D --git`.
   - `"composio"` (text-only fallback): run `python3 -m engine publish $D --via composio --git`. If `result` is `ready_external`:
     1. Call Composio `LINKEDIN_CREATE_LINKED_IN_POST` **once** with account `composio.linkedin_account`, `author` = `composio.person_urn`, `commentary` = the returned `commentary` exactly, `visibility` PUBLIC, `lifecycleState` PUBLISHED.
     2. Success with a post URN → `python3 -m engine record $D published --urn <urn> --git`.
     3. Clear rejection (validation error, 4xx, auth) → `python3 -m engine record $D failed --error "<msg>" --git` (the next hourly run retries; auth errors → email Shweta to reconnect LinkedIn in Composio).
     4. Timeout or unclear response → `python3 -m engine record $D ambiguous --error "<msg>" --git` and email Shweta to check her profile. **Never call the post tool a second time in the same run.**
   Then act on `result`:

   | result | action |
   |---|---|
   | `published` | Email both: "Posted ✓ <url>". |
   | `already_published`, `too_early`, `weekend`, `skipped` | Nothing. |
   | `awaiting_approval` | At 11:00 only, email "Last call: today's post will be skipped at 12:00 unless approved". |
   | `expired` | Email "Today's post was skipped (not approved by 12:00). It stays in the backlog." |
   | `auth_failed` | Email: "LinkedIn connection expired. Reconnect LinkedIn in Zernio (Accounts → Reconnect), or, on the API route, docs/SETUP.md step 4". |
   | `needs_check` | Email **urgently**: "Outcome unknown. Please check your LinkedIn profile. If the post is there, reply POSTED <url>; if not, reply RETRY." Then handle her reply with `engine mark-published $D --url <url> --git` or `engine reset-publish $D --git`. |
   | `failed` | Email the error only if it's the 11:00 run or later (earlier runs will retry automatically). |
   | `quality_failed`, `config_missing`, `missing` | Email the message. |

4. **12:00 run only**: `python3 -m engine fetch-analytics --git` (impressions, reach, reactions, comments, shares, saves for posts from the last 30 days, via Zernio).

5. Never edit `publish_status` by hand, and never call LinkedIn directly.
