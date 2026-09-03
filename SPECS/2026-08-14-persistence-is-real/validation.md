# Persistence is real — Validation

Date: 2026-08-14
Feature: SPECS/2026-08-14-persistence-is-real/requirements.md

This step is complete when all of the following pass. The Verifier agent audits
the work against this file before the branch is considered done.

## Automated checks

- `ruff check .` — no lint errors.
- `ruff format --check .` — formatting matches the repo style (line length 100,
  double-quoted strings, space indentation).
- `mypy .` — passes under `strict = true` (per `pyproject.toml`).
- `pytest` — all tests pass, including:
  - `tests/test_models.py`: `Transcript` and `Story` dataclasses serialise to
    the documented shapes.
  - `tests/test_db.py`: the new save/fetch tests from `plan.md` groups 2–3
    (round-trip, missing ids → `None`, foreign-key `IntegrityError`, empty and
    newest-first `list_stories`), plus the existing schema tests still pass
    after the `row_factory` change.
  - `tests/test_app.py`: the pipeline endpoints still return `400` on invalid
    input and `501` (code `not_implemented`) on valid input; `GET /api/health`
    still returns `200` `{"status": "ok"}`.
- `npm run lint --prefix frontend` and `npm test --prefix frontend` — the
  frontend is untouched by this step and both stay green.
- `pre-commit run --all-files` — gitleaks, Ruff, mypy, pytest, frontend lint,
  and frontend tests all pass.

## TDD evidence

- The test files were committed before (or in the same commit as) the code they
  test, and the git history shows the red→green sequence for each group in
  `plan.md`.

## Manual verification

- `python app.py` boots and serves the page; `/api/health` returns `200`.
- The `interestingifier.db` file is created on startup.
- A REPL round-trip against a throwaway db path confirms
  `save_transcript` → `save_story` → `fetch_story` / `list_stories` return the
  saved data with `id`/`transcript_id`/`created_at` populated.
- The pipeline endpoints still return `501 not_implemented` — no wiring happened
  this step.
- The server responds through the Codio public URL (bind to `0.0.0.0`, then
  curl the `https://${CODIO_HOSTNAME}-3000.codio.io/` URL).

## Spec sync

- The implemented functions match this spec and the roadmap (Cycle 1, Step 4):
  the DB initialises, save/fetch for transcripts and stories exists, and a
  history (`list_stories`) helper is included. Verified 2026-08-14 on branch
  `feature/2026-08-14-persistence-is-real`.
- **Approved deviations / notes:**
  - `get_connection` additionally runs `PRAGMA foreign_keys = ON`. SQLite does
    not enforce foreign keys by default, so without this the schema's
    `REFERENCES transcripts(id)` would not raise for a dangling
    `transcript_id`; the spec's `IntegrityError` test for `save_story` required
    it. One line, backward compatible, and it makes the declared contract real.
  - `save_transcript` / `save_story` assert `cursor.lastrowid is not None`
    before converting to `int`, purely to satisfy `mypy --strict` (typeshed
    types `lastrowid` as `int | None`). Behaviour is unchanged.
  - The existing `interestingifier.db` in the repo root was created by the
    earlier schema-init work and is untouched by this step's round-trip checks
    (those used `tmp_path` and `/tmp` files only).

## Out of scope (must NOT be present)

- No changes to `app.py` routes; endpoints still return `501`.
- No frontend changes (`frontend/` untouched).
- No real Gemini calls, Gemini SDK, or HTTP calls to Google.
- No schema changes, migrations, or new tables; `metadata` unused.
- No API-key work (`config.py` untouched).
- No new logging machinery beyond reusing `@logged`.