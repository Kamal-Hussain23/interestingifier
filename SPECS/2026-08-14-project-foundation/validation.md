# Project Foundation — Validation

Date: 2026-08-14
Feature: SPECS/2026-08-14-project-foundation/requirements.md

This step is complete when all of the following pass. The Verifier agent audits
the work against this file before the branch is considered done.

## Automated checks

- `ruff check .` — no lint errors.
- `ruff format --check .` — formatting matches the repo style (line length 100,
  double-quoted strings, space indentation).
- `mypy .` — passes under `strict = true` (per `pyproject.toml`).
- `pytest` — all tests pass, including:
  - `tests/test_db.py`: `init_db()` creates `transcripts`, `stories`, and
    `metadata`; calling it twice is harmless.
  - `tests/test_app.py`: `GET /` returns 200 with HTML; `GET /api/health`
    returns 200 with `{"status": "ok"}`.
  - A logging test showing the `@logged` decorator emits log output.
- `pre-commit run --all-files` — gitleaks, Ruff, mypy, pytest, and the frontend
  `npm run lint` / `npm test` hooks all pass.

## TDD evidence

- Tests were committed before (or in the same commit as) the code they test;
  the git history shows the red→green sequence for each group.

## Manual verification

- `python app.py` starts the server bound to `0.0.0.0:3000`.
- `curl http://localhost:3000/` returns the placeholder HTML page (HTTP 200).
- `curl http://localhost:3000/api/health` returns `{"status": "ok"}`.
- The three tables `transcripts`, `stories`, and `metadata` exist in
  `interestingifier.db`, verified via Python (`sqlite3.connect(...)` plus
  `SELECT name FROM sqlite_master WHERE type='table'`). The `sqlite3` CLI is
  not installed on the Codio box, so the check is done from Python.
- The app is reachable through the Codio public URL:
  `curl https://${CODIO_HOSTNAME}-3000.codio.io/` succeeds.

## Spec sync

- The implemented layout, schema, and routes match this spec and the roadmap
  (Cycle 1, Step 1). Three approved deviations were recorded during
  implementation:
  - A `.gitignore` was added for repository hygiene (generated files stay out
    of the repo).
  - `pyproject.toml` gained `pythonpath = ["."]` so plain `pytest` can import
    the app modules (see requirements.md "Decisions").
  - The pre-commit mypy hook now uses the system mypy rather than the isolated
    `mirrors-mypy` env, which lacked Flask and caused false "untyped decorator"
    errors (see requirements.md "Decisions").

## Out of scope (must NOT be present)

- No Gemini API calls, keys, or service helpers.
- No transcribe/rewrite/narrate endpoints.
- No save/fetch persistence functions beyond schema creation.
- No kitsch styling or recording UI (that is Step 2's spec).