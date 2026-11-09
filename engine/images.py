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
SIZES = {"story": (1200, 627), "steps": (1200, 627), "stat": (1200, 627), "checklist": (1080, 1350)}
DEFAULT_TEMPLATE = {"personal_story": "story", "client_story": "story", "educational": "steps",
                    "save_worthy": "checklist", "health_wellness": "stat"}
LIMITS = {"title": 90, "subtitle": 140, "eyebrow": 40, "item": 70, "items": 7, "stat": 8,
          "stat_label": 90, "source": 140}


class ImageError(Exception):
    pass


def _e(s) -> str:
    return html.escape(str(s or ""))


BASE_CSS = """
@font-face { font-family: 'Poppins'; font-weight: 600; src: url('{fonts}/Poppins-600.woff2') format('woff2'); }
@font-face { font-family: 'Poppins'; font-weight: 700; src: url('{fonts}/Poppins-700.woff2') format('woff2'); }
:root { --navy:#1B2A4A; --teal:#138A8A; --orange:#E8833A; --cream:#F7F3EC; --slate:#5B6475; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: {w}px; height: {h}px; overflow: hidden; }
body { background: var(--cream); color: var(--navy); font-family: 'Inter', 'DejaVu Sans', sans-serif;
       position: relative; -webkit-font-smoothing: antialiased; }
.frame { position: absolute; inset: 0; padding: {pad}px; display: flex; flex-direction: column; }
.bar { position: absolute; left: 0; top: 0; bottom: 0; width: 14px; background: var(--teal); }
.eyebrow { font-family: 'Poppins'; font-weight: 600; font-size: 22px; letter-spacing: .14em;
           text-transform: uppercase; color: var(--teal); margin-bottom: 18px; }
h1 { font-family: 'Poppins'; font-weight: 700; line-height: 1.12; color: var(--navy); }
.sub { font-size: 26px; line-height: 1.45; color: var(--slate); }
.foot { position: absolute; left: {pad}px; right: {pad}px; bottom: 34px; display: flex;
        justify-content: space-between; align-items: flex-end; font-size: 18px; color: var(--slate); }
.mark { font-family: 'Poppins'; font-weight: 600; font-size: 22px; color: var(--slate); }
.mark b { color: var(--teal); font-weight: 700; }
.src { max-width: 70%; text-align: right; font-size: 15px; line-height: 1.35; }
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
    .q { width: 88px; height: 8px; border-radius: 4px; background: var(--orange); margin: 6px 0 30px; }
    h1 { font-size: 54px; max-width: 980px; }
    .main { flex: 1; display:flex; flex-direction:column; justify-content:center; padding-bottom: 70px; }
    .sub { margin-top: 26px; max-width: 940px; }
    """
    body = f"""<div class='bar'></div><div class='frame'><div class='main fit' data-name='story'>
      <div class='eyebrow'>{_e(spec.get('eyebrow'))}</div><div class='q'></div>
      <h1>{_e(spec['title'])}</h1>{f"<p class='sub'>{_e(spec['subtitle'])}</p>" if spec.get('subtitle') else ''}
    </div></div>{_foot(spec)}"""
    return _page(css, body, w, h)


