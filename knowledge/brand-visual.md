# Visual brand guide (proposal, needs Shweta's approval)

Status: **in use** (approved for build by Shweta, 9 Nov 2026). Images are rendered by `engine/images.py` from four HTML templates (story, steps, checklist, stat) using these tokens; Poppins is bundled in `assets/fonts/`, body text uses Inter. Output: `content/images/<post-id>.png`.

Basis: the colours she already uses in her client documents ("Keerthi format": dark blue, teal, orange) and her invoices (teal, dark, grey) [ME]. No logo is defined in memory, so none is invented. Use a text wordmark until she supplies one.

| Token | Hex | Use |
|---|---|---|
| Deep navy | `#1B2A4A` | Headlines, backgrounds for quote cards |
| Teal | `#138A8A` | Primary accent, highlight bars, chart series 1 |
| Warm orange | `#E8833A` | One call-out per image only (a number, a warning) |
| Soft cream | `#F7F3EC` | Default background (calm, not clinical white) |
| Slate grey | `#5B6475` | Body text, captions |

Typography (free; Google Fonts and Canva both have them): **Poppins SemiBold** for headlines, **Inter** for body. Never more than 2 weights in one image.

Formats (mobile-first, revised 9 Nov 2026 after a phone-legibility check):
- 1080 × 1080 px square: story, steps and stat cards. Shown ~360px wide on phones, so body text is ≥30px and headlines 60–80px.
- 1080 × 1350 px portrait (4:5): Thursday checklists; takes the most feed space on mobile.
- Not 1200 × 627 landscape: on a phone it shrinks to ~30% and body text becomes unreadable.
- Rendered at 2× (2160 px wide) for sharpness.
- Wordmark bottom-left: "TrainWithShweta" in Poppins 600, slate grey, ~24 px.

Rules:
- One idea per image; at most ~25 words of text. The image adds something (a diagram, a lab-marker chart, a checklist), not the post's first line repeated.
- No stock photos of women holding their stomachs or pills.
- Lab-marker visuals: show ranges as horizontal bars, numbers in teal, the "watch" number in orange.
- Contrast check: text ≥ 4.5:1 against its background.

Images by day:
- Mon: usually none, or a real photo of Shweta (from the shared Drive folder) when it fits.
- Tue: an anonymised before/after lab-marker card (only verified numbers) or none.
- Wed: one simple mechanism diagram (e.g. T4 → T3 with the cofactors).
- Thu: a portrait checklist or infographic.
- Fri: a simple concept visual or none.
