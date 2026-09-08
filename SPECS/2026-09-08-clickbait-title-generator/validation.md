# The Clickbait Title Generator — Validation

Date: 2026-09-08
Feature: SPECS/2026-09-08-clickbait-title-generator/requirements.md

This step is complete when all of the following pass. The Verifier agent audits
the work against this file before the branch is considered done.

## Automated checks

- `pytest` — complete and green, including the new cases:
  - service: `generate_headline` sends `HEADLINE_MODEL` + `[HEADLINE_PROMPT,
    story]`; returns the model text uppercased; empty response raises the
    documented `RuntimeError`.
  - db: fresh schema has `headline` default `''`, upgrdades idempotently, and
    `save_story`/`fetch_story`/`list_stories` round-trip it; old rows keep
    `''`.
  - api: `/api/rewrite` returns `{"story", "headline"}`; headline persists;
    generic headline failure degrades to `headline: ""` with a `200` and a saved
    story; `NotImplementedError` → structured 501. All pre-existing tests stay
    green (backward-compat defaults on `StoryResponse` and `save_story`).
- `npm test --prefix frontend` — `formatHeadline` covered (empty/undefined →
  `""`, trimmed pass-through); all pre-existing frontend tests stay green.
- `ruff check .`, `ruff format --check .`, `mypy .` — clean; strict typing holds.
- `npm run lint --prefix frontend` — ESLint clean.
- `pre-commit run --all-files` — all hooks green without `GEMINI_API_KEY`.

## TDD evidence

- For each group in `plan.md`: the Red test was written first and observed to
  fail, then the minimal Green code landed. Git history shows the sequence for
  at least one test per group (service, persistence, API, frontend pure helper).

## Manual verification

- Live `POST /api/rewrite` returns `{"story": …, "headline": "ALL CAPS…"}`.
- The story panel shows the headline above the story in the kitsch style; when
  the headline is empty the element is hidden and the panel looks exactly as
  before.
- The saved row in `interestingifier.db` contains the ALL-CAPS headline; older
  rows have `headline = ''` and still render fine.
- Re-recording produces a fresh story *and* a fresh headline; slider
  re-rewrites (once that feature merges) do the same because both flow through
  `rewriteStory`.
- The server answers through the Codio public URL (per AGENTS.md rules: bind to
  `0.0.0.0`, curl the `https://${CODIO_HOSTNAME}-3000.codio.io/` URL).

## Spec sync

- On merge, update ROADMAP.md to mark "Clickbait Title Generator" done and
  record any approved deviations + implementation notes here (as the previous
  features did).

## Implementation record (2026-09-08)

Implemented on branch `feature/2026-09-08-clickbait-title-generator` (PR #10)
via the TDD groups in plan.md, all Red-first:

- **G1 service** — `generate_headline(story)` in `services.py`: sends
  `HEADLINE_MODEL` + `[HEADLINE_PROMPT, story]`, raises `RuntimeError` on an
  empty response, and returns the model text uppercased via `.upper()`.
- **G2 persistence** — `headline TEXT NOT NULL DEFAULT ''` in the fresh
  `stories` schema, a second idempotent `ALTER TABLE` branch in
  `upgrade_stories_schema`, `save_story(..., headline="")` argument, and the
  column threaded through `fetch_story`/`list_stories` and the `Story` model.
  `StoryResponse` gained `headline: str = ""` (backward-compat default).
- **G3 API** — `rewrite()` calls `generate_headline_result(story)`: a stub's
  `NotImplementedError` maps to the structured `501 not_implemented`, any other
  failure degrades `headline` to `""` with the story still saved and returned;
  `db.save_story` persists the headline. The mirror helper `story_result` kept
  `rewrite()` under ruff's return limit.
- **G4 frontend** — `formatHeadline()` pure helper, `#story-headline` element
  above the story (hidden until a headline arrives, cleared on error),
  `.headline` kitsch bar CSS.
- **G5 gate + live** — `ruff`, `ruff format`, `mypy`, `pytest` (79),
  `npm test` (19), `npm run lint`, and `pre-commit run --all-files` all green.

Live verification through the Codio public URL: two `POST /api/rewrite` calls
with a real Gemini key returned ALL-CAPS sensational headlines plus fresh
stories; `interestingifier.db` rows 20–21 carry the headline while older rows
(18–19) keep `''` exactly as the upgrade intends.

Notes/deviations: the headline model was reached with the same
`gemini-3.1-flash-lite` used for rewrites (as planned). No material deviation
from this spec.

## Out of scope (must NOT be present)

- No "More Drama!" re-roll button.
- No change to `rewrite_story`, `transcribe`, `narrate`, or the Absurdity path.
- No new endpoint (`/api/rewrite` response only), no new library or framework,
  no ORM/migrations; history UI stays as-is.