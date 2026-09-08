# Vocalizing the Absurd — Validation

Date: 2026-09-03
Feature: SPECS/2026-09-03-vocalizing-the-absurd/requirements.md

This step is complete when all of the following pass. The Verifier agent audits
the work against this file before the branch is considered done.

## Automated checks

- `ruff check .` — no lint errors.
- `ruff format --check .` — formatting matches the repo style (line length 100,
  double-quoted strings, space indentation).
- `mypy .` — passes under `strict = true` (per `pyproject.toml`).
- `pytest` — all tests pass, including:
  - `tests/test_services.py`: `narrate_story` returns audio bytes
    (Gemini TTS call faked), while `transcribe_audio` and `rewrite_story`
    still work.
  - `tests/test_app.py`: narrate POST returns `200` with audio bytes
    and correct MIME type; `missing_story` still returns `400`; all other
    endpoints unchanged.
  - `tests/test_db.py`: unchanged, still green.
- `npm run lint --prefix frontend` and `npm test --prefix frontend` — the new
  narration flow is tested; both stay green.
- `pre-commit run --all-files` — gitleaks, Ruff, mypy, pytest, frontend lint and
  tests all pass. Note: running the app/service requires `GEMINI_API_KEY`; the
  pre-commit quality gate itself must not depend on it.

## TDD evidence

- The test files were committed before (or in the same commit as) the code they
  test, and the git history shows the red→green sequence for each group in
  `plan.md`.

## Manual verification

- `python app.py` boots and serves the page with **no `GEMINI_API_KEY` set** —
  the app must still start; the key is only required when a narrate request
  actually reaches Gemini.
- `curl -X POST -H "Content-Type: application/json" -d '{"story":"THE BUS FEARED HIM."}' \
  http://localhost:3000/api/narrate` → HTTP `200` with audio bytes and
  `Content-Type: audio/wav` (requires valid `GEMINI_API_KEY`).
- Record through the UI: the "Your boring anecdote" panel fills with the
  transcript, the "The interestingified version" panel fills with the absurd
  story, and the playback panel appears with narrated audio in a funny Aussie
  accent.
- The server responds through the Codio public URL (bind to `0.0.0.0`, then curl
  the `https://${CODIO_HOSTNAME}-3000.codio.io/` URL).

## Spec sync

- On merge, update ROADMAP.md Cycle 2 feature 3 to record any approved
  deviations from the original roadmap text.

## Out of scope (must NOT be present)

- No fallback-model retry logic in this milestone.
- No change to the SQLite schema or migration tooling.
- No framework/library beyond `google-genai` added to the frontend.