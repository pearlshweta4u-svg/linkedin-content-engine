# API-first social publishing services for a personal LinkedIn profile (image posts), Nov 2026

Method note (read first): this session's network blocked direct page fetches to every vendor domain (ayrshare.com, getlate.dev, upload-post.com, blotato.com, unipile.com, postiz.com all failed DNS at the sandbox). Everything below comes from web-search results: search snippets and the search tool's summaries of vendor pages, vendor docs, GitHub issues and third-party reviews. I could not open any pricing page in full. Treat every price as "reported in search results, not verified on the live page today". Many comparison sources are competitors (Blotato, Upload-Post, Zernio, social-api.ai, PostEverywhere and others publish comparisons of each other), so they carry commercial bias.

## Summary comparison table

| Service | Personal LinkedIn profile | Image via API | LinkedIn connection method | REST API / MCP | Lowest plan with API + LinkedIn (USD, monthly) | Free tier | Personal-profile analytics via API |
|---|---|---|---|---|---|---|---|
| Ayrshare | Yes (changelog references personal profiles) | Yes (core feature; details not re-verified) | Official LinkedIn OAuth (re-link flow grants scopes) | REST yes; MCP not confirmed in my sources | Premium ~$149/mo, 1 profile | No permanent free plan; 28-day trial (third-party) | Yes, expanded set after re-link; lags 24-48 h |
| Late, now Zernio | Yes ("personal & company pages") | Yes (not re-verified) | Official OAuth (third-party review) | REST yes; hosted MCP yes | Per-account: first 2 accounts free, then $6/account (3-10) | First 2 connected accounts free (as of Oct 2026) | Vendor says yes for posts published through Zernio |
| Upload-Post | Yes ("profiles and company pages") | Yes (image or video endpoint) | Vendor says approved LinkedIn integration (OAuth) | REST yes; MCP server yes | Basic $24/mo (unlimited uploads) | Free $0, 10 uploads/mo, LinkedIn included | Docs say NO (company pages only) |
| Blotato | Yes (personal + company pages) | Not specifically confirmed in my sources | Not confirmed in my sources | REST yes; hosted MCP at mcp.blotato.com/mcp | Starter $29/mo (20 accounts) | 7-day trial, but trial excludes API/MCP | No; analytics excludes LinkedIn |
| Unipile | Yes, acts as the member's own session | Yes, `attachments` on Create a post (multipart) | Session/cookie (li_at) or username/password or UniLogin extension: NOT official LinkedIn API | REST yes; MCP not found | ~EUR 49 (~$55)/mo minimum, covers up to 10 accounts (third-party) | Not confirmed | Not found for this use |
| Postiz cloud | Supported channel "LinkedIn" (separate from "LinkedIn Page") | Yes, `/public/v1/upload` and `/upload-from-url` | Official OAuth (Postiz's app on cloud) | Public REST API on every plan; agent/CLI skill; community MCP | ~$29/mo monthly (~$23 annual) | No permanent free tier; 7-day trial | No (Pages only), open feature request #1680 |
| Postiz self-hosted | Same as cloud, with your own LinkedIn app | Same as cloud | You register your own LinkedIn developer app + OAuth keys | Same as cloud | $0 software (AGPL-3.0) + server costs | n/a | No (same codebase) |

## 1. Personal profile support and image / multi-image posts

### Takeaway
All six can publish to a personal LinkedIn profile per their own material. Image posting via API is explicitly documented in my sources for Upload-Post, Unipile and Postiz. For Ayrshare, Zernio and Blotato image support is implied by the product but I could not open the docs to confirm the exact field (URL vs upload). Carousel/multi-image details were only found for Upload-Post (third-party claim).

### Cited Findings
- Late/Zernio's LinkedIn page is titled "LinkedIn API Integration - Post to Personal & Company Pages" and says you can post to LinkedIn programmatically without the Marketing API Partner Program — [getlate.dev/linkedin](https://getlate.dev/linkedin)
- Late was rebranded to Zernio in 2026; the old getlate.dev domain redirects to zernio.com — search summary of [PostEverywhere vs Zernio](https://posteverywhere.ai/blog/posteverywhere-vs-zernio) and [Zernio changelog](https://zernio.com/changelog/simplified-pricing-plans-for-late-api-users)
- Zernio: a profile or a company page counts as one connected account — [Zernio LinkedIn MCP page](https://zernio.com/linkedin-mcp)
- Upload-Post's LinkedIn endpoint "publishes your video or image to the connected LinkedIn profile or company page"; one API covers images and video — [Upload-Post LinkedIn platform page](https://www.upload-post.com/platforms/linkedin/)
- Upload-Post supports up to 20 images per LinkedIn post, per a third-party comparison whose other numbers conflict with Upload-Post's own pages (11 vs 22 platforms), so treat with caution — search summary of [Upload-Post pricing comparison](https://www.upload-post.com/pricing-comparison/) / [Zernio blog](https://zernio.com/blog/social-media-posting-api)
- Blotato can post to LinkedIn personal profiles plus company pages — [Blotato AI info page](https://www.blotato.com/ai-info); [scheduler.social review](https://scheduler.social/schedulers/blotato)
- Unipile "Create a post" reference lists an `attachments` parameter (array of files) and notes LinkedIn image resolution max 6012 x 6012 px; LinkedIn-only fields include `external_link` — [Unipile API reference: Create a post](https://developer.unipile.com/reference/postscontroller_createpost)
- A Unipile guide shows create-post as a `multipart/form-data` POST (its path looks garbled); the Node SDK's LinkedIn example `client.users.createPost` only passes `account_id` and `text` — [Unipile blog](https://www.unipile.com/how-to-get-linkedin-posts-using-api/); [unipile-node-sdk](https://github.com/unipile/unipile-node-sdk)
- Postiz public API exposes `POST /public/v1/upload` and `POST /public/v1/upload-from-url` (a PR adds an optional "adjust to platform limits" flag and a media-processing status endpoint) — [Postiz PR #2281](https://github.com/gitroomhq/postiz-app/pull/2281)
- Postiz media limits: image 10 MB each, video 1 GB; platform rules are stricter — [Postiz docs: Images and video](https://docs.postiz.com/general/composer/media)
- Postiz lists "LinkedIn" and "LinkedIn Page" as separate channels (this session's own `postiz` skill description lists both).
- Ayrshare changelog refers to "personal LinkedIn profiles" (in the analytics context), confirming personal profiles are a supported account type — [Ayrshare Latest Updates](https://www.ayrshare.com/docs/whatsnew/latest)

### Inferences
- For a one-image-per-weekday pipeline, every service here meets the basic requirement; the differentiators are connection method, cost and analytics.
- Upload-Post and Postiz are the two where an image-by-URL path is documented in my sources (Postiz `upload-from-url`; Upload-Post accepts image to its LinkedIn endpoint). That fits a pipeline where images live in the repo and could be served from a public URL, or uploaded as multipart.

### Gaps
- Exact image-field formats (URL vs multipart vs pre-upload) for Ayrshare, Zernio and Blotato: vendor docs could not be fetched.
- Multi-image / carousel (LinkedIn document/PDF carousel vs multi-image) support per service was not confirmed except the Upload-Post third-party claim.

## 2. How each connects to LinkedIn (official OAuth vs session/cookie automation)

### Takeaway
Ayrshare, Zernio, Upload-Post, Blotato (probably) and Postiz use LinkedIn's official OAuth/API. Unipile is the outlier: it links the member's own LinkedIn session (li_at cookie, or username/password, or its UniLogin extension). That is not LinkedIn's official API and carries ToS/restriction risk; it is a bad fit for a coach's main personal account.

### Cited Findings
- Unipile cookie linking reuses an existing browser session; the `li_at` cookie is the key credential (`li_a` for premium products). It also supports username/password and a UniLogin extension; docs recommend sending the browser user agent with the cookie to prevent disconnection — [Unipile docs: Link accounts](https://developer.unipile.com/v2.0/docs/linkedin-link-accounts); [Unipile LinkedIn guide](https://developer.unipile.com/docs/linkedin)
- Unipile material says logging in via Unipile with LinkedIn credentials "may trigger a warning from LinkedIn" (Recruiter context) — search summary of [Unipile LinkedIn guide](https://developer.unipile.com/docs/linkedin)
- A 2026 third-party review says Unipile states "We don't enforce any limits on our side" and that exceeding LinkedIn's limits can bring errors or a restriction; pacing is the developer's job. This conflicts with Unipile/partner marketing that says its infrastructure helps prevent restrictions — [LinkupAPI Unipile review](https://linkupapi.com/blog-articles/unipile-review) vs [omentir.com blog](https://omentir.com/blogs/unipile-safe-linkedin-api)
- Unipile's own comparison describes acting "through a LinkedIn account that the end user connects" — [Unipile: Best LinkedIn API 2026](https://www.unipile.com/best-linkedin-api/)
- Zernio connects to LinkedIn through official OAuth covering publishing, analytics and comments (no connection requests/DMs) — third-party review summarised in search, [Zernio review (lokeshkapoor.com)](https://lokeshkapoor.com/blog/zernio-review)
- Upload-Post says it holds an approved LinkedIn integration so you connect profile and pages without applying for LinkedIn API review yourself — [Upload-Post LinkedIn API guide](https://www.upload-post.com/linkedin-api/)
- Ayrshare's error docs say re-linking grants the required member analytics scopes (an OAuth scope-consent flow) — [Ayrshare Error Codes](https://www.ayrshare.com/docs/errors/errors-ayrshare)
- Blotato's guide argues a unified layer skips LinkedIn's partner queue (vendor claim) — [Blotato: LinkedIn API pricing guide](https://www.blotato.com/blog/linkedin-api-pricing)
- Self-hosted Postiz needs your own OAuth keys/app for each platform including LinkedIn — [Grok post on X](https://x.com/grok/status/2044019782354100551) (weak source; corroborated by the general self-hosting notes in [Postiz pricing review](https://filipkonecny.com/blog/postiz-pricing/))

### Inferences
- The repo's CLAUDE.md says publishing must go only through `python -m engine publish`, which calls the LinkedIn API. Any of the OAuth-based services would replace or sit behind that call; Unipile would introduce session-based automation of the personal account, which is the riskiest option for Shweta's main business profile.
- Self-hosted Postiz with a self-registered LinkedIn app would only get the self-serve products (Share on LinkedIn / Sign In with OpenID Connect), so personal posting works but member analytics (Community Management API, partner-gated) would not. This is from general knowledge of LinkedIn's product tiers, not a source fetched today.

### Gaps
- Blotato's LinkedIn connection mechanism was not stated in any source I reached (assumed OAuth, unverified).
- No primary statement from LinkedIn on Unipile specifically.

## 3. Public REST API / MCP and auth

### Takeaway
All six have a REST API. Hosted MCP servers are documented for Zernio, Upload-Post and Blotato; Postiz has an official agent/CLI skill plus community MCP; Ayrshare and Unipile MCP were not confirmed. Auth is API key (bearer) across the board per general docs; Blotato ends the trial when you generate an API key.

### Cited Findings
- Zernio offers a hosted LinkedIn MCP server for posting and analytics; reviews disagree on tool count (about 50 visible tools vs "over 280") — [Zernio LinkedIn MCP](https://zernio.com/linkedin-mcp); [humantestsai review](https://humantestsai.net/tools/zernio/)
- Upload-Post has an MCP server for ChatGPT/Claude/Cursor exposing tools including `get_analytics`, `get_total_impressions`, `get_post_analytics`, `get_platform_metrics` — [Upload-Post MCP guide](https://docs.upload-post.com/guides/mcp-server-integration/); [Upload-Post LinkedIn MCP](https://www.upload-post.com/mcp/linkedin/)
- Blotato: hosted MCP at `mcp.blotato.com/mcp`; API and MCP access included in every paid plan, no separate API tier; the 7-day trial excludes API/MCP and generating an API key ends the trial and starts the paid plan — [Blotato AI info](https://www.blotato.com/ai-info); [thatmarketingbuddy MCP page](https://thatmarketingbuddy.com/mcp/blotato)
- Postiz: every plan includes a public REST API (create posts, upload media, manage channels) plus webhooks — search summary of [Postiz home](https://postiz.com/) and reviews
- Postiz public API rate limit: 90 create-post requests per hour (current limits page); older public-API page and blog still say 30/hour; one request can carry many posts — [Postiz docs: Limits](https://docs.postiz.com/cloud/limits) vs [Postiz Public API docs](https://docs.postiz.com/public-api)
- Third-party analysis: `API_LIMIT` env var defaults to 90 (cloud set to 100) and only counts create-post, not uploads — search summary of [Blotato: Postiz vs Upload-Post](https://www.blotato.com/blog/postiz-vs-upload-post) (unverified in Postiz docs)
- Community Postiz MCP server and CLI with `postiz upload` — [lobehub: Postiz MCP Server & CLI](https://lobehub.com/mcp/antoniolg-postiz-mcp)
- Ayrshare maintains a public GitHub repo for its Social Media API — [ayrshare/social-media-api](https://github.com/ayrshare/social-media-api)
- Unipile has REST API reference and a Node SDK; an n8n create-post guide exists — [Unipile n8n guide](https://developer.unipile.com/docs/createpost-request-n8n)

### Inferences
- A scheduled Claude cloud session can call any of these via HTTPS with an API key; the key should be a network secret on the environment (like the current LinkedIn token), and the vendor's API host must be added to the allowed hosts. In this very session, none of the vendor domains resolved, so the environment would need those hosts allowed.
- At one post per weekday, Postiz's 90/hour limit is irrelevant.

### Gaps
- Ayrshare MCP availability and Unipile MCP availability not found.
- Exact auth header formats not verified on live docs.

## 4. Pricing (lowest plan with API + LinkedIn) and free tiers

### Takeaway
Cheapest workable options for one personal profile: Zernio (first 2 accounts free, as of Oct 2026), Upload-Post (free 10 uploads/mo is too few for ~22 weekday posts; Basic $24/mo), self-hosted Postiz ($0 + hosting), Postiz cloud (~$29/mo), Blotato ($29/mo). Ayrshare is the most expensive (~$149/mo). Unipile ~EUR 49/mo minimum. No INR prices found.

### Cited Findings
- Ayrshare: Premium $149/mo for 1 profile; Launch $299 for up to 10; Business $599/mo for 30. A SaaSWorthy $24.99 figure conflicts and looks outdated — search summary of [Ayrshare pricing](https://www.ayrshare.com/pricing/); [SaaSWorthy](https://www.saasworthy.com/product/ayrshare/pricing)
- Ayrshare: no permanent free plan; 28-day trial; legacy Basic plan closed to new sign-ups — [social-api.ai Ayrshare pricing 2026](https://social-api.ai/blog/ayrshare-pricing-social-media-api-2026); [heytasky](https://heytasky.com/tools/ayrshare/) (both third-party; social-api.ai is a competitor)
- Zernio: first 2 connected accounts free, accounts 3-10 $6 each, 11-100 $3 each, 101+ $1 each, "as of October 2026"; monthly billing only — search summaries of [thatmarketingbuddy Zernio pricing](https://thatmarketingbuddy.com/pricing/zernio) and [Upload-Post: Ayrshare vs Zernio vs Blotato](https://www.upload-post.com/ayrshare-vs-zernio-vs-blotato/)
- Conflict: older Zernio/Late flat plans (Free, Boot $13/mo, Accelerate $33/mo) from a changelog about 349 days old; and a "From $29/month" headline on thatmarketingbuddy — [Zernio changelog](https://zernio.com/changelog/simplified-pricing-plans-for-late-api-users); [thatmarketingbuddy](https://thatmarketingbuddy.com/pricing/zernio). Current model is unclear; verify live.
- Upload-Post: Free $0 (10 uploads/mo), Basic $24, Professional $50, Advanced $147, Business $438 per month monthly billing; paid plans unlimited uploads, all platforms, scheduling and analytics; LinkedIn available from Free — [Upload-Post docs: Pricing & Limits](https://docs.upload-post.com/resources/pricing-and-limits); [Upload-Post home](https://www.upload-post.com/#pricing)
- Blotato: Starter $29/mo (20 accounts), Creator $97 (40), Agency $499 (100); ~17% annual saving; API/MCP on every paid plan — [PlugKit Blotato pricing](https://www.plugkit.co/blog/blotato-pricing-api-alternatives/); [scheduler.social](https://scheduler.social/schedulers/blotato)
- Unipile: minimum about EUR 49 (~$55)/mo covering up to 10 accounts; per-account rate steps down with volume; no per-request fees; billed post-paid on peak connected accounts per 30 days. Sources disagree on exact tiers and currency — [gtm-api Unipile overview](https://gtm-api.com/unipile-overview/); [LinkupAPI](https://linkupapi.com/blog-articles/linkedin-api-pricing); [Linked API vs Unipile](https://linkedapi.io/vs/unipile)
- Postiz cloud: about $29-$99/mo monthly ($23-$79 annual); 7-day trial; no permanent free hosted tier. Self-hosted is AGPL-3.0, free software, needs your own server/Docker and platform API approvals — [schedulenchill](https://schedulenchill.com/postiz-vs-schedule-and-chill); [filipkonecny Postiz pricing](https://filipkonecny.com/blog/postiz-pricing/); [makerstack](https://makerstack.co/reviews/postiz-review/)

### Inferences
- ~22 weekday posts/month exceeds Upload-Post's free 10 uploads, so Basic ($24) is the realistic floor there.
- If Zernio's "first 2 accounts free" is current, a single personal profile could cost $0 in platform fees, but whether the free accounts include API and analytics was not confirmed.

### Gaps
- No INR pricing found for any vendor.
- All prices are from search results; none of the live pricing pages could be opened today (9 Nov 2026). Zernio's model in particular has conflicting sources.

## 5. Analytics for personal LinkedIn posts via API

### Takeaway
LinkedIn launched the Member Post Analytics API (r_member_postAnalytics, Community Management API, partner-gated) in July 2025. Ayrshare clearly supports personal-profile analytics after a re-link. Zernio claims stats for posts published through it. Upload-Post's docs say company pages only; Blotato excludes LinkedIn from analytics; Postiz has Pages only (personal analytics is an open feature request).

### Cited Findings
- LinkedIn announced the Member Post Analytics API on 8 July 2025 — [PPC Land](https://ppc.land/linkedin-enables-third-party-analytics-access-with-new-member-post-api/)
- LinkedIn's Member Post Statistics docs: Community Management API partners can retrieve IMPRESSION, MEMBERS_REACHED, REACTION, COMMENT, RESHARE — [Microsoft Learn: Member Post Statistics](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/members/post-statistics?view=li-lms-2026-09)
- Personal analytics require the `r_member_postAnalytics` scope; accounts connected before the scope was added must reconnect — [trypost issue #377](https://github.com/trypostit/trypost/issues/377); [postiz issue #1680](https://github.com/gitroomhq/postiz-app/issues/1680)
- Ayrshare: personal LinkedIn profiles return an expanded analytics set but existing accounts must re-link; until then analytics calls return error 475; posting unaffected; data lags LinkedIn by 24-48 h; 475 can persist 5-10 min after re-link — [Ayrshare Latest Updates](https://www.ayrshare.com/docs/whatsnew/latest); [Ayrshare Error Codes](https://www.ayrshare.com/docs/errors/errors-ayrshare); [Ayrshare Analytics on a Social Network](https://www.ayrshare.com/docs/apis/analytics/social)
- An older Ayrshare blog post says personal-page metrics are unavailable; predates the 2025 API and is outdated — [Ayrshare blog](https://www.ayrshare.com/blog/how-to-post-and-get-analytics-with-the-linkedin-api/)
- Zernio: for personal profiles LinkedIn only returns stats on posts published through Zernio; analytics calls cost nothing extra — search summary of [Zernio LinkedIn MCP](https://zernio.com/linkedin-mcp) (vendor claim)
- Upload-Post Analytics API: LinkedIn analytics only for organization/company pages; personal profiles not supported. Its MCP examples hint otherwise (conflict) — [Upload-Post Analytics API](https://docs.upload-post.com/api/get-analytics/)
- Blotato: analytics excludes LinkedIn — [Blotato AI info](https://www.blotato.com/ai-info)
- Postiz docs: LinkedIn analytics available for Pages, not personal profiles; issue #1680 requests personal analytics via memberCreatorPostAnalytics, no merge found — [Postiz docs: Analytics](https://docs.postiz.com/general/analytics); [Issue #1680](https://github.com/gitroomhq/postiz-app/issues/1680)
- WoopSocial says no analytics for personal profiles — [WoopSocial LinkedIn MCP](https://woopsocial.com/social-media-mcp/linkedin-mcp)

### Inferences
- If post analytics feeding back into the content engine matters, Ayrshare (verified docs) and Zernio (vendor claim) are the only candidates; the rest would need manual export from LinkedIn.

### Gaps
- Unipile analytics for own posts not researched/confirmed.
- Zernio's personal analytics claim not independently verified.

## 6. Re-authentication (60-day tokens), reliability and setup effort

### Takeaway
I found no vendor statement giving a concrete re-auth interval for personal LinkedIn connections. Reliability reputations were not well-sourced. Setup effort: hosted services are minutes (OAuth connect + API key); self-hosted Postiz requires a server, Docker and your own LinkedIn developer app; Unipile requires cookie/credential capture.

### Cited Findings
- Search for Ayrshare + 60-day reconnect found no stated reconnect rule; only the analytics re-link requirement — search result summary over [Ayrshare docs](https://www.ayrshare.com/docs/whatsnew/latest)
- Unipile recommends capturing the user agent along with the cookie to help prevent account disconnection (sessions can drop) — [Unipile Link accounts](https://developer.unipile.com/v2.0/docs/linkedin-link-accounts)
- Self-hosted Postiz requires your own server, Docker setup and technical maintenance; platform API approvals can take over a month for Meta/YouTube — [filipkonecny Postiz pricing](https://filipkonecny.com/blog/postiz-pricing/); [schedulenchill](https://schedulenchill.com/postiz-vs-schedule-and-chill)
- Ayrshare has a G2 review listing and Software Advice listing (ratings not extracted) — [G2](https://www.g2.com/products/ayrshare-api/reviews); [Software Advice](https://www.softwareadvice.com/marketing/ayrshare-profile/)
- Late has a 4.0/5 rating on AppSumo — [AppSumo Late](https://appsumo.com/products/late/)

### Inferences
- LinkedIn member access tokens last 60 days; programmatic refresh tokens are generally only issued to approved partner apps (general knowledge, not fetched today). Vendors that are LinkedIn partners (Ayrshare, Zernio and Upload-Post claim approved integrations) can likely refresh silently; a self-hosted Postiz with a self-serve LinkedIn app would likely need a manual re-connect about every 60 days. Verify with each vendor.
- Whichever service is chosen, the pipeline should detect auth errors and email Shweta to reconnect, rather than retrying.

### Gaps
- Concrete re-auth intervals per vendor: not found.
- Independent reliability data (uptime, failed-post rates): not found; review sites found but ratings not extracted.
- Hosts to allow for live verification next time: www.ayrshare.com, getlate.dev / zernio.com, www.upload-post.com, docs.upload-post.com, www.blotato.com, help.blotato.com, www.unipile.com, developer.unipile.com, postiz.com, docs.postiz.com.
