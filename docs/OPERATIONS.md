# Operations and recovery

## Everyday (by email)
| You want to… | Do this |
|---|---|
| Approve a post | Reply `APPROVE` |
| Approve with your own wording | Reply `APPROVE WITH EDIT`, then paste the full post |
| Ask for changes | Reply `EDIT`, then paste the full post or describe the changes; a revised version comes back |
| Skip a day | Reply `SKIP` |

Approvals are accepted until 12:00 IST on the day (checked hourly). After that the slot is skipped.

## Pause / resume / mode (say it in a Claude session, or run it)
```bash
python3 -m engine mode pause --git
```
```bash
python3 -m engine mode resume --git
```
```bash
python3 -m engine mode approval --git
```
Automatic publishing needs your explicit go-ahead, recorded as:
```bash
python3 -m engine mode auto --confirmation SHWETA-CONFIRMED-AUTO --git
```
In auto mode, posts that pass every quality check publish at 08:00 without approval. You still get the evening email and can reply `SKIP`.

## Status, history, analytics
```bash
python3 -m engine status --last 10
```
```bash
python3 -m engine history
```
Enter LinkedIn numbers weekly (from the post's analytics view), until API access exists:
```bash
python3 -m engine analytics 2026-11-10 --impressions 1840 --reactions 42 --comments 9 --reposts 2 --git
```

## Failure handling (built in)
| Situation | What happens |
|---|---|
| Server restart / session dies / missed hourly run | State is in git, so the next run (hourly until 12:00) picks up. Nothing is double-posted: `published` and `publishing` are checked first. |
| LinkedIn 429 / 502 / 503 / 504 | Retried with backoff in the same run, then retried by the next hourly run. |
| Timeout or 500 *while creating the post* | Marked `needs_check`; you get an urgent email; **never auto-retried** (it may have posted). Resolve with `engine mark-published <date> --url <url>` or `engine reset-publish <date>`. |
| Run crashed mid-publish (stale `publishing` lock) | Next run converts it to `needs_check` and emails you. |
| Token expired / 401 / 403 | `auth_failed` email with the reconnect steps. The post can still go out the same morning once you reconnect. |
| Quality gate fails | No publish; email with the reasons. |
| Git push of the lock fails | Publish aborts before calling LinkedIn. |
| Fathom / research unavailable | The generator uses only the knowledge base; Thu/Fri without verifiable research → no post plus an email (no unsourced health content). |

## Manual publishing fallback (if API access isn't set up)
Each evening email contains the final text. Copy, paste into LinkedIn at 8:00, then reply `POSTED <url>` so the record is kept.

## Yearly maintenance
- Bump `linkedin.api_version` in `config/settings.json` to a version from the last ~6 months (see the LinkedIn versioning page). Run `python3 -m engine publish <next date> --dry-run` and a `whoami` check.
- Review `knowledge/` quarterly: new client stories, changed offers, new credentials.
