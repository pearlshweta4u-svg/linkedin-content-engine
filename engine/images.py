"""Branded post images from HTML templates (free, no AI image service).

Each post record may carry an `image_spec`:
  {"template": "story" | "steps" | "checklist" | "stat",
   "eyebrow": "short label", "title": "...", "subtitle": "...",
   "items": ["...", ...], "stat": "136M", "stat_label": "...",
   "source": "Source line", "alt": "alt text for screen readers"}

`render(record)` writes content/images/<post_id>.png and returns its repo path.
Templates follow knowledge/brand-visual.md. Text that does not fit raises
ImageError (never a clipped image).
"""
from __future__ import annotations

import html
import subprocess
import tempfile
from pathlib import Path

from .config import IMAGES_DIR, ROOT

FONTS = ROOT / "assets" / "fonts"
# Mobile-first: LinkedIn's phone feed shows images ~360px wide, so text must be
# large at 1080px. Square for cards, 4:5 portrait for checklists.
SIZES = {"story": (1080, 1080), "steps": (1080, 1080), "stat": (1080, 1080), "checklist": (1080, 1350),
         "photo": (1080, 1350)}
MIN_FONT_PX = 30  # smallest body text; ~10px on a phone. Fine print (source) is 22px.
DEFAULT_TEMPLATE = {"personal_story": "story", "client_story": "story", "educational": "steps",
                    "save_worthy": "checklist", "health_wellness": "stat"}
LIMITS = {"title": 80, "subtitle": 110, "eyebrow": 36, "item": 60, "items": 7, "stat": 7,
          "stat_label": 80, "source": 120}


class ImageError(Exception):
    pass


def _e(s) -> str:
    return html.escape(str(s or ""))


BASE_CSS = """
@font-face { font-family: 'Poppins'; font-weight: 600; src: url('{fonts}/Poppins-600.woff2') format('woff2'); }
@font-face { font-family: 'Poppins'; font-weight: 700; src: url('{fonts}/Poppins-700.woff2') format('woff2'); }
@font-face { font-family: 'Playfair'; font-weight: 700; src: url('{fonts}/PlayfairDisplay-700.woff2') format('woff2'); }
@font-face { font-family: 'Playfair'; font-style: italic; font-weight: 500; src: url('{fonts}/PlayfairDisplay-500-italic.woff2') format('woff2'); }
:root { --navy:#1B2A4A; --teal:#138A8A; --orange:#E8833A; --cream:#F7F3EC; --slate:#5B6475; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: {w}px; height: {h}px; overflow: hidden; }
body { background: var(--cream); color: var(--navy); font-family: 'Inter', 'DejaVu Sans', sans-serif;
       position: relative; -webkit-font-smoothing: antialiased; }
.frame { position: absolute; inset: 0; padding: {pad}px; display: flex; flex-direction: column; }
.bar { position: absolute; left: 0; top: 0; bottom: 0; width: 18px; background: var(--teal); }
.eyebrow { font-family: 'Poppins'; font-weight: 600; font-size: 30px; letter-spacing: .12em;
           text-transform: uppercase; color: var(--teal); margin-bottom: 24px; }
h1 { font-family: 'Poppins'; font-weight: 700; line-height: 1.12; color: var(--navy); }
.sub { font-size: 40px; line-height: 1.4; color: var(--slate); }
.foot { position: absolute; left: {pad}px; right: {pad}px; bottom: 44px; display: flex;
        justify-content: space-between; align-items: flex-end; gap: 30px; font-size: 22px; color: var(--slate); }
.mark { font-family: 'Poppins'; font-weight: 600; font-size: 32px; color: var(--slate); white-space: nowrap; }
.mark b { color: var(--teal); font-weight: 700; }
.src { text-align: right; font-size: 22px; line-height: 1.3; }
.fit { overflow: hidden; }
"""


def _page(css: str, body: str, w: int, h: int, pad: int = 72) -> str:
    base = (BASE_CSS.replace("{fonts}", FONTS.as_uri()).replace("{w}", str(w))
            .replace("{h}", str(h)).replace("{pad}", str(pad)))
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{base}{css}</style></head><body>{body}</body></html>"


def _foot(spec: dict) -> str:
    src = f"<div class='src'>{_e(spec.get('source'))}</div>" if spec.get("source") else "<div></div>"
    return f"<div class='foot'><div class='mark'>TrainWith<b>Shweta</b></div>{src}</div>"


def _story(spec, w, h):
    css = """
    .q { width: 110px; height: 10px; border-radius: 5px; background: var(--orange); margin: 8px 0 40px; }
    h1 { font-size: 80px; line-height: 1.1; }
    .main { flex: 1; display:flex; flex-direction:column; justify-content:center; padding-bottom: 110px; }
    .sub { margin-top: 40px; }
    """
    body = f"""<div class='bar'></div><div class='frame'><div class='main fit' data-name='story'>
      <div class='eyebrow'>{_e(spec.get('eyebrow'))}</div><div class='q'></div>
      <h1>{_e(spec['title'])}</h1>{f"<p class='sub'>{_e(spec['subtitle'])}</p>" if spec.get('subtitle') else ''}
    </div></div>{_foot(spec)}"""
    return _page(css, body, w, h, pad=84)


