# Publishing image posts to a personal LinkedIn profile: official API and Composio (as of 9 Nov 2026)

Method note: learn.microsoft.com and docs.composio.dev could not be fetched from this cloud session (both hosts are outside its network allowlist). LinkedIn facts below come from web-search summaries of Microsoft Learn pages plus third-party developer guides, and are labelled that way. Composio facts come mostly from the **live Composio tool schemas**, read directly through the connected Composio MCP (COMPOSIO_SEARCH_TOOLS, 2026-11-09 10:08 UTC). That is a primary source for what the tools accept today. Those schemas have no public URL, so they are cited as "Composio live schema (MCP, 2026-11-09)". Anything marked "unverified" needs checking against Microsoft Learn once that host is allowed.

## (A1) Can w_member_social + Images API + Posts API publish an image to a personal profile? Is the legacy route still there? Which headers?

### Takeaway
Yes. The self-serve "Share on LinkedIn" product grants w_member_social, and that scope is accepted by the versioned Images API (`POST /rest/images?action=initializeUpload`, owner `urn:li:person:{id}`) and the Posts API (`POST /rest/posts`, author `urn:li:person:{id}`, `content.media.id = urn:li:image:...`). Versioned `/rest/` calls need `Linkedin-Version: YYYYMM` (a non-sunset month) and `X-Restli-Protocol-Version: 2.0.0`. No extra product approval is reported for member posting. The legacy `/v2/assets?action=registerUpload` + `/v2/ugcPosts` flow is still documented on the Share on LinkedIn page and reportedly still works, but it is labelled legacy and has no published sunset date.

