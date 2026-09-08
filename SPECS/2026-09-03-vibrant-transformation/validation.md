# The Vibrant Transformation — Validation

Date: 2026-09-03
Feature: SPECS/2026-09-03-vibrant-transformation/requirements.md

This step is complete when all of the following pass. The Verifier agent audits
the work against this file before the branch is considered done.

## Automated checks

- `ruff check .` — no lint errors.
- `ruff format --check .` — formatting matches the repo style (line length 100,
  double-quoted strings, space indentation).
- `mypy .` — passes under `strict = true` (per `pyproject.toml`).
- `pytest` — all tests pass, including:
  - `tests/test_services.py`: `rewrite_story` returns the story string
    (Gemini call faked), while `narrate_story` still raises `NotImplementedError`.
  - `tests/test_app.py`: rewrite POST returns `200` `{"story": "..."}`
    and persists the story linked to the transcript; `missing_transcript` still
    returns `400`; `/`, `/api/health`, `/api/transcribe`, and narrate `501` stub
    are unchanged.
  - `tests/test_db.py`: unchanged, still green.
- `npm run lint --prefix frontend` and `npm test --prefix frontend` — the new
  rewrite flow is tested; both stay green.
- `pre-commit run --all-files` — gitleaks, Ruff, mypy, pytest, frontend lint and
  tests all pass. Note: running the app/service requires `GEMINI_API_KEY`; the
  pre-commit quality gate itself must not depend on it.

## TDD evidence

- The test files were committed before (or in the same commit as) the code they
  test, and the git history shows the red→green sequence for each group in
  `plan.md`.

## Manual verification

- `python app.py` boots and serves the page with **no `GEMINI_API_KEY` set** —
  the app must still start; the key is only required when a rewrite request
  actually reaches Gemini.
- `curl -X POST -H "Content-Type: application/json" -d '{"transcript":"I missed the bus."}' \
  http://localhost:3000/api/rewrite` → HTTP `200` with `{"story": "..."}` and
  the story persisted linked to the transcript.
- Record through the UI: the "Your boring anecdote" panel fills with the
  transcript, then the "The interestingified version" panel auto-fills with the
  absurd story.
- The server responds through the Codio public URL (bind to `0.0.0.0`, then curl
  the `https://${CODIO_HOSTNAME}-3000.codio.io/` URL).

## Spec sync

- **Implemented and verified 2026-09-03** — automated checks, pre-commit
  gate, and live verification pass (live Gemini rewrite returned a real story
  that persisted to SQLite linked to the most recent transcript, per the
  documented design decision).
- **Follow-up (2026-09-08):** the frontend rewrite-flow test required by this
  validation file ("the new rewrite flow is tested") was missing. It was added
  (`buildRewriteBody` helper in `frontend/static/app.js` +
  `frontend/tests/rewrite-body.test.js`) as part of resolving the PR review
  findings for feature 3.
- ROADMAP.md Cycle 2 feature 2 updated to record status.

## Out of scope (must NOT be present)

- No changes to `/api/narrate` behaviour — its service stub still raises
  `NotImplementedError`.
- No fallback-model retry logic in this milestone.
- No change to the SQLite schema or migration tooling.
- No framework/library beyond `google-genai` added to the frontend.