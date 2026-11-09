"""Import Shweta's past LinkedIn posts from LinkedIn's official data export
(Settings > Data privacy > Get a copy of your data > "Posts"/"Shares").

Reads Shares.csv (and Rich_Media.csv when present) from the export ZIP or folder,
writes history/posts.json and downloads post images to history/images/.
Nothing here posts or changes anything on LinkedIn.
"""
from __future__ import annotations

import csv
import io
import json
import re
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from .config import ROOT

HISTORY = ROOT / "history"


def _norm(h: str) -> str:
    return re.sub(r"[^a-z]", "", h.lower())


def _read_csvs(src: Path) -> dict[str, list[dict]]:
    """Return {"shares": rows, "rich_media": rows} from a ZIP or a folder."""
    files: dict[str, str] = {}
    if src.is_dir():
        for p in src.rglob("*.csv"):
            files[p.name.lower()] = p.read_text(encoding="utf-8-sig", errors="replace")
    else:
        with zipfile.ZipFile(src) as z:
            for n in z.namelist():
                if n.lower().endswith(".csv"):
                    files[Path(n).name.lower()] = z.read(n).decode("utf-8-sig", errors="replace")
    out = {"shares": [], "rich_media": []}
    for name, text in files.items():
        key = "shares" if name in ("shares.csv", "posts.csv") else "rich_media" if name.startswith("rich_media") else None
        if not key:
            continue
        rows = list(csv.DictReader(io.StringIO(text)))
        out[key] += [{_norm(k): (v or "").strip() for k, v in r.items() if k} for r in rows]
    return out


def _first(row: dict, *keys: str) -> str:
    for k in keys:
        if row.get(k):
            return row[k]
    return ""


def _download(url: str, dest: Path, opener=urllib.request.urlopen) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "linkedin-content-engine/1.0"})
        with opener(req, timeout=60) as r:
            data = r.read()
            ctype = (r.headers.get("Content-Type") or "").split(";")[0]
        if not ctype.startswith("image/"):
            return f"not an image ({ctype or 'unknown type'})"
        ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp"}.get(ctype, ".img")
        dest = dest.with_suffix(ext)
        dest.write_bytes(data)
        return str(dest)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return f"download failed: {e}"


def import_export(src: Path, out_dir: Path | None = None, download: bool = True, opener=urllib.request.urlopen) -> dict:
    out_dir = out_dir or HISTORY
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    data = _read_csvs(src)
    posts = []
    for i, row in enumerate(data["shares"]):
        text = _first(row, "sharecommentary", "commentary", "text")
        date = _first(row, "date", "datetime", "createdat")
        media = [u for u in re.split(r"\s+", _first(row, "mediaurl", "mediaurls", "media")) if u.startswith("http")]
        posts.append({
            "date": date, "url": _first(row, "sharelink", "link", "url"),
            "shared_url": _first(row, "sharedurl"), "visibility": _first(row, "visibility"),
            "text": text, "hook": text.strip().split("\n")[0][:200] if text else "",
            "word_count": len(text.split()), "media_urls": media, "images": [], "image_errors": [],
        })
    # Rich_Media.csv: images uploaded with posts (Date/Time, Media Description, Media Link)
    rich = [{"date": _first(r, "datetime", "date"), "url": _first(r, "medialink", "link"),
             "description": _first(r, "mediadescription", "description")} for r in data["rich_media"]]
    if download:
        for n, p in enumerate(posts):
            stem = re.sub(r"[^0-9]", "", p["date"])[:8] or "undated"
            for k, u in enumerate(p["media_urls"]):
                res = _download(u, img_dir / f"{stem}-{n:03d}-{k}", opener)
                (p["images"] if res and not res.startswith(("not ", "download")) else p["image_errors"]).append(
                    str(Path(res).relative_to(ROOT)) if res and res.startswith(str(ROOT)) else res)
        for n, r in enumerate(rich):
            if r["url"].startswith("http"):
                stem = re.sub(r"[^0-9]", "", r["date"])[:8] or "undated"
                res = _download(r["url"], img_dir / f"rich-{stem}-{n:03d}", opener)
                r["image"] = str(Path(res).relative_to(ROOT)) if res and res.startswith(str(ROOT)) else None
                r["error"] = None if r["image"] else res
    posts.sort(key=lambda p: p["date"])
    summary = {"posts": len(posts), "with_media_links": sum(1 for p in posts if p["media_urls"]),
               "images_saved": sum(len(p["images"]) for p in posts) + sum(1 for r in rich if r.get("image")),
               "image_errors": sum(len(p["image_errors"]) for p in posts) + sum(1 for r in rich if r.get("error")),
               "rich_media_rows": len(rich)}
    (out_dir / "posts.json").write_text(json.dumps({"summary": summary, "posts": posts, "rich_media": rich},
                                                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary
