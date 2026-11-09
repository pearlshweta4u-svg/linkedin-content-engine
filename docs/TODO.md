# To-do

## Waiting on Shweta
- [ ] LinkedIn Company Page + developer app + token (docs/SETUP.md steps 1–4).
- [ ] Review the 5 sample posts; answer the `questions_for_shweta` in each.
- [ ] Answer `knowledge/gaps.md` (own health story, why coaching, story details), ideally as one 10-minute voice-note transcript.
- [ ] Approve or adjust the visual style in `knowledge/brand-visual.md`; share Canva brand kit / logo if one exists.
- [ ] Explicit go-ahead before automatic publishing (only after she's happy with quality).

## Image generation (deferred by Shweta, 9 Nov 2026: "need to figure out")
Options to decide between:
1. **Free, template-based**: HTML/SVG templates in brand colours rendered to PNG with the pre-installed headless browser. Best for Thursday checklists, lab-marker cards and diagrams. No cost, fully consistent branding. Recommended first step.
2. **AI image API** (OpenAI / Google Imagen): illustrations and concept art; roughly ₹3–10 per image; needs an API key (stored as a network secret, never in the repo).
3. **Canva**: no Canva connector is available in this environment today. Manual, or via Canva's API with an Enterprise/Connect app.
When decided: implement `engine/images.py`, set `images_enabled: true`, and add an image step to `runbooks/generate.md` (the publisher already uploads images).

## Later
- [ ] Retry the Fathom connector (errored 9 Nov 2026) and mine transcripts for verbatim client phrasing and new cases.
- [ ] Apply for Community Management API access if analytics automation becomes important.
- [ ] Quarterly performance review using `engine history` → adjust pillar weights.