def _steps(spec, w, h):
    items = spec.get("items") or []
    css = """
    h1 { font-size: 60px; line-height: 1.12; }
    .col { display:flex; flex-direction:column; gap: 22px; margin-top: 44px; }
    .step { display:flex; gap: 26px; align-items:center; background:#fff; border-radius: 22px; padding: 28px 32px;
            border-left: 10px solid var(--teal); }
    .step:last-child { border-left-color: var(--orange); }
    .num { font-family:'Poppins'; font-weight:700; color: var(--teal); font-size: 40px; flex: 0 0 64px; }
    .step:last-child .num { color: var(--orange); }
    .txt { font-size: 36px; line-height: 1.3; color: var(--navy); }
    .main { flex:1; padding-bottom: 100px; display:flex; flex-direction:column; justify-content:center; }
    """
    cells = "".join(f"<div class='step'><div class='num'>{i + 1:02d}</div><div class='txt'>{_e(it)}</div></div>"
                    for i, it in enumerate(items))
    body = f"""<div class='bar'></div><div class='frame'><div class='main fit' data-name='steps'>
      <div class='eyebrow'>{_e(spec.get('eyebrow'))}</div><h1>{_e(spec['title'])}</h1>
      <div class='col'>{cells}</div></div></div>{_foot(spec)}"""
    return _page(css, body, w, h, pad=80)


def _checklist(spec, w, h):
    items = spec.get("items") or []
    css = """
    h1 { font-size: 68px; line-height: 1.1; margin-bottom: 14px; }
    .sub { margin-bottom: 26px; font-size: 36px; }
    ol { list-style: none; display:flex; flex-direction:column; gap: 18px; flex: 1; justify-content: center; }
    li { display:flex; gap: 24px; align-items:center; background:#fff; border-radius: 20px; padding: 24px 28px; }
    .box { flex: 0 0 52px; height: 52px; border-radius: 12px; border: 4px solid var(--teal);
           font-family:'Poppins'; font-weight:700; color: var(--teal); display:flex; align-items:center;
           justify-content:center; font-size: 28px; }
    li:last-child .box { border-color: var(--orange); color: var(--orange); }
    .t { font-size: 36px; line-height: 1.25; color: var(--navy); }
    .main { flex:1; padding-bottom: 110px; display:flex; flex-direction:column; }
    """
    lis = "".join(f"<li><div class='box'>{i + 1}</div><div class='t'>{_e(it)}</div></li>" for i, it in enumerate(items))
    body = f"""<div class='bar'></div><div class='frame'><div class='main fit' data-name='checklist'>
      <div class='eyebrow'>{_e(spec.get('eyebrow'))}</div><h1>{_e(spec['title'])}</h1>
      {f"<p class='sub'>{_e(spec['subtitle'])}</p>" if spec.get('subtitle') else ''}<ol>{lis}</ol>
    </div></div>{_foot(spec)}"""
    return _page(css, body, w, h, pad=72)


def _stat(spec, w, h):
    items = spec.get("items") or []
    css = """
    .big { font-family:'Poppins'; font-weight:700; font-size: 190px; line-height: .95; color: var(--orange); }
    .lab { font-size: 38px; line-height: 1.3; color: var(--navy); margin: 14px 0 40px; }
    h1 { font-size: 50px; margin-bottom: 22px; }
    ul { list-style:none; display:flex; flex-direction:column; gap: 16px; }
    li { font-size: 34px; line-height: 1.3; padding-left: 34px; position: relative; color: var(--navy); }
    li::before { content:''; position:absolute; left:0; top: 15px; width: 16px; height: 16px; border-radius: 4px; background: var(--teal); }
    .main { flex:1; padding-bottom: 120px; display:flex; flex-direction:column; justify-content:center; }
    """
    lis = "".join(f"<li>{_e(it)}</li>" for it in items)
    body = f"""<div class='bar'></div><div class='frame'><div class='main fit' data-name='stat'>
      <div class='eyebrow'>{_e(spec.get('eyebrow'))}</div><div class='big'>{_e(spec.get('stat'))}</div>
      <div class='lab'>{_e(spec.get('stat_label'))}</div><h1>{_e(spec['title'])}</h1><ul>{lis}</ul>
    </div></div>{_foot(spec)}"""
    return _page(css, body, w, h, pad=80)