def _steps(spec, w, h):
    items = spec.get("items") or []
    n = len(items)
    css = f"""
    h1 {{ font-size: 46px; max-width: 1040px; }}
    .row {{ display:flex; gap: 18px; margin-top: 44px; align-items: stretch; }}
    .step {{ flex: 1; background: #fff; border-radius: 18px; padding: 26px 24px; position: relative;
             box-shadow: 0 2px 0 rgba(27,42,74,.06); border-top: 6px solid var(--teal); }}
    .step:last-child {{ border-top-color: var(--orange); }}
    .num {{ font-family:'Poppins'; font-weight:700; color: var(--teal); font-size: 22px; margin-bottom: 10px; }}
    .step:last-child .num {{ color: var(--orange); }}
    .txt {{ font-size: {26 if n <= 3 else 22}px; line-height: 1.35; color: var(--navy); }}
    .arrow {{ align-self: center; color: var(--slate); font-size: 34px; }}
    .main {{ flex:1; padding-bottom: 60px; }}
    """
    cells = []
    for i, it in enumerate(items):
        if i:
            cells.append("<div class='arrow'>&rarr;</div>")
        cells.append(f"<div class='step'><div class='num'>{i + 1:02d}</div><div class='txt'>{_e(it)}</div></div>")
    body = f"""<div class='bar'></div><div class='frame'><div class='main fit' data-name='steps'>
      <div class='eyebrow'>{_e(spec.get('eyebrow'))}</div><h1>{_e(spec['title'])}</h1>
      <div class='row'>{''.join(cells)}</div></div></div>{_foot(spec)}"""
    return _page(css, body, w, h)


def _checklist(spec, w, h):
    items = spec.get("items") or []
    css = """
    h1 { font-size: 58px; margin-bottom: 18px; }
    .sub { margin-bottom: 34px; }
    ol { list-style: none; display:flex; flex-direction:column; gap: 20px; flex: 1; justify-content: center; }
    li { display:flex; gap: 24px; align-items:center; background:#fff; border-radius: 18px; padding: 30px 30px; }
    .box { flex: 0 0 40px; height: 40px; border-radius: 10px; border: 3px solid var(--teal);
           font-family:'Poppins'; font-weight:700; color: var(--teal); display:flex; align-items:center;
           justify-content:center; font-size: 20px; }
    li:last-child .box { border-color: var(--orange); color: var(--orange); }
    .t { font-size: 32px; line-height: 1.35; color: var(--navy); }
    .main { flex:1; padding-bottom: 90px; display:flex; flex-direction:column; }
    """
    lis = "".join(f"<li><div class='box'>{i + 1}</div><div class='t'>{_e(it)}</div></li>" for i, it in enumerate(items))
    body = f"""<div class='bar'></div><div class='frame'><div class='main fit' data-name='checklist'>
      <div class='eyebrow'>{_e(spec.get('eyebrow'))}</div><h1>{_e(spec['title'])}</h1>
      {f"<p class='sub'>{_e(spec['subtitle'])}</p>" if spec.get('subtitle') else ''}<ol>{lis}</ol>
    </div></div>{_foot(spec)}"""
    return _page(css, body, w, h, pad=76)


def _stat(spec, w, h):
    items = spec.get("items") or []
    css = """
    .grid { flex:1; display:flex; gap: 56px; align-items:center; padding-bottom: 60px; }
    .left { flex: 0 0 430px; }
    .big { font-family:'Poppins'; font-weight:700; font-size: 150px; line-height: 1; color: var(--orange); }
    .lab { font-size: 26px; line-height: 1.4; color: var(--navy); margin-top: 14px; }
    .right { flex: 1; }
    h1 { font-size: 40px; margin-bottom: 22px; }
    ul { list-style:none; display:flex; flex-direction:column; gap: 14px; }
    li { font-size: 24px; line-height: 1.4; padding-left: 26px; position: relative; color: var(--navy); }
    li::before { content:''; position:absolute; left:0; top: 12px; width: 12px; height: 12px; border-radius: 3px; background: var(--teal); }
    """
    lis = "".join(f"<li>{_e(it)}</li>" for it in items)
    body = f"""<div class='bar'></div><div class='frame'><div class='eyebrow'>{_e(spec.get('eyebrow'))}</div>
      <div class='grid fit' data-name='stat'><div class='left'><div class='big'>{_e(spec.get('stat'))}</div>
      <div class='lab'>{_e(spec.get('stat_label'))}</div></div>
      <div class='right'><h1>{_e(spec['title'])}</h1><ul>{lis}</ul></div></div></div>{_foot(spec)}"""
    return _page(css, body, w, h)


BUILDERS = {"story": _story, "steps": _steps, "checklist": _checklist, "stat": _stat}


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