### Cited Findings
- The Images API accepts several scopes, including w_member_social, rw_ads, w_organization_social and w_power_creators — [truto.one LinkedIn personal integration](https://truto.one/integrations/detail/linkedinpersonal/); [Adaptly: initializeUpload image URN](https://adaptlypost.com/blog/linkedin-initializeupload-image-urn)
- For images whose owner is a member URN, LinkedIn's rule (as quoted by Adaptly) is that the caller must match the image owner. In practice you upload as yourself, for your own posts — [Adaptly](https://adaptlypost.com/blog/linkedin-initializeupload-image-urn)
- The flow: initializeUpload with body `{"initializeUploadRequest": {"owner": "urn:li:person:..."}}` returns `uploadUrl` and an `urn:li:image:{id}`. You PUT the bytes to uploadUrl, then reference the image URN in the post — [Postproxy](https://www.postproxy.dev/blog/linkedin-api-automate-company-page-publishing/); [Blotato](https://www.blotato.com/blog/linkedin-posting-api)
- The person URN is `urn:li:person:` plus the `sub` value from the OpenID userinfo endpoint — [truto.one](https://truto.one/integrations/detail/linkedinpersonal.md)
- Microsoft docs state that the Posts API replaces ugcPosts and the Images/Videos APIs replace the Assets API. `/rest/` calls need the Linkedin-Version header in YYYYMM form — [Microsoft Learn Posts API (search summary)](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2025-11); [flaghand guide](https://flaghand.com/docs/guides/linkedin-api-personal-profile)
- Version rules: six-digit YYYYMM; a missing header gives 400 VERSION_MISSING and a sunset version gives 426 NONEXISTENT_VERSION; each version lives at least one year. `/v2/` paths do not use the header — [Adaptly: version header format](https://adaptlypost.com/blog/linkedin-version-header-format-required); [Microsoft Learn versioning](https://learn.microsoft.com/en-us/linkedin/marketing/versioning)
- Example header in a current guide: `LinkedIn-Version: 202608` with `X-Restli-Protocol-Version: 2.0.0` — [Postproxy](https://www.postproxy.dev/blog/linkedin-api-automate-company-page-publishing/)
- Reported sunsets: 202508 sunset on 17 Aug 2026, and 202511 sunset on 16 Nov 2026. The newest version is reported as 202609 or 202610, depending on the source — [search summary of Ayrshare / Upload-Post / Blotato guides](https://www.ayrshare.com/solutions/linkedin-api-v1-to-v2-versioned-migration-the-developers-survival-guide/), [Upload-Post](https://www.upload-post.com/linkedin-api/) (third-party; conflicting)
- The Microsoft Images API page currently has a 2026-10 view (`li-lms-2026-10`) — [Microsoft Learn Images API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/images-api?view=li-lms-2026-10)
- The Share on LinkedIn guide still documents `POST /v2/assets?action=registerUpload` and `POST /v2/ugcPosts` (shareMediaCategory IMAGE) — [Microsoft Learn Share on LinkedIn (ru-ru mirror, search result)](https://learn.microsoft.com/ru-ru/linkedin/consumer/integrations/self-serve/share-on-linkedin); [ezooon tutorial](https://ezooon.hashnode.dev/linkedin-api-tutorial-posting-images-and-text)
- ugcPosts has been flagged legacy since 2023 and "still works for some integrations". New features go to /rest/posts only — [timetopost](https://timetopost.co/blog/how-to-post-to-linkedin-api/); [postiv.ai](https://postiv.ai/blog/linkedin-posting-api-for-ai-agents) (third-party)
- A w_member_social-only token cannot do `GET /rest/images` even for an image it just uploaded, because the scope is write-only — [bundle.social / outstand search summary](https://www.outstand.so/blog/linkedin-posts-api)
- Composio's own LinkedIn tools show both routes in production today: LINKEDIN_INITIALIZE_IMAGE_UPLOAD (Images API, owner person or org) and LINKEDIN_REGISTER_IMAGE_UPLOAD (legacy assets API, recipe `urn:li:digitalmediaRecipe:feedshare-image`, "works with a person or organization owner") — Composio live schema (MCP, 2026-11-09)

### Inferences
- For new code the recommended path is: (1) `GET /v2/userinfo` (OpenID) → sub; (2) `POST /rest/images?action=initializeUpload` with owner `urn:li:person:{sub}`; (3) `PUT` bytes to uploadUrl; (4) `POST /rest/posts` with `author`, `commentary`, `visibility: PUBLIC`, `distribution.feedDistribution: MAIN_FEED`, `content.media.id: urn:li:image:...`, `lifecycleState: PUBLISHED`; (5) the post URN comes back in the `x-restli-id` response header. Pin the version in config and bump it at least yearly. A hard-coded retired version is exactly what broke Composio (see B).
- Nothing found says a member-only app needs any product beyond Share on LinkedIn (plus Sign In with LinkedIn using OpenID Connect for the `sub`) to use /rest/images and /rest/posts.

### Gaps
- Could not read the Microsoft Images API, Posts API or Share on LinkedIn pages directly. Exact current "latest" version and the page wording on w_member_social for /rest/images are unverified.
- No published sunset date found for /v2/ugcPosts or /v2/assets on the consumer (Share on LinkedIn) side.

## (A2) Token lifetime, refresh tokens, rate limits, image limits, multi-image

### Takeaway
Access tokens last 60 days. Self-serve apps generally get no programmatic refresh token (refresh is reported as limited to approved partners), so plan to re-authorize in a browser about every 60 days. LinkedIn publishes no post-count cap. Call limits are reported as 150 requests per member and 100,000 per app per UTC day for Share on LinkedIn (third-party, unverified). Images must be under 36,152,320 pixels; formats are JPG, PNG and GIF. Multi-image posts take 2 to 20 images, and Composio's tool exposes this for personal posts.

### Cited Findings
- All access tokens are issued with a 60-day lifespan — [LinkedAPI guide quoting LinkedIn](https://linkedapi.io/guides/linkedin-api-access); [Microsoft Learn 3-legged OAuth](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow)
- Programmatic refresh tokens are available only to a limited set of partners. Self-serve apps re-run the authorization flow, which can be silent if the member is still logged in — [LinkedAPI](https://linkedapi.io/guides/linkedin-api-access); the same claim (refresh limited to approved MDP partners, 365-day refresh lifetime) appears in an AI-generated answer on [Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/5970557/how-to-generate-refresh-token-in-linkedin) (weak evidence). Contradicted by [Zernio](https://zernio.com/blog/linkedin-posting-api), which describes refresh as part of the standard flow.
- Limits count API calls, not posts. An image post costs several calls (initialize, upload, create) — [Adaptly: post limit per day](https://adaptlypost.com/blog/linkedin-post-limit-per-day)
- 150 requests per member and 100,000 per application per UTC day are cited as listed on the Share on LinkedIn page. These were not confirmed on LinkedIn's page in this session — [Adaptly](https://adaptlypost.com/blog/linkedin-post-limit-per-day); [Blotato rate limits](https://www.blotato.com/blog/social-media-api-rate-limits)
- Official: standard rate limits are not published. Check the Developer Portal Analytics tab. Limits reset at midnight UTC and an overage returns 429 — [Microsoft Learn rate limits](https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/rate-limits)
- Images must have fewer than 36,152,320 pixels; formats are JPG, PNG and GIF — [Microsoft Learn Images API (search summary)](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/images-api?view=li-lms-2026-10); [PublishQ](https://publishq.com/linkedin-limits)
- GIF frame limit: 250 in the Images API per one source, 500 or under 400 per others (conflicting) — [connectsafely](https://connectsafely.ai/articles/how-many-photos-can-you-post-on-linkedin-2026); [PostPost](https://postpost.ai/articles/linkedin-image-sizes)
- File size: third-party guides range from 5 MB to 20 MB; no official MB cap was found — [PublishQ](https://publishq.com/linkedin-limits); [opentweet](https://opentweet.io/tools/linkedin-image-size)
- The MultiImage API takes 2 to 20 images per organic post — [connectsafely](https://connectsafely.ai/articles/how-many-photos-can-you-post-on-linkedin-2026)
- Composio's create-post tool accepts 1 to 20 images for a person author and uses `media` for one image and `multiImage` for two or more — Composio live schema (MCP, 2026-11-09)

### Inferences
- For this engine, a 60-day token with no refresh means a re-auth reminder every ~55 days. 150 calls/member/day is far above a one-post-per-day schedule (~3 to 4 calls per image post).
- Keep images comfortably under ~5 MB JPG/PNG to stay within every quoted limit.

### Gaps
- No official per-image MB limit found. Whether multiImage works with w_member_social alone was not confirmed in LinkedIn's docs, though Composio's tool claims it for person authors.

## (A3) Does a developer app need a Company Page? Review step? Setup time?

### Takeaway
Yes, creating any LinkedIn developer app requires associating it with a LinkedIn Company Page, and a page admin must verify the app. Share on LinkedIn and Sign In with LinkedIn (OpenID Connect) are self-serve products with no review, so setup is typically same-day once a page exists.

### Cited Findings
- A LinkedIn Company Page is required to create a developer app; the app must be verified and have Share on LinkedIn enabled — [Zernio](https://zernio.com/blog/linkedin-posting-api)
- The page administrator verifies the app via a verification link — [OWOX docs](https://docs.owox.com/packages/connectors/src/sources/linked-in-pages/credentials/); [nestcode](https://nestcode.co/en/blog/using-linkedin-developer-apps-to-share-information-to-your-profile-or-company-page-)
- profile, email and w_member_social are open permissions that need no LinkedIn approval; w_member_social is available via self-serve Share on LinkedIn with no review gate — [closelyhq](https://blog.closelyhq.com/linkedin-api-for-developers-what-you-can-and-cant-do); [flaghand](https://flaghand.com/docs/guides/linkedin-api-personal-profile)

### Inferences
- Shweta would need a Company Page (a TrainWithShweta page would do; it can be minimal) that she administers, so she can self-verify. The app posts to her personal profile, not the page.

### Gaps
- No official statement on typical setup time; "same-day" is an inference from the absence of review for self-serve products.

## (A4) Analytics: can a member read impressions/reactions on their own posts with self-serve scopes?

### Takeaway
No. Member post analytics (`memberCreatorPostAnalytics`, scope `r_member_postAnalytics`, versions 202506+) belongs to the Community Management API, which requires app review. LinkedIn's official app-review page says that API is "only available to registered legal organizations for commercial use cases". Individual developers are not eligible. Reading a member's own posts (`r_member_social`) is also restricted.

### Cited Findings
- memberCreatorPostAnalytics returns IMPRESSION, MEMBERS_REACHED, REACTION, COMMENT and RESHARE for single posts (entity finder) or aggregated (me finder). It requires `r_member_postAnalytics`, which comes with Community Management, not Share on LinkedIn. The scope is supported only from version 202506. 202604 added metrics such as POST_SEND — [Microsoft Learn Member Post Statistics (search summary)](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/members/post-statistics?view=li-lms-2026-09); [postiz issue #1680](https://github.com/gitroomhq/postiz-app/issues/1680)
- Adding the scope before approval breaks the consent screen for every connect or reconnect — [linkedin_engagement_manager issue #695](https://github.com/christopherqueenconsulting/linkedin_engagement_manager/issues/695)
- Official: "our Community Management APIs are only available to registered legal organizations for commercial use cases only". Applicants give a verified business email, legal name, registered address, website and privacy policy. A rejected app cannot re-apply for Standard tier — [Microsoft Learn Community Management app review](https://learn.microsoft.com/en-us/linkedin/marketing/community-management-app-review)
- Individuals or unregistered projects are "instantly ineligible" (third-party) — [singhamandeep.com](https://singhamandeep.com/?p=1387)
- r_member_social (listing a member's posts) is restricted to approved users — [closelyhq](https://blog.closelyhq.com/linkedin-api-for-developers-what-you-can-and-cant-do)
- Composio had no native LinkedIn post-analytics tool for this account. A search for "impressions and reactions for my own linkedin posts" returned only Ordinal toolkit tools (a third-party scheduler that reads analytics for profiles connected to Ordinal) — Composio live schema (MCP, 2026-11-09)

### Inferences
- With a self-serve app, analytics need manual entry (from LinkedIn's UI or the export) or a third-party tool that has Community Management approval. A sole-trader business might qualify as a "registered legal organization", but that is untested.

### Gaps
- No LinkedIn statement found on sole proprietors. Did not check whether Composio's own LinkedIn OAuth app holds r_member_postAnalytics.

## (B) Composio LinkedIn toolkit: images

### Takeaway
LINKEDIN_CREATE_LINKED_IN_POST takes images only as Composio file objects `{name, mimetype, s3key}` (1 to 20, `file_uploadable: true`). There is no URL field and no raw-bytes or base64 field. The s3key can come from the Composio workbench's `upload_local_file()` helper or from a download action in another toolkit. Composio also exposes LINKEDIN_INITIALIZE_IMAGE_UPLOAD (Images API) and LINKEDIN_REGISTER_IMAGE_UPLOAD (legacy assets). Each returns an upload URL plus an image or asset URN, but you must PUT the bytes yourself, and create-post has no field for a pre-made URN. Known risk: Composio has twice shipped a retired LinkedIn-Version header (426 errors) on the create-post tool.

### Cited Findings
- `LINKEDIN_CREATE_LINKED_IN_POST` required: `author` (pattern `urn:li:(person|organization):...`) and `commentary` (max 3000 chars). Optional `images`: an array of `{name, mimetype, s3key}`, maxItems 20; "s3key: The S3 key of a publicly accessible file, typically returned from a previous download action that stored the file in S3". It auto-selects `media` for 1 image and `multiImage` for 2 or more. It also has visibility, lifecycleState (PUBLISHED/DRAFT), distribution and reshareContext. It needs w_member_social for a person — Composio live schema (MCP, 2026-11-09)
- `LINKEDIN_INITIALIZE_IMAGE_UPLOAD`: input `owner` (person or org URN) → presigned upload_url + image URN; "upload the image bytes to the returned upload_url via PUT request, then use the image URN in CREATE_LINKED_IN_POST" — Composio live schema (MCP, 2026-11-09). Note: the create-post schema has no image-URN field, so the documented hand-off does not match the schema.
- `LINKEDIN_REGISTER_IMAGE_UPLOAD`: inputs `owner_urn`, `recipe` (default `urn:li:digitalmediaRecipe:feedshare-image`; ads recipes with a person owner return 403), `supported_upload_mechanism` → upload_url + asset URN — Composio live schema (MCP, 2026-11-09)
- Workbench helper `upload_local_file(*file_paths)` uploads sandbox files to Composio S3/R2 and returns `s3_url, uploaded_file, type, s3key`. The remote workbench can also fetch an image URL into its sandbox first, and `proxy_execute(method, endpoint, toolkit='linkedin', ...)` can call raw LinkedIn endpoints with the connected account's token — Composio REMOTE_WORKBENCH tool description (MCP, 2026-11-09)
- Toolkit-specific helpers that turn base64 into a Composio file key exist (e.g. BOLDSIGN_FILE_UPLOAD, "upload a file to R2 temp via the Composio file pipeline, returning a key that can be passed to FileUploadable fields in other actions"; BUBBLE_FILE_TEMP_CREATE). Each needs its own toolkit connection. LinkedIn has no equivalent — Composio live schema (MCP, 2026-11-09)
- Composio docs: create-post supports image + text and multiple images when called through the SDKs/APIs, by passing an array to `images`. If image posting fails, check the toolkit version first — [Composio KB: LinkedIn toolkit](https://docs.composio.dev/kb/guide/toolkits-linkedin)
- Issue #4320: the image upload path worked (presigned URL, 200 on upload, s3key accepted), but the post failed with 426 NONEXISTENT_VERSION because /api/v3 without a tool version resolved to a pinned toolkit with retired header 20241101. Workaround: v3.1 endpoint / `toolkit_versions=latest`. It fails the same way with or without images — [ComposioHQ/composio #4320](https://github.com/ComposioHQ/composio/issues/4320)
- Issue #3113: the same 426 traced to `LinkedIn-Version: 20241101`; suggested fix is a supported version like 202603 — [ComposioHQ/composio #3113](https://github.com/ComposioHQ/composio/issues/3113)
- Org posting needs org scopes on the auth config. Not relevant for personal posts, but it confirms personal posting uses w_member_social — [#4138](https://github.com/ComposioHQ/composio/issues/4138); [#4444](https://github.com/ComposioHQ/composio/issues/4444)
- The connected account in this environment is Shweta Mehta (pearl.shweta4u@gmail.com, OpenID sub `I5qjBjt3sE`, so author `urn:li:person:I5qjBjt3sE`). Two ACTIVE LinkedIn connections exist, `linkedin_libra-rifter` (default) and `linkedin_oxane-atis`, both created 2026-10-16. Account selection is required — Composio MCP connection status (2026-11-09)

### Inferences
- Most reliable Composio route: in the workbench, put the image file in the sandbox (download it from a URL, e.g. a raw GitHub URL of `content/images/...`) → `upload_local_file(path)` → take `s3key` → `run_composio_tool('LINKEDIN_CREATE_LINKED_IN_POST', {author, commentary, images:[{name, mimetype:'image/jpeg', s3key}]}, account='linkedin_libra-rifter')`. The fallback is `proxy_execute` to `/rest/images?action=initializeUpload` + PUT + `/rest/posts` with your own Linkedin-Version header. I have not tested whether proxy_execute can PUT binary to the external upload URL.
- Whether a workbench `upload_local_file` s3key is accepted by a FileUploadable field in another call is implied by the helper's description and the issue #4320 report ("s3key accepted"), but this session did not test it end to end.
- This engine's CLAUDE.md requires all publishing through `python -m engine publish` and forbids calling the LinkedIn API any other way. Any Composio path would have to be wired into the engine's publish command, not used ad hoc.

### Gaps
- Could not fetch composio.dev/toolkits/linkedin or docs.composio.dev (host blocked). No end-to-end test was run, deliberately, because that would publish a post.
- Unknown which LinkedIn-Version Composio's create-post tool sends today. The 426 issues suggest checking the toolkit version before relying on it.