def _photo(spec, w, h):
    """Her real photo (from her Google Photos album) with a cream text panel on the left,
    serif headline and up to 3 short points: modelled on her own best designed posts."""
    photo = (ROOT / spec["photo"]).as_uri()
    scale = float(spec.get("photo_scale", 1.15))
    right = int(spec.get("photo_right", -200))
    top = int(spec.get("photo_top", 0))
    items = spec.get("items") or []
    css = f"""
    .ph {{ position:absolute; top:{top}px; right:{right}px; height:{scale * 100:.0f}%; width:auto; }}
    .veil {{ position:absolute; inset:0; background: linear-gradient(90deg, rgba(247,243,236,1) 0%,
             rgba(247,243,236,.97) 40%, rgba(247,243,236,.75) 52%, rgba(247,243,236,0) 66%); }}
    .col {{ position:absolute; left:72px; top:96px; width:520px; bottom:150px; display:flex; flex-direction:column; }}
    h1 {{ font-family:'Playfair'; font-weight:700; font-size:70px; line-height:1.06; color: var(--navy); }}
    .it {{ font-family:'Playfair'; font-style:italic; font-weight:500; font-size:38px; line-height:1.25;
           color: var(--teal); margin-top: 26px; }}
    .pts {{ margin-top: 40px; display:flex; flex-direction:column; gap: 16px; }}
    .pt {{ background: rgba(255,255,255,.92); border-radius: 18px; padding: 18px 22px; display:flex; gap:16px;
           align-items:center; box-shadow: 0 2px 10px rgba(27,42,74,.08); }}
    .n {{ font-family:'Poppins'; font-weight:700; font-size:30px; color: var(--orange); flex: 0 0 34px; }}
    .t {{ font-size: 30px; line-height:1.25; color: var(--navy); }}
    .foot {{ background: linear-gradient(0deg, rgba(247,243,236,.95), rgba(247,243,236,0)); padding-top: 40px;
             left:0; right:0; bottom:0; padding: 50px 72px 40px; }}
    """
    pts = "".join(f"<div class='pt'><div class='n'>{i + 1}</div><div class='t'>{_e(it)}</div></div>"
                  for i, it in enumerate(items))
    body = f"""<img class='ph' src='{photo}'><div class='veil'></div>
      <div class='col fit' data-name='photo'><div class='eyebrow'>{_e(spec.get('eyebrow'))}</div>
      <h1>{_e(spec['title'])}</h1>{f"<div class='it'>{_e(spec['subtitle'])}</div>" if spec.get('subtitle') else ''}
      <div class='pts'>{pts}</div></div>{_foot(spec)}"""
    return _page(css, body, w, h)


BUILDERS = {"story": _story, "steps": _steps, "checklist": _checklist, "stat": _stat, "photo": _photo}


def validate(spec: dict) -> list[str]:
    errs = []
    t = spec.get("template")
    if t not in BUILDERS:
        errs.append(f"unknown template {t!r}")
    if not spec.get("title"):
        errs.append("title is required")
    if not spec.get("alt"):
        errs.append("alt text is required (accessibility)")
    for k in ("title", "subtitle", "eyebrow", "stat_label", "source"):
        if spec.get(k) and len(spec[k]) > LIMITS[k]:
            errs.append(f"{k} too long ({len(spec[k])}>{LIMITS[k]} chars)")
    items = spec.get("items") or []
    if len(items) > LIMITS["items"]:
        errs.append(f"too many items ({len(items)}>{LIMITS['items']})")
    errs += [f"item {i + 1} too long" for i, it in enumerate(items) if len(it) > LIMITS["item"]]
    if t == "stat" and (not spec.get("stat") or len(spec["stat"]) > LIMITS["stat"]):
        errs.append("stat template needs a short 'stat' (max 8 chars)")
    if t == "photo":
        if not spec.get("photo") or not (ROOT / spec["photo"]).exists():
            errs.append("photo template needs 'photo' = an existing repo path (content/photos/...)")
        if len(items) > 3:
            errs.append("photo template takes at most 3 items")
    if t in ("steps", "checklist") and len(items) < 2:
        errs.append(f"{t} template needs at least 2 items")
    return errs


def render(record: dict, out_dir: Path | None = None) -> str:
    spec = record.get("image_spec") or {}
    errs = validate(spec)
    if errs:
        raise ImageError("; ".join(errs))
    w, h = SIZES[spec["template"]]
    page = BUILDERS[spec["template"]](spec, w, h)
    out_dir = out_dir or IMAGES_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{record['post_id']}.png"
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as fh:
        fh.write(page)
        html_path = fh.name
    r = subprocess.run(["node", str(ROOT / "engine" / "render.js"), html_path, str(out), str(w), str(h)],
                       capture_output=True, text=True, cwd=ROOT)
    Path(html_path).unlink(missing_ok=True)
    if r.returncode == 3:
        raise ImageError("text does not fit: " + r.stderr.strip() + " (shorten the copy)")
    if r.returncode != 0:
        raise ImageError("render failed: " + (r.stderr or r.stdout).strip()[:500])
    try:
        return str(out.relative_to(ROOT))
    except ValueError:
        return str(out)


def phone_preview(png_path: str, out_path: str, width: int = 360) -> str:
    """Downscale to phone-feed width so a human (or Claude) can check legibility."""
    from PIL import Image
    im = Image.open(png_path)
    h = round(im.height * width / im.width)
    im.resize((width, h), Image.LANCZOS).save(out_path)
    return out_path
