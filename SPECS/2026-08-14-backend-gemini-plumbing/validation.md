# Backend + Gemini Plumbing — Validation

Date: 2026-08-14
Feature: SPECS/2026-08-14-backend-gemini-plumbing/requirements.md

This step is complete when all of the following pass. The Verifier agent audits
the work against this file before the branch is considered done.

## Automated checks

- `ruff check .` — no lint errors.
- `ruff format --check .` — formatting matches the repo style (line length 100,
  double-quoted strings, space indentation).
- `mypy .` — passes under `strict = true` (per `pyproject.toml`).
- `pytest` — all tests pass, including:
  - `tests/test_config.py`: `get_gemini_api_key()` returns the env value when
    `GEMINI_API_KEY` is set, and raises a clear `RuntimeError` when it is unset
    or blank.
  - `tests/test_models.py`: `asdict()` of `TranscriptResponse`, `StoryResponse`,
    and `ErrorResponse` yields the documented JSON shapes.
  - `tests/test_services.py`: `transcribe_audio`, `rewrite_story`, and
    `narrate_story` each raise `NotImplementedError`, and are `@logged`.
  - `tests/test_app.py`: the three new routes return `400` on invalid input and
    `501` (code `not_implemented`) on valid input; `GET /api/health` still
    returns `200` `{"status": "ok"}`.
- `npm run lint --prefix frontend` and `npm test --prefix frontend` — the
  frontend is untouched by this step and both stay green.
- `pre-commit run --all-files` — gitleaks, Ruff, mypy, pytest, frontend lint,
  and frontend tests all pass.

## TDD evidence

- The test files were committed before (or in the same commit as) the code they
  test, and the git history shows the red→green sequence for each group in
  `plan.md`.

## Manual verification

- `python app.py` boots and serves the page with **no `GEMINI_API_KEY` set** —
  the app must not fail to start without a key.
- `curl -X POST http://localhost:3000/api/transcribe` (no file) → HTTP `400`
  with body `{"error": {"code": "missing_audio", ...}}`.
- `curl -X POST -F "audio=@/tmp/sample.webm" http://localhost:3000/api/transcribe`
  → HTTP `501` with body `{"error": {"code": "not_implemented", ...}}`.
- `curl -X POST -H "Content-Type: application/json" -d '{"transcript":"hi"}' \
  http://localhost:3000/api/rewrite` → HTTP `501` with code `not_implemented`.
- `curl -X POST -H "Content-Type: application/json" -d '{"story":"hi"}' \
  http://localhost:3000/api/narrate` → HTTP `501` with code `not_implemented`.
- The server responds through the Codio public URL (bind to `0.0.0.0`, then
  curl the `https://${CODIO_HOSTNAME}-3000.codio.io/` URL).

## Spec sync

- The implemented endpoints, error contract, service signatures, and API-key
  seam match this spec and the roadmap (Cycle 1, Step 3). Verified 2026-08-14 on
  branch `feature/2026-08-14-backend-gemini-plumbing`.
- **Approved deviations / notes:**
  - The three pipeline handlers live at module level and are registered with
    `app.add_url_rule` inside `create_app`, rather than being defined inline with
    `@app.route` as `plan.md` sketched. Inline definitions pushed `create_app`'s
    McCabe complexity to 15 (> Ruff's limit of 8); the module-level handlers keep
    each function small and readable. Behaviour is identical, and `/` and
    `/api/health` still use the inline `@app.route` style.
  - `tests/test_app.py` types its `error_code` helper parameter as
    `werkzeug.test.TestResponse` (the Flask test client's response type) to keep
    `mypy --strict` green.
  - The roadmap's Cycle 2 feature 3 and this spec's `narrate_story` stub both
    now explicitly require the TTS config to request a funny, energetic Aussie
    accent (MISSION.md's signature voice).

## Out of scope (must NOT be present)

- No real Gemini API calls, Gemini SDK, or HTTP calls to Google — the service
  helpers only raise `NotImplementedError`.
- No persistence writes: nothing is inserted into SQLite in this step.
- No frontend changes (`frontend/` untouched; no `fetch`/POST from the browser).
- No changes to the existing `/` or `/api/health` routes.
- No new logging machinery beyond reusing `@logged`.
- No new database schema or migration tooling.