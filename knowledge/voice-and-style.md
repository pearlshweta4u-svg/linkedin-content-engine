# Writing voice and style guide

## Who's talking
A 41-year-old coach from Bangalore who lifts heavy, reads lab reports for a living, and talks to women like a smart friend who happens to know the biochemistry. She is direct and warm, explains the clinical *why*, and isn't afraid to say "I got this wrong".

How she communicates with clients [ME]: "warm, direct, specific; lead with the client's own wins, then new information or asks". Mechanism-led ("explain the clinical why"). Indian food culture is the default (dal, curd, roti, buttermilk, makhana, poha, idli). She uses her clients' own words as hooks.

## Reader
A woman aged 30–50, often in tech or another corporate job, who has been told her reports are "normal", has tried the Instagram plan, and is tired. Secondary readers: doctors and other professionals who will judge credibility.

## Hooks (every post; rule set by Shweta, 9 Nov 2026)
The first paragraph is all most people see before "…see more" (about 140 characters on mobile, about 210 on desktop). It must make the reader curious enough to tap.
- Put the most surprising specific first: a twist, a number, a scene, a belief the post challenges. Never warm up.
- Keep the first paragraph under ~140 characters; one or two short sentences.
- Open a gap the post closes. Don't give away the answer in the hook, and don't promise anything the post doesn't deliver (no clickbait).
- Set `hook_style` and rotate it: `curiosity_gap` ("Twenty years on thyroid medicine. Then, in eight weeks, the same dose became too strong for her."), `surprising_number` ("About 136 million people in India are estimated to have prediabetes…"), `contrarian` ("Your iron report can say 'normal' while your iron stores are close to empty."), `story_drop_in`, `relatable_moment`, `direct_question`.
- Banned openers: "Tomorrow is…", "Today is…", "Did you know…", "Here are…", "In this post…", "As a coach…", "Have you ever wondered…".
- Write 3 hook options while drafting, keep the strongest, and record the other two in `questions_for_shweta` if they're close.
- The image headline echoes the hook's curiosity, never the answer. Photo images: at most 18 words, no lists or steps (Shweta, 10 Nov 2026).

## Storytelling (Monday and Tuesday; rule set by Shweta, 9 Nov 2026)
Story posts must read as a story, not a lab report. Plan the beats first, store them in the record's `story_structure`, then write.

**Tuesday client stories: STAR + lesson**
| Beat | What it holds | Example |
|---|---|---|
| Situation | Who she is (anonymized) and what life felt like, in human terms first | "Early 30s, on thyroid tablets for twenty years, catching a cold almost every week" |
| Task | What had to change, and what made it hard | "Fix what her body was missing without touching her medicine" |
| Action | What we actually did, in plain words, in order | "Iron from day 10, vitamin D, short home workouts" |
| Result | Verified outcome, honest about limits | "Her doctor had to lower her dose" |
| Lesson | One takeaway the reader can act on | "Ask for iron, D and B12, and retest after fixing them" |

**Monday personal stories: story arc**
moment (a specific scene) → struggle (what was hard, or what people assume) → action (what she did) → change (what's different now) → lesson.

**Plain language in story posts** (checked by `engine/quality.py`):
- At most 4 different medical terms, each explained in everyday words the first time. Lead with how she *felt* or *lived* (tired, colds, puffy face), not with markers.
- At most 3 numbers. Prefer "more than tripled" to "8.1 to 27.65".
- No supplement or drug names unless the story needs them.

## Do
- Open with a specific moment, number, or sentence a client actually said. First two lines must earn the "see more" click.
- One idea per post. If there are two, make two posts.
- Short paragraphs (1–3 lines). Plain words. Explain one mechanism properly instead of naming five.
- Indian context: Indian foods, Indian labs ("Thyronorm", "ferritin"), Indian family life.
- Say "I" and "my clients". Use real numbers from the case bank.
- End with a takeaway or one honest question someone would actually answer. A plain statement is fine too.
- 150–300 words. Longer only for Thursday save-worthy posts that need it.
- Hashtags: 0–3, at the end, and only specific ones (#Hashimotos #PCOS #ThyroidHealth). Never #motivation, #mondaymotivation, #health.
- Hinglish: occasionally, one phrase, when it's how the moment was actually said.

## Don't (checked by `engine/quality.py` and by the Humanizer pass)
- Em dashes (—). Use none. A full stop or comma almost always works.
- "Not X, but Y" / "It's not about X. It's about Y."
- One-line dramatic closers ("And that changed everything.") and sayings that sound deep.
- Triads by default ("energy, clarity, and confidence").
- Stock AI words: delve, journey (unless literal), game-changer, unlock, empower, transformative, navigate, landscape, tapestry, testament, pivotal, holistic (unless quoting), "in today's fast-paced world", "let that sink in", "here's the thing", "the truth is".
- Engagement bait: "Comment YES", "Agree?", "Tag a friend", "Save this for later!" (Thursday posts may say *why* it's worth saving once, plainly).
- Emoji bullets, bold section labels, all-caps shouting.
- Medical overreach: "cure", "reverse", "heal your thyroid", "get off medication", guaranteed timelines, dosages, brand names.
- Inventing anything: events, clients, quotes, numbers, studies.
- Fear-mongering about doctors. She works alongside them.

## Hooks log
Every published hook is stored in the post record. The generator must not reuse the opening structure of any of the last 15 posts (e.g. starting with a number, "She sat across from me…", a question). See `python -m engine recent-hooks`.
