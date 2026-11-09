# LinkedIn API: findings (checked 9 Nov 2026)

## Can we publish to Shweta's personal profile automatically? **Yes**, through the official API.

| Need | LinkedIn product / scope | Access |
|---|---|---|
| Create posts on her own profile | **Share on LinkedIn** product → scope `w_member_social` | Self-serve, instant |
| Know her member ID (author URN) | **Sign In with LinkedIn using OpenID Connect** → scopes `openid profile` | Self-serve, instant |
| Upload images for posts | Images API, covered by `w_member_social` | Self-serve |
| Read analytics for her personal posts (impressions, reactions) | Community Management API (`r_member_postAnalytics` / member social read scopes) | **Restricted.** Application and review needed; usually granted to companies building tools, rarely to individuals. Treat as unavailable. |

Endpoints used (`engine/linkedin.py`):
- `GET https://api.linkedin.com/v2/userinfo` → `sub` → author `urn:li:person:{sub}`
- `POST https://api.linkedin.com/rest/images?action=initializeUpload` → `uploadUrl` + `urn:li:image:…`; then `PUT` the bytes to `uploadUrl`
- `POST https://api.linkedin.com/rest/posts` with headers `LinkedIn-Version: YYYYMM` and `X-Restli-Protocol-Version: 2.0.0` → `201` and an `x-restli-id` header holding the post URN. Post URL = `https://www.linkedin.com/feed/update/{urn}/`

## Constraints that shape the design
- **Token lifetime: 60 days, no refresh token** for self-serve apps (programmatic refresh tokens are only for approved partners). Shweta reconnects every ~60 days (2 minutes, docs/SETUP.md step 4). The engine warns 10 days ahead; on expiry the post isn't lost, it waits for her or is skipped with an alert.
- **API versions expire after about a year.** The `LinkedIn-Version` header is in `config/settings.json` (`202606` at build time; e.g. version 202511 sunsets 16 Nov 2026). Bump it once a year (see OPERATIONS).
- **Commentary escaping.** The Posts API "little text" format needs `( ) [ ] { } < > @ # * _ ~ | \` backslash-escaped, or LinkedIn silently truncates the post. Hashtags become `{hashtag|\#|Tag}`. Handled and tested.
- **Not idempotent.** `POST /rest/posts` has no idempotency key. The engine writes a durable "publishing" lock before the call and never auto-retries an ambiguous failure (timeout/500); it asks Shweta to check instead.
- **Rate limits:** member daily limits are far above 1 post/day; 429s are retried with backoff.
- A developer app must be associated with a **LinkedIn Company Page** (it can be a TrainWithShweta page). Posts still go out as Shweta personally.

## Sources
- Posts API: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api
- Images API: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/images-api
- Share on LinkedIn: https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin
- Getting access: https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access
- Versioning: https://learn.microsoft.com/en-us/linkedin/marketing/versioning
