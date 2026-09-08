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

## Out of scope (must NOT be present)

- No "More Drama!" re-roll button.
- No change to `rewrite_story`, `transcribe`, `narrate`, or the Absurdity path.
- No new endpoint (`/api/rewrite` response only), no new library or framework,
  no ORM/migrations; history UI stays as-is.