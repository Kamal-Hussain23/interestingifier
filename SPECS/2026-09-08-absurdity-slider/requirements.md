# The Absurdity Slider — Requirements

Date: 2026-09-08
Source: ROADMAP.md, fast-finisher stretch features ("An **Absurdity Slider** —
`Slightly Weird`, `Unhinged`, `Total Fever Dream` — that changes the story
prompt.")

## Feature summary

Add a three-way toggle — **Slightly Weird**, **Unhinged**, **Total Fever Dream**
— that changes the system prompt used to rewrite the user's anecdote. Choosing a
level (or flipping the toggle after a story has been generated) re-runs the
rewrite on the latest transcript with that level's prompt and narrates the new
version aloud. The default is **Unhinged**, which keeps today's dramatic
behaviour when the level is not specified.

This is the first fast-finisher stretch feature on top of the completed Cycle 2
pipeline (transcribe → rewrite → persist → narrate → play). It should be simple,
general, and playful: one toggle, one prompt map, one small schema addition.

## Scope — in

- **Backend (`models.py`)**: Add a frozen `Absurdity` enum with the wire tokens
  `slightly_weird`, `unhinged`, `total_fever_dream`, and a `from_token(token)`
  parser that raises a descriptive error for unknown tokens (a schema/contract,
  not regex). Extend the `Story` dataclass with an `absurdity` field (the stored
  wire token).
- **Backend (`services.py`)**: Replace the single `REWRITE_PROMPT` constant with
  a `REWRITE_PROMPTS: dict[Absurdity, str]` map — one prompt per level. The
  current `REWRITE_PROMPT` text becomes the **Unhinged** entry. Change
  `rewrite_story(transcript: str, absurdity: Absurdity = Absurdity.UNHINGED)`
  to send the matching prompt as the first `contents` element (the same SDK
  pattern as today). Keep `@logged`.
- **Backend (`db.py`)**: Add an `absurdity TEXT NOT NULL DEFAULT 'unhinged'`
  column to the `stories` table. `save_story` stores the level; `fetch_story`
  and `list_stories` return it. **Idempotent upgrade (no migration tooling):**
  `init_db` inspects `PRAGMA table_info(stories)` and runs
  `ALTER TABLE stories ADD COLUMN absurdity ...` only when the column is
  missing, so the existing dev DB upgrades safely and existing rows keep the
  default.
- **Backend (`app.py`)**: `POST /api/rewrite` accepts an optional `absurdity`
  JSON field. Absent → `Absurdity.UNHINGED` (backward compatible). Present and
  unparseable → structured `400 invalid_absurdity` (message lists the allowed
  tokens). On success, persist the level with the story. `StoryResponse` stays
  unchanged.
- **Frontend (`frontend/static/app.js` + `index.html` + `style.css`)**:
  - A kitsch three-button segmented toggle (Slightly Weird / Unhinged / Total
    Fever Dream), always visible, default **Unhinged**.
  - The current transcript is kept in a variable so that **changing the toggle
    re-runs the rewrite on that transcript with the new prompt and re-narrates**
    (a pure `buildRewriteBody(transcript, absurdity)` helper + `node:test`
    coverage, `buildRewriteBody` extended backward-compatibly).
  - Toggling before any transcript exists just stores the selected level for the
    upcoming automatic rewrite.

## Scope — out (later milestones / later specs)

- No Visual Engine, Clickbait Title, or "More Drama!" re-roll button — those are
  separate stretch features. (Re-rewrite-on-toggle is *not* a "More Drama!"
  button: it re-runs the same anecdote only when the user changes the level.)
- No changes to `/api/transcribe`, `/api/narrate`, `/`, or `/api/health`.
- No fallback-model retry logic.
- No history-panel rendering (still a static placeholder).
- No schema changes beyond the single idempotent `absurdity` column upgrade.
- No new framework or library (vanilla JS/HTML/CSS only; no ORM/migrations).

## Decisions

- **Wire tokens are the contract.** The frontend sends, and the DB stores,
  snake-case tokens (`slightly_weird` / `unhinged` / `total_fever_dream`). An
  `Absurdity` enum + `from_token` is the single validation point; no ad-hoc
  string matching or regex anywhere.
- **Default is `unhinged`.** Omitting the field (existing clients and tests)
  keeps today's behaviour exactly. The current `REWRITE_PROMPT` becomes the
  Unhinged prompt, so nothing about the default output changes.
- **The "system prompt" stays in `contents`.** Today the rewrite prompt is the
  first `contents` element of the `generate_content` call, and that pattern is
  verified in production. We keep it (swapping in the level's prompt) rather
  than converting to a true `system_instruction`, to minimise churn and keep the
  fix reviewable.
- **Reuse the existing endpoint.** Re-rewrite-on-change calls the same
  `/api/rewrite` with the same transcript and a different level — no new route,
  no new service, no re-recording.
- **Three distinct prompts.** Each level gets its own prompt text; tests assert
  the correct prompt is sent for each level (via the existing fake
  `build_client` seam).
- **Stored as a token string.** The `stories.absurdity` column holds the stable
  wire token so history and API agree, and students only need plain SQLite
  (`ALTER TABLE` + `PRAGMA table_info`) — no migration tooling.

## Context

The Cycle 2 pipeline is complete and verified: the frontend records, transcribes,
rewrites with a single fixed prompt, and narrates with an Aussie voice. The
rewrite prompt lives in `services.py` as `REWRITE_PROMPT` and is currently the
same for every story. `db.py` has a simple `stories` table
(`id, transcript_id, story_text, created_at`); the dev DB already has rows, so
the schema change must upgrade in place. `models.py` holds the frozen
request/response dataclasses. The frontend `buildRewriteBody(transcript)`
already builds the rewrite JSON, and `rewriteStory()` already re-narrates after
each rewrite — so "re-rewrite and re-narrate" is mostly wiring the toggle's
level through the existing flow.

## Status

Spec created 2026-09-08 on branch `feature/2026-09-08-absurdity-slider`,
pending implementation. See `validation.md` for the spec-sync record.