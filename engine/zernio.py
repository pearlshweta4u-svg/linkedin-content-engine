"""Zernio (zernio.com) publishing backend: image posts + personal-post analytics
for LinkedIn, stdlib only.

Auth: the API key is a network secret on the cloud environment, injected by the
egress proxy for zernio.com, or the ZERNIO_API_KEY env var for local use.
Never stored in the repo.

Duplicate safety: every create-post call carries a fixed Idempotency-Key derived
from the slot's post_id. Zernio returns the original post for a repeated key
within 24 hours, so a retry after a timeout cannot create a second post.
"""
from __future__ import annotations

import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
import uuid

from .linkedin import LinkedInError as PublishError, Response, post_url

API = "https://zernio.com/api"
PLACEHOLDER_KEY = "proxy-injected"
_NS = uuid.UUID("6f1c3c2a-9d0e-4b5e-8a7d-2b4c5d6e7f80")


def idempotency_key(post_id: str) -> str:
    return str(uuid.uuid5(_NS, f"trainwithshweta-linkedin-{post_id}"))


class Client:
    idempotent_create = True  # publisher may safely retry an ambiguous create

    def __init__(self, key: str | None = None, opener=None, max_retries: int = 3,
                 backoff: float = 2.0, sleep=time.sleep):
        self.key = key or os.environ.get("ZERNIO_API_KEY") or PLACEHOLDER_KEY
        self._open = opener or urllib.request.urlopen
        self.max_retries = max_retries
        self.backoff = backoff
        self.sleep = sleep

    def _request(self, method: str, url: str, body: bytes | None = None,
                 headers: dict | None = None, auth: bool = True) -> Response:
        h = dict(headers or {})
        if auth:
            h["Authorization"] = f"Bearer {self.key}"
        attempt = 0
        while True:
            attempt += 1
            req = urllib.request.Request(url, data=body, headers=h, method=method)
            try:
                with self._open(req, timeout=120) as resp:
                    return Response(resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read())
            except urllib.error.HTTPError as e:
                payload = e.read().decode("utf-8", "replace")[:2000]
                if e.code in (401, 403):
                    raise PublishError(f"Zernio auth failed ({e.code}): API key missing/invalid", e.code, body=payload)
                if (e.code in (409, 429) or e.code >= 500) and attempt <= self.max_retries:
                    self.sleep(self.backoff ** attempt)
                    continue
                raise PublishError(f"HTTP {e.code} from {url}", e.code, body=payload)
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                if attempt <= self.max_retries:
                    self.sleep(self.backoff ** attempt)
                    continue
                raise PublishError(f"network error: {e}", None)

    def _json(self, method: str, path: str, payload: dict | None = None, headers: dict | None = None) -> dict:
        h = {"Content-Type": "application/json", **(headers or {})}
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        return self._request(method, API + path, data, h).json()

    # ---- API ---------------------------------------------------------------
    def accounts(self) -> list[dict]:
        return self._json("GET", "/v1/accounts").get("accounts", [])

    def upload_image(self, owner: str, image_bytes: bytes, content_type: str = "image/png",
                     filename: str = "post-image.png") -> str:
        """Returns a public HTTPS URL Zernio can attach to a post."""
        pre = self._json("POST", "/v1/media/presign",
                         {"filename": filename, "contentType": content_type, "size": len(image_bytes)})
        self._request("PUT", pre["uploadUrl"], image_bytes, {"Content-Type": content_type}, auth=False)
        return pre["publicUrl"]

    def create_post(self, account_id: str, commentary: str, image_url: str | None = None,
                    image_alt: str | None = None, idempotency_key: str | None = None):
        """Publish now. Returns (platform_post_id, url). Raises PublishError on failure."""
        body = {"content": commentary, "publishNow": True,
                "platforms": [{"platform": "linkedin", "accountId": account_id}]}
        if image_url:
            item = {"type": "image", "url": image_url}
            if image_alt:
                item["altText"] = image_alt
            body["mediaItems"] = [item]
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else {}
        data = self._json("POST", "/v1/posts", body, headers)
        post = data.get("post") or {}
        target = next((p for p in post.get("platforms", []) if p.get("platform") == "linkedin"), {})
        if target.get("status") == "published" and target.get("platformPostId"):
            pid = target["platformPostId"]
            return pid, target.get("platformPostUrl") or post_url(pid)
        if target.get("status") == "failed" or post.get("status") == "failed":
            status = 401 if target.get("errorCategory") == "auth_expired" else 400
            raise PublishError(f"Zernio publish failed: {target.get('errorMessage')}", status,
                               body=json.dumps(target.get("platformError") or {})[:500])
        # still processing: retrying with the same idempotency key is safe
        raise PublishError(f"Zernio post {post.get('_id')} not yet published (status {target.get('status')})", None)

    def post_analytics(self, account_id: str, urn: str) -> dict:
        q = urllib.parse.urlencode({"urn": urn})
        return self._json("GET", f"/v1/accounts/{account_id}/linkedin-post-analytics?{q}").get("analytics", {})


import urllib.parse  # noqa: E402  (used above; kept at end for readability of the module head)


def guess_type(path: str) -> str:
    return mimetypes.guess_type(path)[0] or "image/png"
