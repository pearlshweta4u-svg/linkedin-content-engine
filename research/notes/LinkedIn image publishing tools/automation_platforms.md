# Workflow-automation platforms for LinkedIn personal-profile image posts (Zapier, Make, n8n, Pipedream), as of 9 Nov 2026

Method note: in this cloud session, direct page fetches to zapier.com, make.com, docs.n8n.io and pipedream.com were blocked by the network allowlist (DNS "ENOTFOUND"). Every finding below comes from web-search results: search snippets and summaries of official pages, community forums and third-party blogs. Nothing was read as a full page. Treat exact field names, prices and version numbers as "verify before relying on them". To check them first-hand, those four hosts need to be allowed in the session's network settings.

## 1. LinkedIn integration: can each platform post an image to a personal profile? Image by URL or by file?

### Takeaway
All four platforms have an action that posts an image to a personal (member) profile. Zapier's "Create Share Update" takes an image **URL**. Make's "Create a User Image Post" takes an image **file**. n8n's LinkedIn node takes **binary** data, and there was a 2026 breakage. Pipedream's "Create Image Post (User)" takes a **file path or URL**. Each platform also has separate company-page actions.

### Cited Findings
**Zapier**
- "Create Share Update" posts a status update to your personal LinkedIn profile. It can include text, URLs and images, and lets you set visibility. "Create Company Update" is a separate action for Company Pages and needs page-admin rights. — [Zapier Help: How to get started with LinkedIn on Zapier](https://help.zapier.com/hc/en-us/articles/8495987891853-How-to-get-started-with-LinkedIn-on-Zapier)
- A Zapier community thread names the image field "Content - Image URL" and calls LinkedIn's API through Zapier "notoriously finicky" for images. — [Zapier Community: attach image with linkedin post](https://community.zapier.com/how-do-i-3/attach-image-with-linkedin-post-51111)
- A third-party guide says to use a publicly reachable direct image URL, not a Zapier attachment or a restricted Dropbox link, and names the `w_member_social` scope for personal sharing. It is a secondary source. — [Mallary.ai: Zapier LinkedIn integration guide](https://mallary.ai/blog/zapier-linkedin-integration)

**Make**
- The LinkedIn app has "Create a User Image Post" (shares an image on the user's wall) next to user text and video post modules. "Create a Company Image Post" is the company-page version. — [Make: LinkedIn integration / help](https://www.make.com/en/help/app/linkedin); [Make template: company image post](https://www.make.com/en/templates/5064-create-a-linkedin-image-post-on-behalf-of-an-organization-from-a-new-twitter-post)
- A community answer says to map the post text to "Content" and the image file to "Image File" in "Create a User Image Post". This means a file or binary, usually downloaded first with an HTTP "Get a file" module. That last step is my inference. — [Make Community: text and image on a LinkedIn personal account](https://community.make.com/t/how-to-upload-text-image-together-in-linkedin-personal-account-using-make/86474)

**n8n**
- The built-in LinkedIn node creates posts as a Person or as an Organization. You attach an image by choosing Media Category "Image" and pointing to a **binary property**. — [n8n docs: LinkedIn node](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.linkedin/)
- Community reports: an image needs a separate binary download step, and binary-field naming errors are common. One template uses four nodes (three LinkedIn nodes plus a download node) for one image post. Posting as a person sometimes fails to fetch the person's name. — [n8n Community: LinkedIn post with image](https://community.n8n.io/t/linkedin-post-with-image/40515); [n8n Community: Error in image upload for LinkedIn](https://community.n8n.io/t/error-in-image-upload-for-linkedin/41916)
- **2026 breakage:** from about April to July 2026, the native node failed with `NONEXISTENT_VERSION 20250401` / HTTP 426 in n8n Cloud 2.15.x. The node sent an invalid LinkedIn-Version header. The suggested workaround was an HTTP Request node with OAuth2 and a valid `LinkedIn-Version` (YYYYMM). Reports conflict on whether updating n8n fixed it, and a fix was tracked in GitHub issue #28559. — [n8n Community: NONEXISTENT_VERSION 20250401](https://community.n8n.io/t/linkedin-node-fails-with-nonexistent-version-20250401-in-n8n-cloud-2-15-x/288332); [n8n Community: workaround using the HTTP node](https://community.n8n.io/t/linkedin-connection-issue-workaround-using-the-http-node/289794?tl=es)
- Community node `@xnkee/n8n-nodes-linkedin` does the image upload in one operation. Community nodes run on self-hosted n8n. Whether n8n Cloud allows unverified community nodes was not checked. — [pkgstats: @xnkee/n8n-nodes-linkedin](https://www.pkgstats.com/pkg:@xnkee/n8n-nodes-linkedin)

**Pipedream**
- Action "Create Image Post (User)", key `linkedin-create-image-post-user`, v1.0.9, write action. Inputs are an image (file path or URL) and post text. An older version needed the file to be in `/tmp`. There is a separate "Create Image Post (Organization)". — [Pipedream: Create Image Post (User)](https://pipedream.com/apps/linkedin/actions/create-image-post-user)

### Inferences
- For this repo, images are already in `content/images/`. Zapier needs those images at a public URL, so they would have to be hosted somewhere public, for example a raw GitHub URL if the repo is public, or object storage. Pipedream accepts a URL. Make and n8n need a file, which a public URL plus an HTTP download step can provide.
- All four platforms are thin wrappers over LinkedIn's member posting API (`w_member_social`). That is the same API `engine/` already calls directly, so none of them adds posting capability the engine lacks. What they offer is a hosted OAuth connection.

### Gaps
- I could not open the live action pages, so the current field names, image size and format limits, and whether multi-image posts are supported are unverified.
- I could not confirm that the n8n LinkedIn node is fixed as of Nov 2026.

## 2. Can Claude trigger it from outside (webhook, API, MCP)? Do Zapier MCP and Pipedream MCP expose LinkedIn create-post-with-image?

### Takeaway
Zapier MCP lists LinkedIn "Create Share Update" as a tool, and that action supports an image URL. Pipedream MCP exposes `linkedin-create-image-post-user`, but a July 2025 GitHub issue reports a 403 error when posting images through it, and I couldn't find whether it was fixed. Make (Custom Webhook or Make MCP on-demand scenarios) and n8n (Webhook node or MCP Server Trigger node) can both expose a workflow that Claude calls.

### Cited Findings
- Zapier's LinkedIn MCP page lists "Create Share Update" ("posts a status update sharing some content") as an available action. The same page says Zapier MCP does not currently enforce Enterprise app and action restrictions. — [Zapier MCP: LinkedIn](https://zapier.com/mcp/linkedin)
- Zapier MCP works with Claude, including Claude Desktop and Cowork. — [Zapier: Claude + Zapier](https://zapier.com/apps/ai-tools/claude); [createwith.com: Zapier MCP and Claude](https://www.createwith.com/tool/zapier/updates/zapier-mcp-turns-claude-into-personal-assistant-across-9000-apps)
- Zapier webhooks ("Webhooks by Zapier", Catch Hook trigger) are **not on the free plan**. Webhooks and premium apps start on Professional. — [eesel.ai: Zapier subscription plans 2026](https://eesel.ai/blog/zapier-subscription); [dupple: Is Zapier free in 2026](https://dupple.com/learn/is-zapier-free)
- Pipedream's examples call `linkedin-create-image-post-user` through its remote MCP endpoint. Each call needs a project ID and an external user ID tied to the connected LinkedIn account. — [Pipedream: Create Image Post (User)](https://pipedream.com/apps/linkedin/actions/create-image-post-user.md)
- GitHub issue #17752 (July 2025): posting LinkedIn images through the Pipedream MCP server failed with 403 Forbidden ("authenticated user ID missing or invalid"). The listing still showed it open, but its current status is unknown. — [goodfirstissue: PipedreamHQ/pipedream #17752](https://www.goodfirstissue.org/PipedreamHQ/pipedream/issues/17752)
- Make has an official MCP server, hosted at `https://mcp.make.com` with a legacy open-source version. It exposes **on-demand scenarios** as callable tools and needs an API key with scenario read and run scopes. One guide says the hosted endpoint may not yet be available in every Make zone or plan. — [GitHub: integromat/make-mcp-server](https://github.com/integromat/make-mcp-server); [use-apify: Make MCP server with Claude](https://use-apify.com/blog/make-com-mcp-server-claude)
- Make scenarios can also start with a Custom Webhook module, and one source says Custom Webhooks work on Make's free tier. — [Vinkius: Make.com webhook trigger MCP](https://vinkius.com/apps/makecom-webhook-trigger-mcp/tools)
- n8n's MCP Server Trigger node turns a workflow into an MCP endpoint, over SSE or streamable HTTP. It is available on Cloud and on self-hosted Community Edition. Connections must hit the same instance, which matters if you run replicas. — [n8n docs: MCP Server Trigger](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-langchain.mcptrigger/); [Hackceleration: n8n MCP server trigger](https://hackceleration.com/es/recursos/integraciones/n8n/mcp-server-trigger)

### Inferences
- Simplest path from a scheduled Claude cloud session is a plain HTTPS POST to a webhook URL: a Make Custom Webhook, an n8n Webhook node, a Zapier Catch Hook, or a Pipedream HTTP trigger. That host would need to be on the environment's network allowlist. An MCP connector would mean attaching the connector to the scheduled session.
- The repo's CLAUDE.md rule 4 says to publish only through `python -m engine publish <date> --git` and never to call LinkedIn any other way. Any of these platforms would need to be added as a publisher backend inside `engine/`, with locking, retries and duplicate prevention kept. Claude calling Zapier or Pipedream MCP tools directly would break that rule and skip the one-post-per-slot guard.
- An MCP tool call that fails in a way the engine can't see could cause a duplicate post if it is retried. A webhook that returns a post URN is easier to make idempotent.

### Gaps
- No source confirms that Zapier MCP's Create Share Update tool exposes the image-URL field. It's a reasonable assumption because MCP tools mirror the action fields, but it is unverified.
- Whether Pipedream issue #17752 is fixed is unknown.

## 3. Pricing (USD) for the cheapest plan that supports this at about 22 posts a month; free-tier limits

### Takeaway
At 22 posts a month: **Make Free** (1,000 credits, Custom Webhook allowed) or **n8n self-hosted** (free software, but you pay for a server) probably cost nothing. **Zapier Free** might work through MCP: 22 × 2 = 44 tasks, under the 100-task limit, but it has no webhooks. Otherwise Zapier Professional costs about $19.99/mo annual or $29.99/mo monthly. **n8n Cloud Starter** is about €20–24/mo. **Pipedream** changed its plans in Oct 2026: Free is reportedly development-only, and production starts at about $99/mo. All figures come from third-party sources and some conflict.

### Cited Findings
**Zapier**
- Free: 100 tasks a month, two-step Zaps only, no premium apps, no webhooks, 15-minute polling. — [dupple: Is Zapier free 2026](https://dupple.com/learn/is-zapier-free); [eesel.ai](https://eesel.ai/blog/zapier-subscription)
- Professional: multi-step Zaps, premium apps and webhooks, 750 tasks/mo at about $19.99/mo billed annually or $29.99/mo monthly. — [eesel.ai](https://eesel.ai/blog/zapier-subscription); [Lindy: Zapier pricing 2026](https://www.lindy.ai/blog/zapier-pricing-2026). Conflict: Vendr lists Professional at $49/mo annual or $73.50 monthly for 2,000 tasks, probably a higher task tier. — [Vendr](https://www.vendr.com/buyer-guides/zapier)
- Zapier MCP has no separate price. Each successful MCP tool call costs **2 tasks**, and failed calls cost none. On Free that caps you at about 50 successful MCP calls a month. — [Latenode: Zapier MCP pricing](https://latenode.com/blog/zapier-mcp-pricing); [Toolradar: Zapier MCP pricing](https://toolradar.com/tools/zapier-mcp/pricing)
- Retries on errors count against the task quota. — [eesel.ai](https://eesel.ai/blog/zapier-subscription)
- LinkedIn's premium-app status on Zapier was not confirmed. The help page does not label it premium. **Uncertain.**

**Make**
- Free: 1,000 credits a month, 2 active scenarios, no card needed. Make renamed "operations" to "credits" in 2026. — [eesel.ai: Make pricing 2026](https://eesel.ai/blog/make-pricing); [Lindy: Make pricing](https://www.lindy.ai/blog/make-com-pricing)
- Core: 10,000 credits at about $9/mo annual or about $10.59–12 monthly (sources differ). Pro is about $16 and Teams about $29 on annual billing. — [Hackceleration: Make pricing](https://hackceleration.com/labs/make-pricing); [Latenode: Make pricing](https://latenode.com/blog/make-com-pricing); [CostBench: Make](https://www.costbench.com/software/ai-automation/make/)

**n8n**
- Cloud Starter: about €20/mo annual or €24 monthly for 2,500 executions. Pro: about €50–60 for 10,000. n8n prices in EUR, and third-party USD figures (about $20–24) are not converted. An execution is one workflow run, not one step. — [dupple: n8n pricing 2026](https://dupple.com/learn/n8n-pricing); [Toolradar: n8n pricing 2026](https://toolradar.com/blog/n8n-pricing-2026); [sliplane: n8n pricing](https://sliplane.io/blog/n8n-pricing)
- Self-hosted Community Edition is free, and you pay only for hosting. The MCP Server Trigger node is included. — [n8n docs: MCP Server Trigger](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-langchain.mcptrigger/); [sliplane](https://sliplane.io/blog/n8n-pricing)
- n8n Cloud has no permanent free tier according to the pricing sources (trial only). **Not directly confirmed.**

**Pipedream**
- October 2026 restructure, per one report: Basic ($29) and Advanced ($49) removed, Connect renamed "Startup" at $99/mo annual or $150/mo monthly with 10,000 credits ($0.012 per extra credit). Free becomes **development-only**, and production use and external users start at Startup. — [UsagePricing: Pipedream 2026-10-04](https://www.usagepricing.com/blueprint/activity/pipedream-2026-10-04-startup-plan-replaces-tiers); [CostBench: Pipedream (checked 30 Oct 2026)](https://costbench.com/software/ai-automation/pipedream/)
- An MCP tool call costs 1 credit per 30 seconds of compute. — [dailyaifixs: Pipedream pricing 2026](https://dailyaifixs.com/blog/pipedream-pricing-2026-credits-are-compute)
- Earlier 2026 sources give conflicting free allowances (100 credits a month, 100 a day, or 300 a month), so treat these as outdated. — [CostBench free plan](https://costbench.com/software/ai-automation/pipedream/free-plan/); [Toolradar: Pipedream pricing](https://toolradar.com/tools/pipedream/pricing)

### Inferences
- Each post probably uses about 3–5 Make credits (webhook, HTTP get file, LinkedIn image post, webhook response), so 22 posts is roughly 66–110 credits. That fits easily in Make Free's 1,000.
- On Zapier Free with a 2-step Zap, the trigger would have to be a schedule or polling trigger, because webhooks aren't on Free. MCP calls do work on Free, so about 44 tasks a month (22 × 2) fits under 100, but there would be no headroom for retries or tests.
- Pipedream is the most expensive for this use if the October 2026 change is accurate.

### Gaps
- None of the official pricing pages were opened directly, so all prices are from third parties. Confirm on zapier.com/pricing, make.com/en/pricing, n8n.io/pricing and pipedream.com/pricing.
- I found no confirmation of whether n8n MCP-trigger calls count as executions (they probably do, as workflow runs).
- I could not confirm whether LinkedIn is a premium app on Zapier.

## 4. Do they use LinkedIn's official API through their own partner app, and how often must you re-authenticate?

### Takeaway
Zapier, Make and Pipedream connect through their own OAuth apps on LinkedIn's official API, so the user just clicks "connect". n8n usually needs your own LinkedIn developer app (client ID and secret), especially when self-hosted. Expect to **reconnect about every 60 days** unless the platform's app has LinkedIn's approved refresh-token access. Zapier states the 60-day reconnect explicitly.

### Cited Findings
- Zapier: "The authorisation tokens for LinkedIn expire after 60 days," so you must reconnect at least every 60 days. You can check the connection under Connected Accounts with "Test". — [Zapier Help: Get started with LinkedIn](https://help.zapier.com/hc/en-us/articles/8495987891853-How-to-get-started-with-LinkedIn-on-Zapier)
- LinkedIn: access tokens last 60 days. Programmatic refresh tokens (for approved partners) last 365 days and **do not reset** when used, so the member must re-authorize at the one-year mark. — [Microsoft Learn: LinkedIn programmatic refresh tokens](https://learn.microsoft.com/en-us/linkedin/shared/authentication/programmatic-refresh-tokens)
- Self-serve LinkedIn apps get no refresh token. — [opentweet.io: LinkedIn API token expires 60 days](https://opentweet.io/answers/linkedin-api-token-expires-60-days); [Ayrshare: LinkedIn 401 invalid grant](https://www.ayrshare.com/solutions/linkedin-api-error-401-invalid-grant-how-to-fix-token-expiration/)
- Pipedream: for managed OAuth apps it stores the refresh token and creates access tokens automatically. If the refresh token is revoked or expired you must reconnect. — [Pipedream docs: connected accounts](https://pipedream.com/docs/v1/connected-accounts/)
- A Make community thread asks how to automate reconnecting the LinkedIn OAuth token, which suggests Make users also hit periodic reconnects. — [Make Community: automate reconnecting LinkedIn OAuth token](https://community.make.com/t/i-am-trying-to-automated-the-reconnecting-of-the-linkedin-oauth-token/78852)
- n8n's LinkedIn credential is OAuth2. The HTTP-node workaround also uses your own OAuth2 credentials. — [n8n Community: workaround using the HTTP node](https://community.n8n.io/t/linkedin-connection-issue-workaround-using-the-http-node/289794?tl=es)

### Inferences
- If these platforms' LinkedIn apps have refresh tokens, reconnection would be about yearly. Zapier's own help says 60 days, so plan for 60 days on Zapier and assume about the same for Make unless shown otherwise. Pipedream may last longer if its LinkedIn app has refresh scopes, but that is unconfirmed.
- This is about the same as the engine's current direct-token setup, which also has a 60-day token unless it has refresh scopes. So these platforms do not remove the reauthentication chore.

### Gaps
- No official statement on how long Make's or Pipedream's LinkedIn tokens last.
- Whether n8n Cloud has a managed LinkedIn OAuth app or needs your own developer app was not confirmed.

## 5. Analytics for personal posts

### Takeaway
I found no evidence that any of the four platforms offers native analytics for **personal-profile** posts. LinkedIn's Member Post Analytics API (`memberCreatorPostAnalytics`, July 2025) exists but is reached through approved partner tools such as Buffer and Hootsuite. Make's analytics modules cover organization (company-page) statistics.

### Cited Findings
- LinkedIn launched the Member Post Analytics API on 9 July 2025, with per-post engagement data for personal profiles available through approved third-party tools. — [DestinationCRM](https://www.destinationcrm.com/Articles/CRM-News/CRM-Across-the-Wire/LinkedIn-Launches-Member-Post-Analytics-API-170402.aspx); [PPC Land](https://ppc.land/linkedin-enables-third-party-analytics-access-with-new-member-post-api/)
- Creators see this data in tools like Buffer and Hootsuite. — [onlinemarketing.de](https://onlinemarketing.de/social-media-marketing/linkedin-bringt-post-analytics-api-fuer-alle)
- Make's LinkedIn modules include organization share statistics, which are company-page data only. — [Axelor docs: Make LinkedIn modules](https://docs.axelor.com/connect-help-center/docs/HTML/en/apps/marketing/linkedin.html)
- n8n analytics workflows found online use scrapers (Apify, Airtop), not the official API. — [Apify: n8n LinkedIn posts scraper](https://apify.com/integrations/n8n/linkedin-posts-scraper)

### Inferences
- For personal-post analytics, these platforms add nothing. A raw HTTP call to `memberCreatorPostAnalytics` (from n8n's HTTP node or Pipedream code) would need a LinkedIn app approved for that API, which a platform's own app probably isn't, and your own app would need approval.

### Gaps
- I found no official documentation confirming that any of the four exposes member post analytics.

## 6. Setup effort and reliability notes

### Takeaway
Least effort: Zapier (one URL-based action, MCP ready, 60-day reconnect). Make is low effort, needs a file download step, and works on the free tier. n8n takes the most effort and had a native-node outage in 2026. Pipedream is developer-friendly but has a reported MCP image bug and a big October 2026 price rise.

### Cited Findings
- Zapier: LinkedIn image handling is "notoriously finicky", and the image must be a public direct URL. — [Zapier Community](https://community.zapier.com/how-do-i-3/attach-image-with-linkedin-post-51111); [Mallary.ai](https://mallary.ai/blog/zapier-linkedin-integration)
- Make: forum posts from July and August 2025 show users completing personal image-post workflows with "Create a User Image Post". — [Make Community](https://community.make.com/t/how-to-upload-text-image-together-in-linkedin-personal-account-using-make/86474)
- n8n: native node outage in April–July 2026 (`NONEXISTENT_VERSION`, HTTP 426), several forum threads, and a multi-node image workaround. — [n8n Community thread 288332](https://community.n8n.io/t/linkedin-node-fails-with-nonexistent-version-20250401-in-n8n-cloud-2-15-x/288332); [n8n Community: native node not working](https://community.n8n.io/t/linkedin-native-node-not-working/288287)
- Pipedream: MCP image-post 403 bug, status unknown. — [goodfirstissue #17752](https://www.goodfirstissue.org/PipedreamHQ/pipedream/issues/17752)
- Pipedream had a past status incident affecting connected accounts. — [Pipedream status: issues with connected accounts](https://status.pipedream.com/incidents/6lpc3m4mg914)

### Inferences
- All four platforms add a dependency between the engine and LinkedIn without removing the 60-day OAuth chore or adding personal analytics. Their main benefit is a managed OAuth app, which matters only if getting your own LinkedIn developer app with `w_member_social` (the self-serve "Share on LinkedIn" product) is a problem.
- If one is used, the lowest-risk design is a webhook (Make Free, or Zapier Professional) called from inside `engine/` by `python -m engine publish`, with a returned post URN used for duplicate prevention. This keeps CLAUDE.md rule 4.

### Gaps
- I found no published uptime or SLA figures for any platform's LinkedIn integration.
- I did not hands-on test any platform.
