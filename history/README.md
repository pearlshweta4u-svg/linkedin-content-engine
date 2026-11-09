# Past LinkedIn posts (for analysis)

Source: LinkedIn's official data export (no scraping).
- `posts.json`: every past post with date, link, full text, hook (first line), word count and image links.
- `images/`: images downloaded from those posts (`<yyyymmdd>-<n>-<k>.<ext>`).

Load or refresh with:

    python3 -m engine import-history <path to the LinkedIn export ZIP or folder>

Why not Zernio or the LinkedIn API? For personal profiles, LinkedIn's API only exposes posts
published through that app. Zernio confirmed 0 readable past posts on 9 Nov 2026.
