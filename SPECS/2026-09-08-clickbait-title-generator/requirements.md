# The Clickbait Title Generator — Requirements

Date: 2026-09-08
Source: ROADMAP.md, fast-finisher stretch features ("A **Clickbait Title
Generator** that saves a sensationalist headline with each story").

## Feature summary

Have the LLM invent a sensationalist, ALL-CAPS clickbait headline for every
rewritten story, and save it alongside the story so it ships to the frontend
and is stored for history.

A new service call `services.generate_headline(story)` produces the headline
right after `rewrite_story`, inside the existing `POST /api/rewrite` request.
The response contract grows a `headline` field, and the `stories` table grows a
`headline` column (idempotent upgrade, same pattern as `absurdity`). The story
panel shows the headline above the story text.

## Scope — in

- **Service (`services.py`)**:
  - `HEADLINE_PROMPT`, `HEADLINE_MODEL` (reuse the rewrite model,
    `gemini-3.1-flash-lite`, to keep calls cheap and familiar), and a
    `@logged generate_headline(story: str) -> str` function mirroring
    `rewrite_story`: one `generate_content` call with `[HEADLINE_PROMPT,
    story]`, `RuntimeError("Gemini returned an empty headline response.")` on
    missing text.
  - **Force ALL-CAPS server-side**: return `response.text.upper()`. The
    displayed and stored headline is guaranteed all-caps regardless of what the
    model emits — a contract, not a regex (no ad-hoc string matching).
- **Models (`models.py`)**:
  - `Story` gains `headline: str = ""`.
  - `StoryResponse` gains `headline: str = ""` (default keeps older
    constructions working).
- **Persistence (`db.py`)**:
  - `stories` `CREATE TABLE` gains `headline TEXT NOT NULL DEFAULT ''`.
  - `upgrade_stories_schema` also adds the `headline` column to pre-existing
    tables via the same check-then-`ALTER TABLE` pattern (idempotent, old rows
    get `''` automatically). Still one PRAGMA+ALTER helper, just two columns.
  - `save_story` gains a `headline: str = ""` keyword parameter, stores it, and
    returns the row with it; `fetch_story` and `list_stories` round-trip it.
- **API (`app.py`, `POST /api/rewrite`)**: after a successful story rewrite,
  call `services.generate_headline(story)`. On success persist story + headline
  and return `{"story": ..., "headline": ...}`. On a generic headline failure,
  **degrade gracefully**: still persist and return the story with
  `headline: ""` (never throw away a good story because the headline call
  flaked). A `NotImplementedError` raises the existing structured 501 to stay
  consistent with the other routes.
- **Frontend**:
  - `index.html`: a `#story-headline` element in the story panel, hidden by
    default.
  - `app.js`: pure, testable `formatHeadline(value) -> str` (empty/undefined →
    `""`, otherwise trimmed) plus browser wiring in `rewriteStory`: set
    `#story-headline` text and toggle its `hidden` attribute. Narrate keeps
    using only `story`.
  - `style.css`: a kitsch `.headline` (neon gradient, punchy letter-spacing)
    so the caption reads as part of the brand; hidden element is invisible.

## Scope — out (later milestones / later specs)

- No change to the transcript narrate path, `transcribe`, `narrate`, or the
  Absurdity logic itself — `rewrite_story` is not modified.
- No "More Drama!" re-roll button — separate stretch feature with its own spec.
- No history UI work: `list_stories` returns the headline in the model but the
  history panel stays as-is.
- No new library, framework, or DB tooling — the established keep-simple SQLite
  pattern applies. No ORM, no migrations.

## Decisions

- **Separate Gemini call inside `/api/rewrite`** (user decision 2026-09-08):
  headline generation is its own `generate_headline` call that runs right after
  `rewrite_story` in the same request. The rewrite prompt and response text
  parsing stay untouched — no fragile two-field response to slice up.
- **Extend the `/api/rewrite` response** (user decision 2026-09-08): the
  headline arrives in the same JSON the frontend already consumes
  (`StoryResponse.headline`). No new endpoint.
- **Force ALL-CAPS server-side** (user decision 2026-09-08): `.upper()` on the
  service's return value enforces the contract; the frontend does no case
  tricks.
- **Headline failure degrades to `""`**: the story still saves and ships; the
  frontend hides an empty headline. Elegant general rule — a doodad never
  blocks the main deliverable. (If you would rather fail the whole request,
  say so at spec review.)
- **Backward compatibility is additive and therefore kept** (per "ask per
  instance", this instance needs no ask): the response field and DB column both
  default to `""`, `save_story(…, headline="")` and `StoryResponse(story=…)`
  keep their old call shapes, and old rows upgrade to `""` automatically. No
  existing consumer or data shape is altered.
- **Model choice**: `HEADLINE_MODEL = "gemini-3.1-flash-lite"` — same model as
  the rewrite for predictability, latency, and cost.

## Context

`services.py` already has the `@logged` + `build_client` + single
`generate_content` shape (see `rewrite_story`); `generate_headline` is a fifth
function in that exact family, so it needs no new plumbing. `db.py` already
established the check-then-`ALTER TABLE` upgrade in `upgrade_stories_schema`,
so the `headline` column follows a proven, idempotent path (old
`interestingifier.db` databases from earlier milestones upgrade in place).
`app.rewrite()` already owns the rewrite → save → respond sequence; the
headline call slots in between save and respond. When the Visual Engine feature
merges, its `celebrateStory()` fires from `rewriteStory()` too — the same single
hook, so headline + confetti coexist without extra wiring.

## Status

Spec created 2026-09-08 on branch `feature/2026-09-08-clickbait-title-generator`,
pending implementation. See `validation.md` for the spec-sync record.