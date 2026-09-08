# The "More Drama!" Re-roll — Requirements

Date: 2026-09-08
Source: ROADMAP.md, fast-finisher stretch features ("A **'More Drama!'** re-roll
button that creates an alternate spin on the same anecdote without
re-recording").

## Feature summary

Add a **More Drama!** button that re-rewrites the *current* transcript into a
fresh, genuinely-different story — an alternate spin — without the user
re-recording. Each click threads a random dramatic "twist" into the rewrite at
the currently-selected absurdity level, so consecutive spins differ instead of
repeating near-identical text. Each re-roll saves as a brand-new story row, the
same way the Absurdity Slider already stores its re-rewrites.

The backend reuses `POST /api/rewrite` with an optional `drama` flag — no new
endpoint, no schema change, and the response contract is unchanged.

## Scope — in

- **Service (`services.py`)**:
  - A small curated `DRAMA_TWISTS` list — short dramatic-angle instructions
    (e.g. "Retell it as a locked-room courtroom drama.", "Make it feel like an
    action-movie trailer.", "Tell it as a villain's last confession.") — a
    constant, strings, non-empty.
  - `pick_drama_twist(pick: Callable[[list[str]], str] = random.choice) -> str`
    — one random twist from the list, randomness injectable for tests (same
    pattern as the Visual Engine's `makeConfettiPieces`).
  - `rewrite_story(transcript, absurdity=UNHINGED, twist: str | None = None)`
    — when `twist` is given, inject it into the request contents between the
    level prompt and the transcript (`[REWRITE_PROMPTS[absurdity], twist,
    transcript]`). `twist=None` keeps today's exact behaviour. No change to the
    level prompts themselves.
- **API (`app.py`, `POST /api/rewrite`)**:
  - `parse_drama_flag(data) -> bool`: absent/missing or anything non-true →
    `False`; `true` → `True` (lenient, additive).
  - When `drama` is true the route calls `services.pick_drama_twist()` and
    passes it as `twist=` to `rewrite_story`. Otherwise `twist` is omitted.
  - Saving unchanged: the story is a brand-new row via the existing
    `db.save_story` inserted fresh each request — the transcript already links
    to many stories, so history accumulates variants naturally.
  - Response shape unchanged (`StoryResponse`).
- **Frontend**:
  - `index.html`: a kitsch "More Drama!" button in the story panel, disabled by
    default, enabled once a transcript exists.
  - `app.js`: pure `buildRewriteBody(transcript, absurdity, drama = false)` —
    when `drama` is truthy the body includes `"drama": true`; otherwise the body
    is byte-for-byte what it was before (backward compatible). Browser wiring:
    `rewriteStory(transcript, drama = false)` selects the drama body; the
    button's click handler re-runs `rewriteStory(currentTranscript, true)` (and
    is disabled before the first transcript arrives); the fresh story re-narrates
    exactly like a slider re-rewrite.
  - `style.css`: a vivid kitsch button matching the existing brand.

## Scope — out (later milestones / later specs)

- No new endpoint, no response-contract change, no schema change, no new model
  fields.
- No change to `services.rewrite_story`'s signature for existing callers beyond
  the optional `twist` keyword — the Absurdity slider path is untouched.
- No seed/escalation logic (each click is a fresh random twist at the current
  level, not an absurdity ladder).
- No history UI work; the Visual Engine, Clickbait Title Generator, and
  narrator carry over automatically because they all hang off the same
  `rewriteStory` / `rewrite()` path.

## Decisions

- **Optional `drama` flag on `POST /api/rewrite`** (user decision 2026-09-08):
  no new route; behaviour is a flag on the existing rewrite, mirroring how the
  Clickbait headline rides the same endpoint.
- **Random twist at the current absurdity level** (user decision 2026-09-08):
  a random `DRAMA_TWISTS` phrase is injected into the prompt, at whatever level
  the slider has selected. Consecutive clicks differ; the user's chosen level is
  respected.
- **New story row per re-roll** (user decision 2026-09-08): each spin is a fresh
  `stories` row linked to the same transcript — the exact persistence behaviour
  the Absurdity Slider already uses, so history accumulates variants with no
  schema change and no overwrite semantics.
- **Backward compatibility is additive and therefore kept** (per "ask per
  instance", this instance needs no ask): `rewrite_story`'s new `twist`
  keyword defaults to `None`, `buildRewriteBody` emits the old body when `drama`
  is falsy, the `drama` flag is optional and lenient, and the response is
  byte-for-byte unchanged. No existing consumer or data shape is altered.
- **Randomness injectable for tests**: `pick_drama_twist(pick)` takes its
  random source as an argument (defaults to `random.choice`) so node/pytest can
  assert a deterministic choice.
- **Logging**: services stay `@logged` (the decorator already covers
  `rewrite_story`); `pick_drama_twist` is a trivial pure picker on a module
  constant and needs no business logging.

## Context

The Absurdity Slider already proved the pattern this feature reuses wholesale:
re-request `rewrite_story(transcript)` from the frontend's stored
`currentTranscript`, and each call inserts a new `stories` row via the existing
`save_story`. "More Drama!" adds exactly two new things to that proven path: a
`drama` flag on the route that selects a random twist, and a button in the UI
that calls it. When the Visual Engine and Clickbait headlines merge, the re-roll
gets both for free because they hang off the same `rewriteStory()` /
`rewrite()` seam. `parse_drama_flag` mirrors `parse_absurdity` as the single
validation point for the new field.

## Status

Spec created 2026-09-08 on branch `feature/2026-09-08-more-drama`, pending
implementation. See `validation.md` for the spec-sync record.