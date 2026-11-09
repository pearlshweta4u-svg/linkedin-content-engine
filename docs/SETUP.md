# Setup (Shweta's steps are marked 👤)

> **Primary publisher: Zernio** (since 9 Nov 2026). Your LinkedIn (personal, `linkedin.com/in/shwetam`) is connected in Zernio; its API key is stored as a network secret for zernio.com on the `linkedin-content-engine` cloud environment. Zernio publishes image posts and returns analytics for personal posts. If LinkedIn disconnects, reconnect it in Zernio when the engine emails you.
> **Backup: LinkedIn official API** (steps 1–4 below; set `publisher` to `"api"` to switch). **Text-only fallback:** Composio.

## 1. 👤 LinkedIn Company Page (skip if you have one), ~5 min
LinkedIn → **For Business** (top right) → **Create a Company Page** → Company → name "TrainWithShweta", URL `trainwithshweta`, logo optional → Create.

## 2. 👤 LinkedIn developer app, ~5 min
1. Go to https://www.linkedin.com/developers/apps → **Create app**.
2. Fill in: App name "TrainWithShweta Publisher"; LinkedIn Page: the page from step 1; Privacy policy URL: your website (optional); App logo: any square image. Accept the terms → **Create app**.
3. **Settings** tab → *Verify* the app with the page (LinkedIn gives a link to click as the page admin).
4. **Products** tab → **Request access** for:
   - **Share on LinkedIn**
   - **Sign In with LinkedIn using OpenID Connect**

   Both are approved instantly.

## 3. 👤 Generate your access token, ~2 min
1. In the developer portal, go to **Docs and tools → OAuth Token Tools** (https://www.linkedin.com/developers/tools/oauth), then **Create token**.
2. Select your app and tick the scopes **openid**, **profile**, **w_member_social** → **Request access token** → sign in and **Allow**.
3. Copy the token. **Do not paste it in chat or email.**

## 4. 👤 Give the token to the engine (every ~60 days), ~1 min
In a Claude Code session on this repo, say **"connect LinkedIn"**. Claude opens a secure form (a "network secret" for `api.linkedin.com`). Paste the token there. Claude never sees it; the cloud proxy adds it to LinkedIn requests only.
Then Claude runs `python3 -m engine whoami --save` (stores your member URN, which isn't secret) and sets `linkedin.token_issued_on` to today.
*Reconnecting after 60 days: repeat steps 3 and 4.*

## 5. Scheduled tasks (Claude sets these up after you approve the samples)
| Task | When (IST) | Runbook |
|---|---|---|
| Generate tomorrow's post + email for approval | Sun–Thu 19:00 | `runbooks/generate.md` |
| Read approval, 7 AM reminder, publish, alerts | Mon–Fri hourly 07:00–12:00 | `runbooks/morning.md` |

Created as Claude scheduled tasks (cron with `CRON_TZ=Asia/Kolkata`), each firing a fresh cloud session with Gmail access. Because every state change is pushed to git, a restart or missed run loses nothing: the next hourly run catches up until the 12:00 deadline.

## 6. Local / developer use (optional)
```bash
git clone https://github.com/pearlshweta4u-svg/linkedin-content-engine && cd linkedin-content-engine
```
```bash
python3 -m unittest
```
```bash
python3 -m engine status
```
Python 3.10+, no dependencies. For local publishing, export `LINKEDIN_ACCESS_TOKEN` in your shell. Never commit it.
