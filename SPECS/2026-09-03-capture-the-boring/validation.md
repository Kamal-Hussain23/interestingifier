# Capture the Boring — Validation

Date: 2026-09-03
Feature: SPECS/2026-09-03-capture-the-boring/requirements.md

This step is complete when all of the following pass. The Verifier agent audits
the work against this file before the branch is considered done.

## Automated checks

- `ruff check .` — no lint errors.
- `ruff format --check .` — formatting matches the repo style (line length 100,
  double-quoted strings, space indentation).
- `mypy .` — passes under `strict = true` (per `pyproject.toml`).
- `pytest` — all tests pass, including:
  - `tests/test_services.py`: `transcribe_audio` returns the transcript string
    (Gemini call faked), while `rewrite_story` and `narrate_story` still raise
    `NotImplementedError`.
  - `tests/test_app.py`: transcribe POST returns `200` `{"transcript": "..."}`
    and persists the transcript; `missing_audio` still returns `400`; `/`,
    `/api/health`, and the rewrite/narrate `501` stubs are unchanged.
  - `tests/test_db.py`: unchanged, still green.
- `npm run lint --prefix frontend` and `npm test --prefix frontend` — the new
  `FormData` builder is tested; both stay green.
- `pre-commit run --all-files` — gitleaks, Ruff, mypy, pytest, frontend lint and
  tests all pass. Note: running the app/service requires `GEMINI_API_KEY`; the
  pre-commit quality gate itself must not depend on it.

## TDD evidence

- The test files were committed before (or in the same commit as) the code they
  test, and the git history shows the red→green sequence for each group in
  `plan.md`.

## Manual verification

- `python app.py` boots and serves the page with **no `GEMINI_API_KEY` set** —
  the app must still start; the key is only required when a transcribe request
  actually reaches Gemini.
- `curl -X POST http://localhost:3000/api/transcribe` (no file) → HTTP `400`
  with body `{"error": {"code": "missing_audio", ...}}` (unchanged).
- With `GEMINI_API_KEY` set and a real recorded audio file:
  `curl -X POST -F "audio=@recording.webm" http://localhost:3000/api/transcribe`
  → HTTP `200` with `{"transcript": "..."}` and the transcript persisted.
- Record through the UI: the "Your boring anecdote" panel auto-fills with the
  transcript after recording stops.
- The server responds through the Codio public URL (bind to `0.0.0.0`, then curl
  the `https://${CODIO_HOSTNAME}-3000.codio.io/` URL).

## Spec sync

- On merge, update ROADMAP.md Cycle 2 feature 1 to record these approved
  deviations from the original roadmap text:
  - **Model:** `gemini-3.5-transcribe` instead of `gemini-3.1-flash-lite`
    (the flash-lite name is that family's generative-text model; the dedicated
    Speech-to-Text model is `gemini-3.5-transcribe`).
  - **Persistence:** the transcript is saved in feature 1 (not deferred to
    feature 2); feature 2 then saves only the story.
  - **NGWeb search reflect reality (Sep 2026):** the dedicated STT model and the
    google-genai SDK (`< 3.0.0`) are the documented current way.

## Out of scope (must NOT be present)

- No changes to `/api/rewrite` or `/api/narrate` behaviour — their service stubs
  still raise `NotImplementedError`.
- No fallback-model retry logic in this milestone.
- No story persistence or history rendering changes.
- No change to the SQLite schema or migration tooling.
- No framework/library beyond `google-genai` added to the frontend.