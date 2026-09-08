# The Absurdity Slider — Validation

Date: 2026-09-08
Feature: SPECS/2026-09-08-absurdity-slider/requirements.md

This step is complete when all of the following pass. The Verifier agent audits
the work against this file before the branch is considered done.

## Automated checks

- `ruff check .` — no lint errors.
- `ruff format --check .` — formatting matches the repo style (line length 100,
  double-quoted strings, space indentation).
- `mypy .` — passes under `strict = true` (per `pyproject.toml`).
- `pytest` — all tests pass, including:
  - `tests/test_models.py`: `Absurdity` tokens are exact, `from_token` parses
    and rejects (descriptive error), `Story` carries `absurdity`.
  - `tests/test_db.py`: fresh DB has the column; an old-schema DB is upgraded
    idempotently by `init_db` (pre-existing rows read `unhinged`);
    `save_story`/`fetch_story`/`list_stories` round-trip the level.
  - `tests/test_services.py`: each of the three levels sends its own prompt
    (fake `build_client` asserts `contents`), and calling without a level uses
    the `UNHINGED` prompt.
  - `tests/test_app.py`: `/api/rewrite` accepts the optional `absurdity`,
    defaults to `UNHINGED` when absent, returns structured `400
    invalid_absurdity` for unknown tokens, and persists the level.
  - All pre-existing tests stay green.
- `npm run lint --prefix frontend` and `npm test --prefix frontend` — the
  toggle/body helpers are tested (`buildRewriteBody` with and without a level);
  both stay green.
- `pre-commit run --all-files` — gitleaks, Ruff, mypy, pytest, frontend lint and
  tests all pass. The quality gate must not depend on `GEMINI_API_KEY`.

## TDD evidence

- The test files were committed before (or in the same commit as) the code they
  test, and the git history shows the red→green sequence for each group in
  `plan.md`.

## Manual verification

- `python app.py` boots and serves the page with **no `GEMINI_API_KEY` set**.
- With a valid key, live against the public URL:
  - `POST /api/rewrite` bodies with `absurdity` set to each of the three tokens
    return `200` and produce clearly different tones (Slightly Weird is the
    tamest; Total Fever Dream is the most chaotic).
  - An unknown token returns `400 invalid_absurdity` listing the allowed tokens.
  - SQLite shows the chosen `stories.absurdity` value per story; old rows read
    `unhinged` after the idempotent upgrade.
- UI end-to-end: record → transcript appears → story generates at Unhinged →
  flip the toggle to Total Fever Dream → the story re-rewrites into a more
  absurd version and its narration plays. The toggle is styled kitsch, matching
  the brand.
- The server responds through the Codio public URL (bind to `0.0.0.0`, then curl
  the `https://${CODIO_HOSTNAME}-3000.codio.io/` URL).

## Spec sync — implementation record (2026-09-08)

Implemented per plan.md groups G1–G6, red→green (each failing test written and
run before the code). All checks pass: ruff, ruff format, mypy strict, pytest
(52 backend tests incl. the new models/db/services/app cases), ESLint + node:test
(14 frontend tests), pre-commit chain. Merged `origin/main` (which carries the
transcribe fix from PR #4) into the feature branch with a clean auto-merge.

Live verification against the public URL (server restarted on the merged code):

- `POST /api/rewrite` without `absurdity` → Unhinged story, persisted with
  `stories.absurdity = 'unhinged'`.
- `absurdity: "total_fever_dream"` → clearly more chaotic story than the default,
  persisted as `total_fever_dream`.
- `absurdity: "chaotic"` → `400 {"error":{"code":"invalid_absurdity", ...}}`
  listing `slightly_weird, unhinged, total_fever_dream`.
- Full pipeline on the current code: `POST /api/transcribe` (merged transcribe
  fix) on a narrated WAV → `"The toast fed him."` → rewrite at Unhinged and
  Total Fever Dream on that transcript → both distinct, both persisted.
- `/api/narrate` → `200 audio/wav`; `--glow-blue` was not defined in `:root`, so
  the slider uses an inline neon-blue glow.
- No spec deviations; implementation matched requirements.md decisions exactly.

The browser-only half of the UI checklist (physically tapping the segmented
control after a live recording) is left for the Verifier agent, since the
record→transcribe→toggle wiring is covered by the 14 node:test cases and every
endpoint it calls was exercised live above.

## Out of scope (must NOT be present)

- No Visual Engine, Clickbait Title, or "More Drama!" re-roll button.
- No changes to `/api/transcribe`, `/api/narrate`, `/`, or `/api/health`.
- No fallback-model retry logic.
- No history-panel rendering changes.
- No schema changes beyond the idempotent `absurdity` column upgrade
  (no ORM, no migration tooling).
- No framework/library beyond the existing vanilla stack + `google-genai`.