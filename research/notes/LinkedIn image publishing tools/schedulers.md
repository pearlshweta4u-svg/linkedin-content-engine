# Mainstream schedulers: programmatic image posts to a personal LinkedIn profile (as of 9 Nov 2026)

Method note: this session's network blocked direct page fetches (buffer.com and developers.buffer.com both failed DNS, so other vendor sites were not attempted). All findings below come from web-search result summaries plus one live Composio tool-catalog lookup (`COMPOSIO_SEARCH_TOOLS`, 9 Nov 2026). No vendor pricing page or API reference was read in full, so every price and plan gate should be checked on the vendor page before buying. Several third-party pricing pages contradict each other; conflicts are flagged.

## 1. Personal profile and image-post support

### Takeaway
Most of the tools say they support LinkedIn personal profiles, and Publer, Hootsuite and Ordinal say outright that they support image posts. Personal-profile posting uses LinkedIn's self-serve `w_member_social` permission, so supporting it is easy for vendors. The open question for each tool is whether the API exposes image posts, not whether the web app does.

### Cited Findings
- Publer: LinkedIn Profiles and Pages are both supported, and the plans page counts "LinkedIn Profile Posts" separately from "Page Posts". Supported LinkedIn types: status updates, links, single photo, multi-photo (up to 9), video. No polls or articles. — [Publer LinkedIn integration](https://publer.com/integrations/linkedin); [Publer help: managing LinkedIn accounts](https://publer.com/help/en/article/managing-linkedin-accounts-on-publer-1c6hrwl); [Publer help: connect Profile and Pages](https://publer.com/help/en/article/how-to-connect-linkedin-profile-and-pages-1seoebz/)
- Hootsuite: raised the per-post LinkedIn image limit from 9 to 20 "for both company and personal profiles" (in the app). — [Hootsuite What's New](https://www.hootsuite.com/whats-new/upload-up-to-20-images-to-your-linkedin-post)
- Later: supports LinkedIn Pages and profiles. Video scheduling only works for Company Pages, multi-photo carousels can't be scheduled through the API, and you can't tag people or companies. — [Later help](https://help.later.com/hc/articles/360063905933); [Later LinkedIn scheduler](https://www.later.com/linkedin-scheduler)
- Metricool: sources disagree on whether personal profiles connect. An older Metricool page lists "LinkedIn personal or company page (only available on Premium plans)", while a third-party review says the pricing page doesn't say which LinkedIn account types are supported. LinkedIn isn't on the Free plan (Starter or above). — [Metricool plans explained](https://metricool.com/premium-vs-free-metricool-plans); [upload-post Metricool pricing (verified 17 Sep 2026)](https://www.upload-post.com/metricool-pricing/)
- Ordinal: a LinkedIn-first scheduler. Its API/MCP `create post` takes a `linked_in` object with `copy`, `profile_id`, and up to 20 `assets` (existing Ordinal asset IDs), plus poll and link-preview options. — Composio tool catalog, `ORDINAL_CREATE_POST` schema (live lookup 9 Nov 2026); [Ordinal homepage](https://tryordinal.com/)
- Typefully: LinkedIn is one of its supported platforms (with X, Mastodon, Threads, Bluesky). — [Typefully agent skill docs](https://skills.lc/typefully/agent-skills/typefully-agent-skills-skills-typefully-skill-md)
- Taplio: LinkedIn-only tool with scheduling and carousels. I found no clear confirmation of single-image posts through any integration. — [Taplio pricing](https://app.taplio.com/pricing)
- Buffer: LinkedIn is among the channels the API supports. — [Buffer resources: multi-platform posting APIs](https://buffer.com/resources/social-media-api-multi-platform-posting/)
- LinkedIn background: personal-profile posting uses `w_member_social` ("Share on LinkedIn"), which needs no partner review. Company Page posting needs the reviewed Community Management API. An image post takes three calls: initializeUpload, PUT the bytes, then create the post with the image URN. — [Zernio LinkedIn posting API guide](https://zernio.com/blog/linkedin-posting-api); [Schedulenchill](https://schedulenchill.com/blog/does-linkedin-have-an-api)

### Inferences
- Because personal-profile posting is self-serve on LinkedIn's side, all of these tools probably use the official LinkedIn API for it. Nothing I found suggests any of them use browser automation for publishing.
- For a solo coach, Later's limits (no video or carousels to profiles) don't matter much for single-image posts.

### Gaps
- No confirmation from SocialBee or Taplio pages of image posts to personal profiles (likely supported in the UI, not verified).
- Metricool personal-profile support is unresolved.

## 2. Public API or official MCP that can create or schedule a post WITH an image

### Takeaway
Ordinal and Typefully have the clearest documented API and MCP paths for image posts. Buffer's new API and MCP (May 2026, all plans including Free) is the cheapest, but image attachment is unclear: older docs say images had to be hosted URLs, and the Composio Buffer tool is text-only. Publer and Metricool have APIs on higher tiers with unverified image flows. For Hootsuite (Enterprise only), Later, SocialBee and Taplio I found no usable public API for this purpose.

### Cited Findings
**Buffer**
- Public GraphQL API launched 27 May 2026 at api.buffer.com, together with an official MCP server and a CLI, "on every plan, including Free". — [Buffer blog: API is open](https://buffer.com/resources/buffer-api-is-here/); [Product Hunt launch](https://www.producthunt.com/posts/1157197); [Buffer help: does Buffer have an API](https://support.buffer.com/article/859-does-buffer-have-an-api)
- `createPost` takes text, channelId and a mode (`addToQueue`, or `customScheduled` with `dueAt`). — [Postzen Buffer API guide](https://www.postzen.dev/blog/buffer-api)
- Images: a Buffer roadmap comment says an image has to be already hosted online (by URL) to be attached through the API. An older guide (about 222 days old, from the beta period) said there was "no image upload through the GraphQL API". I couldn't verify the current state. — [Buffer API roadmap](https://developers.buffer.com/roadmap); [Postzen Buffer API guide](https://www.postzen.dev/blog/buffer-api)
- A community MCP server built on Buffer's GraphQL API says it creates posts with images and LinkedIn metadata and uploads local images to Cloudflare R2 to get a hosted URL. That supports the "hosted URL needed" reading. — [Glama community Buffer MCP](https://glama.ai/mcp/servers/p1etv5uxmn)
- Composio's `BUFFER_PUBLISH_POSTS` tool accepts text, channel_ids, delivery_mode and due_at only, with no media field. — Composio tool catalog, live lookup 9 Nov 2026
- Older Zernio guide calls it "Public beta" (possibly stale). — [Zernio Buffer API](https://zernio.com/blog/buffer-api)

**Ordinal**
- REST API and MCP server launched 3 Feb 2026 (changelog 2.3). Posts can be created, updated, scheduled and managed, and analytics can be pulled. The MCP uses OAuth and the REST API uses a bearer key. — [Ordinal changelog 2.3](https://www.tryordinal.com/changelog/2-3-mcp-and-api-launch); [Ordinal API docs](https://docs.tryordinal.com/api/introduction.md); [Ordinal MCP docs](https://docs.tryordinal.com/mcp/introduction.md)
- "The Ordinal API is available on the Pro plan or higher." — [Ordinal API docs](https://docs.tryordinal.com/api/introduction.md)
- Composio has an `ordinal` toolkit with CREATE_POST (LinkedIn assets up to 20, by existing asset_id), SCHEDULE_POST, UNSCHEDULE_POST, LIST_PROFILES, LIST_POSTS, UPDATE_POST and GET_PROFILE_ANALYTICS. The search didn't return an asset-upload tool, so the image may have to be uploaded through Ordinal's REST API or UI first. — Composio tool catalog, live lookup 9 Nov 2026

**Typefully**
- API v2 (with an official MCP server; one source dates the launch to December 2025). Media flow: `POST /v2/social-sets/{id}/media/upload` returns a presigned upload URL, then `GET /v2/social-sets/{id}/media/{id}` checks status, and the media_id is attached to a draft. An "Upload Media by URL" tool is listed on Zapier's MCP. — [Obsidian-Typefully API features](https://dsebastien.github.io/obsidian-typefully/api-features.html); [Zapier MCP Typefully](https://zapier.com/ja/mcp/typefully); [Typefully MCP gist](https://gist.github.com/linuz90/55a666a181b23d8ab19552c0d3c1b2fe); [aiproductivity Typefully](https://aiproductivity.ai/pricing/typefully/)
- A competitor blog (OpenTweet, 17 Oct 2026) says every Typefully plan, Free included, comes with the API, MCP and agent access. — [OpenTweet Typefully pricing 2026](https://opentweet.io/blog/typefully-pricing-2026)

**Publer**
- The Publer API (create and schedule content, view posts, analytics) is on Business and Enterprise only, for "customers in good standing". Accounts must be connected in the dashboard first, because the accounts endpoint is read-only. The API has scopes for workspaces, accounts, posts and media. — [Publer help: what's in Business](https://publer.com/help/en/article/1c57hsq/); [Publer plans](https://publer.com/plans); [Blotato Publer review](https://www.blotato.com/blog/publer-pricing)
- I found no documentation of the API's media upload flow for LinkedIn profiles.

**Metricool**
- "The Metricool API is available only on Advanced and Custom plans." Metricool MCP is available on every plan, Free included, through OAuth. Clients that authenticate with an API key need Advanced. — [Metricool help: plans, add-ons and API access](https://help.metricool.com/plans-add-ons-and-api-access-explained-xux1u); [Blotato Metricool](https://www.blotato.com/blog/metricool-pricing)
- I didn't find documentation of whether the MCP can attach images to LinkedIn posts.

**Hootsuite**
- Third-party sources say public API access is custom Enterprise only. I found nothing from Hootsuite's developer portal. — [upload-post Hootsuite pricing (verified 17 Sep 2026)](https://www.upload-post.com/hootsuite-pricing/); [SocialPilot Hootsuite pricing 2026](https://www.socialpilot.co/blog/hootsuite-pricing)

**Later**
- A third-party blog (Postiv, Oct 2026) says Later has a public REST API. I couldn't confirm this against Later's own documentation. — [Postiv Later alternatives](https://postiv.ai/blog/later-alternatives)

**SocialBee**
- The public API docs require a login. There's third-party MCP access through Boost.space, but I found no official SocialBee MCP. — [xpay SocialBee agent-ready index](https://www.xpay.sh/agent-ready-index/socialbee-io/); [Boost.space SocialBee MCP](https://boost.space/integrations/socialbee/?view=mcp)

**Taplio**
- The pricing page mentions only a Zapier integration "for your CRM". There's a "Developers API" link in the site nav whose content I couldn't retrieve. The Zapier page shows LinkedIn image fields, but those belong to Zapier's LinkedIn app, not a Taplio action. — [Taplio pricing](https://app.taplio.com/pricing); [Zapier LinkedIn + Taplio](https://zapier.com/apps/linkedin/integrations/taplio)

### Inferences
- **Best fit for an automated Claude session:** Typefully (documented presigned media upload, official MCP, API reportedly on all plans) and Ordinal (full API and MCP with LinkedIn assets and analytics, already in Composio, but $235-265/mo).
- Buffer is the cheapest option if image attachment works through the official API or MCP with a public image URL. Our images live in `content/images/` in a git repo, so they would need a public URL (for example a raw GitHub URL from a public repo, or other hosting). That has to be tested before relying on Buffer.
- Every one of these tools adds a second scheduler between the engine and LinkedIn. That duplicates the locking and duplicate-prevention the repo already does in `python -m engine publish`.

### Gaps
- Buffer's current image support in the official API and MCP (by URL, by upload, or not at all) is unverified. This is the most important thing to check, at developers.buffer.com once the network allows it.
- Whether Ordinal's REST API can upload an asset (so the whole flow works without the UI) is unverified.
- Publer API and Metricool MCP image flows for LinkedIn profiles are undocumented in what I could reach.
- Whether Later and Taplio have public APIs is unverified.

## 3. Pricing (cheapest plan with API and LinkedIn; free tiers)

### Takeaway
Free or cheap API: Buffer (Free plan includes the API, 1 key, 3,000 requests per 30 days) and Typefully (API reportedly on all plans, Creator about $99/yr per an Oct 2026 source). Mid-range: Publer Business (roughly $10-21/mo per account, sources conflict), Metricool Advanced (about €43/mo, or about $53/mo annual). Expensive: Ordinal Pro ($235/mo annual, $265 monthly), Hootsuite Enterprise (custom). I found no INR prices.

### Cited Findings
- Buffer: API on every plan including Free. Free gives 1 API key and 3,000 requests per 30 days. — [Buffer help](https://support.buffer.com/article/859-does-buffer-have-an-api); paid tier prices not retrieved ([Blotato Buffer pricing 2026](https://www.blotato.com/blog/buffer-pricing) covers them).
- Typefully: Free plan, Creator $99/yr, Business $20 per social set, API, MCP and agent access on every plan (competitor blog, 17 Oct 2026; Typefully's pricing page loads with JavaScript and gives no change date). Older sources list Starter $8, Creator $19, Team $39/mo, or Creator $12.50/mo annual and Team $29-49. These are likely stale. — [OpenTweet](https://opentweet.io/blog/typefully-pricing-2026); [SocialRails Typefully pricing](https://socialrails.com/blog/typefully-pricing); [Toolradar](https://toolradar.com/tools/typefully/pricing)
- Publer: API from Business. Pricing is per social account. Business price conflicts: "$10/month, 1 account, 1 user" in one source, "$10/user/month" in another, and "$21/month Business" (vs $10 Professional) in a third. — [Publer help: plans and pricing](https://publer.com/help/en/article/15h4yqh/); [Socialk.it Publer](https://socialk.it/en/pricing/publer); [SocialRails Publer](https://socialrails.com/blog/publer-pricing)
- Metricool: Advanced from €43/mo ex-VAT (June 2026), about $53/mo annual (Aug 2026), $50/mo in older guides. MCP on Free, but Free doesn't include LinkedIn. — [Metricool help](https://help.metricool.com/plans-add-ons-and-api-access-explained-xux1u); [Mallary.ai (Aug 2026)](https://mallary.ai/alternatives/metricool-pricing); [upload-post](https://www.upload-post.com/metricool-pricing/)
- Ordinal: Starter $95/mo ($85 annual), Pro $265/mo ($235 annual), Enterprise custom. API on Pro and above. — [Ordinal pricing](https://tryordinal.com/pricing); [Ordinal API docs](https://docs.tryordinal.com/api/introduction.md)
- Hootsuite: no free plan. Tier names and prices conflict: Standard $99, Professional $199, Advanced $399 (verified 17 Sep 2026), against a March 2026 blog saying Professional was dropped and the starting price is $149. API is Enterprise only (custom quote). — [upload-post Hootsuite](https://www.upload-post.com/hootsuite-pricing/); [Schedulala Hootsuite 2026](https://schedulala.com/blog/hootsuite-pricing-worth-it-2026); [Fluxnote](https://fluxnote.io/guides/hootsuite-pricing-guide-2026)
- SocialBee: Bootstrap $29/mo (5 profiles) in one source, "from $24/mo" in another. API pricing isn't published. — [SocialBee pricing](https://socialbee.com:443/pricing); [xpay SocialBee pricing](https://www.xpay.sh/saas-pricing/socialbee-io/)
- Taplio: Starter $39/mo in one source, $39/$65/$199 tiers in another (Postiz comparison, unverified), and an older 2025 article says $49/mo with an unresolved "verify" note. — [TrustRadius](https://www.trustradius.com/products/taplio/reviews); [Postiz compare](https://postiz.com/compare/taplio/upload-post); [getfuzzy](https://getfuzzy.ai/blog/taplio-pricing)
- Later: API pricing not found.

### Inferences
- For a solo coach with one LinkedIn profile, the cost of API access ranks roughly: Buffer Free ($0) < Typefully (about $0-99/yr) < Publer Business (about $10-21/mo) < Metricool Advanced (about $50/mo) < Ordinal Pro ($235+/mo) < Hootsuite Enterprise.

### Gaps
- No INR pricing found for any tool.
- Typefully's current plan gating for the API needs confirming on typefully.com (the main source is a competitor).
- Buffer paid-tier prices and whether the free plan caps channels or queue size were not retrieved.

## 4. Analytics for personal LinkedIn posts (in-app and via API)

### Takeaway
Personal-profile analytics are limited across the industry because of LinkedIn's API. LinkedIn's Member Post Analytics API is now open to a small set of approved vendors. Ordinal exposes LinkedIn profile post performance through its API and MCP. Publer says its profile analytics are limited. Buffer's API (through Composio) avoids analytics fields. Typefully LinkedIn analytics are reported as not available.

### Cited Findings
- LinkedIn's Member Post Analytics API is available to Later and ten other vendors, with no fee to LinkedIn and a free approval form. — [Digiday](https://digiday.com/media/linkedin-makes-it-easier-for-creators-to-track-performance-across-platforms)
- Ordinal: the API and MCP pull analytics (follower growth, post performance). Composio's `ORDINAL_GET_PROFILE_ANALYTICS` returns "follower history or post performance for one connected LinkedIn or X scheduling profile". Whether impressions are included isn't stated. — [Ordinal MCP docs](https://docs.tryordinal.com/mcp/introduction.md); Composio tool catalog, live lookup 9 Nov 2026
- Publer: "for LinkedIn profiles we are limited on the analytics we show, due to API limitations from LinkedIn". Profile analytics track connections, post engagement and best times. The API advertises "track analytics insights". — [Publer help](https://publer.com/help/en/article/managing-linkedin-accounts-on-publer-1c6hrwl); [Publer plans](https://publer.com/plans)
- Buffer: Composio's BUFFER_LIST_POSTS is described as listing posts "without requesting OAuth-inaccessible analytics fields", which suggests analytics aren't available through OAuth API access. — Composio tool catalog, live lookup 9 Nov 2026
- Typefully: one comparison says X analytics only and "LinkedIn analytics not yet available". No source confirms otherwise. — [Kleo Typefully review](https://kleo.so/blog/typefully-review)

### Inferences
- If impressions and reactions per post matter, Ordinal or a vendor on LinkedIn's Member Post Analytics list (Later is named) is most likely to provide them. Buffer, Typefully and Publer probably give little or no impression data for personal profiles through their APIs.

### Gaps
- The full list of the 11 vendors with Member Post Analytics access wasn't found, so I can't tell which of Hootsuite, Metricool, Buffer etc. are on it.
- Metricool, Hootsuite, SocialBee and Taplio personal-profile analytics not verified.

## 5. Official LinkedIn integration vs unofficial; setup effort

### Takeaway
Every tool in scope appears to publish through LinkedIn's official API with OAuth. None was reported to use browser automation for publishing. Setup for any of them means connecting the LinkedIn profile once in the vendor's web UI (OAuth), then creating an API key or doing an MCP OAuth. Accounts can't be connected through the API (Publer says so explicitly), so the first setup is always manual.

### Cited Findings
- Third-party statement that LinkedIn's official API with OAuth "is the same mechanism Buffer or Hootsuite use". — [Ayrshare LinkedIn API](https://www.ayrshare.com/linkedin-api.md)
- Later says it connects through LinkedIn's API and that its restrictions come from that API. — [Later help](https://help.later.com/hc/articles/360063905933)
- Taplio "uses LinkedIn's official API for all automation features" (aggregator claim). — [aitoolsatlas Taplio](https://aitoolsatlas.ai/tools/taplio)
- Publer: accounts must be connected in the dashboard, and the accounts API is read-only. — [Blotato Publer review](https://www.blotato.com/blog/publer-pricing)
- Ordinal MCP uses OAuth and the REST API uses a bearer key. It's available in Composio. — [Ordinal MCP docs](https://docs.tryordinal.com/mcp/introduction.md); Composio live lookup
- Buffer: one API key on Free, official MCP. — [Buffer help](https://support.buffer.com/article/859-does-buffer-have-an-api)
- In this session's Composio account, a `linkedin` toolkit is already connected. The `ordinal` and `buffer` toolkits are not. — Composio tool catalog, live lookup 9 Nov 2026

### Inferences
- In a cloud session, the simplest path is an API key stored as a network secret for the vendor's API host (the same pattern the repo uses for api.linkedin.com), or a remote MCP added with OAuth.
- Any scheduler would bypass `python -m engine publish` (CLAUDE.md non-negotiable 4: publish only through the engine, never call the LinkedIn API another way). Adopting one would mean either changing that rule or wrapping the vendor API inside the engine's publish command so it keeps the locking and duplicate prevention.

### Gaps
- Whether any of these tools is a formal LinkedIn Marketing Developer Platform partner wasn't verified from LinkedIn's partner directory.
- Hootsuite, Metricool and SocialBee OAuth details for personal profiles weren't confirmed from primary sources.
