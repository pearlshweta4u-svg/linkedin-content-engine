"""Minimal official-LinkedIn-API client (Posts API + Images API), stdlib only.

Auth: a member access token with scopes `w_member_social` (post) and
`openid profile` (to read the member id). Token source, in order:
  1. env LINKEDIN_ACCESS_TOKEN
  2. none -> we send a placeholder and rely on the cloud environment's network
     secret for api.linkedin.com, which the egress proxy injects as the
     Authorization header. The real token never sits in the repo or the session.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

API = "https://api.linkedin.com"
PLACEHOLDER_TOKEN = "injected-by-proxy"
_RESERVED = re.compile(r"([\\|{}@\[\]()<>#*_~])")
_HASHTAG = re.compile(r"(?<![\w\\])#([A-Za-z][A-Za-z0-9_]*)")


class LinkedInError(Exception):
    def __init__(self, message: str, status: int | None = None, ambiguous: bool = False, body: str = ""):
        super().__init__(message)
        self.status = status
        self.ambiguous = ambiguous  # True => the request may have succeeded server-side
        self.body = body


def escape_commentary(text: str) -> str:
    """Posts API 'little text' format: reserved characters must be backslash-escaped
    or LinkedIn silently truncates the post. Hashtags become hashtag templates."""
    tags: list[str] = []

    def _stash(m: re.Match) -> str:
        tags.append(m.group(1))
        return f"\x00{len(tags) - 1}\x00"

    stashed = _HASHTAG.sub(_stash, text)
    escaped = _RESERVED.sub(r"\\\1", stashed)
    return re.sub(r"\x00(\d+)\x00", lambda m: "{hashtag|\\#|" + tags[int(m.group(1))] + "}", escaped)


def post_url(urn: str) -> str:
    return f"https://www.linkedin.com/feed/update/{urn}/"


@dataclass
class Response:
    status: int
    headers: dict
    body: bytes

    def json(self):
        return json.loads(self.body.decode("utf-8")) if self.body else {}


class Client:
    def __init__(self, api_version: str, token: str | None = None, opener=None,
                 max_retries: int = 3, backoff: float = 2.0, sleep=time.sleep):
        self.api_version = api_version
        self.token = token or os.environ.get("LINKEDIN_ACCESS_TOKEN") or PLACEHOLDER_TOKEN
        self._open = opener or urllib.request.urlopen
        self.max_retries = max_retries
        self.backoff = backoff
        self.sleep = sleep

    # ---- transport -------------------------------------------------------
    def _request(self, method: str, url: str, body: bytes | None = None,
                 headers: dict | None = None, idempotent: bool = True, rest: bool = True) -> Response:
        h = {"Authorization": f"Bearer {self.token}"}
        if rest:
            h.update({"LinkedIn-Version": self.api_version, "X-Restli-Protocol-Version": "2.0.0"})
        h.update(headers or {})
        attempt = 0
        while True:
            attempt += 1
            req = urllib.request.Request(url, data=body, headers=h, method=method)
            try:
                with self._open(req, timeout=60) as resp:
                    return Response(resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read())
            except urllib.error.HTTPError as e:
                payload = e.read().decode("utf-8", "replace")[:2000]
                if e.code in (401, 403):
                    raise LinkedInError(f"auth failed ({e.code}): token missing, expired or lacks scope", e.code, body=payload)
                retryable = e.code == 429 or (e.code >= 500 and (idempotent or e.code in (502, 503, 504)))
                if retryable and attempt <= self.max_retries:
                    self.sleep(self.backoff ** attempt)
                    continue
                # A 500 on a non-idempotent POST may still have created the post.
                ambiguous = (not idempotent) and e.code == 500
                raise LinkedInError(f"HTTP {e.code} from {url}", e.code, ambiguous=ambiguous, body=payload)
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                if idempotent and attempt <= self.max_retries:
                    self.sleep(self.backoff ** attempt)
                    continue
                # Network failure on create-post: we cannot know if LinkedIn got it.
                raise LinkedInError(f"network error: {e}", None, ambiguous=not idempotent)

    def _json(self, method: str, path: str, payload: dict, idempotent: bool) -> Response:
        return self._request(method, API + path, json.dumps(payload).encode("utf-8"),
                             {"Content-Type": "application/json"}, idempotent=idempotent)

    # ---- API calls -------------------------------------------------------
    def userinfo(self) -> dict:
        """OpenID userinfo; 'sub' is the member id for urn:li:person:{sub}."""
        return self._request("GET", API + "/v2/userinfo", rest=False).json()

    def upload_image(self, owner_urn: str, image_bytes: bytes, content_type: str = "image/png") -> str:
        init = self._json("POST", "/rest/images?action=initializeUpload",
                          {"initializeUploadRequest": {"owner": owner_urn}}, idempotent=True).json()
        value = init["value"]
        self._request("PUT", value["uploadUrl"], image_bytes,
                      {"Content-Type": content_type}, idempotent=True, rest=False)
        return value["image"]

    def create_post(self, author_urn: str, commentary: str, image_urn: str | None = None,
                    image_alt: str | None = None, escape: bool = True) -> str:
        body = {
            "author": author_urn,
            "commentary": escape_commentary(commentary) if escape else commentary,
            "visibility": "PUBLIC",
            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [],
                             "thirdPartyDistributionChannels": []},
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        if image_urn:
            media = {"id": image_urn}
            if image_alt:
                media["altText"] = image_alt[:4086]
            body["content"] = {"media": media}
        resp = self._json("POST", "/rest/posts", body, idempotent=False)
        urn = resp.headers.get("x-restli-id") or resp.headers.get("x-linkedin-id")
        if resp.status != 201 or not urn:
            raise LinkedInError(f"unexpected create-post response {resp.status}", resp.status,
                                ambiguous=True, body=resp.body.decode("utf-8", "replace")[:2000])
        return urn
