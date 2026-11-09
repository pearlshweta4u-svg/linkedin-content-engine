# TrainWithShweta: LinkedIn content engine

Writes, humanizes, gets approval for, and publishes one LinkedIn post every weekday at **08:00 IST** for Shweta Mehta.

```
19:00 IST (day before)          07:00 IST            08:00–12:00 IST (hourly)
 Claude scheduled run  ─────►  reminder if not  ─►  read reply ─► publish via official
 • pick topic (history-aware)   approved             LinkedIn API (once, locked)
 • research (Thu/Fri required)                       ─► email link / alerts
 • draft → Humanizer → quality gate                  12:00 not approved → skipped
 • email for approval
```

| Day | Content |
|---|---|
| Mon | Personal story |
| Tue | Client story (anonymized, verified outcomes only) |
| Wed | Educational |
| Thu | Save-worthy (current, researched) |
| Fri | Health & wellness (credible sources) |

- **Mode:** approval (default). Auto-publishing only after Shweta explicitly enables it.
- **State:** `content/posts/*.json`, one record per slot, committed to git (an SQLite index is built from them for queries).
- **Secrets:** none in the repo. The LinkedIn token lives in the cloud environment's secret store.

Docs: [Setup](docs/SETUP.md) · [Operations & recovery](docs/OPERATIONS.md) · [LinkedIn API findings](docs/LINKEDIN_API.md) · [To-do](docs/TODO.md) · [Claude instructions](CLAUDE.md)
Knowledge base: [`knowledge/`](knowledge/)
