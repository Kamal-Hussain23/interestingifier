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

- **Implemented and verified 2026-09-08** — automated checks, pre-commit gate,
  and live verification pass. See `plan.md` groups 1–4.
- **Approved deviation (Audio format):** The original decision said "The SDK
  returns base64-encoded audio data … MIME type will be `audio/wav`." Live
  testing showed that is wrong for this SDK/model combo:
  - The `google-genai` SDK returns `inline_data.data` as **already-decoded
    bytes**, not a base64 string.
  - The `gemini-3.1-flash-tts-preview` model emits **raw L16 PCM**
    (`audio/l16; rate=24000; channels=1`), which browsers cannot play via
    `<audio>`.
  - Fix: `narrate_story` now returns the PCM bytes as-is and wraps them in a
    standard **WAV container** (`_wrap_l16_in_wav`), so `audio/wav` is now
    accurate and the browser playback works. PR review findings (double
    base64-decode + MIME mismatch) were the prompt for this fix.
- **Test coverage added in the fix:** asserts the real SDK contract (raw bytes,
  not base64), the TTS model/voice config (Aussie accent via `Aoede` +
  `response_modalities`), a `RIFF`-valid narrate route response, the 502
  `narration_failed` path, and the frontend narrate body helper.
- Rolled up in the follow-up that resolved the PR #2 review. ROADMAP.md Cycle 2
  feature 3 updated accordingly.

## Out of scope (must NOT be present)

- No fallback-model retry logic in this milestone.
- No change to the SQLite schema or migration tooling.
- No framework/library beyond `google-genai` added to the frontend.