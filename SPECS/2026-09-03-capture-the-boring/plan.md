# Capture the Boring — Plan

Date: 2026-09-03
Feature: SPECS/2026-09-03-capture-the-boring/requirements.md

TDD note: in every group, write the failing test first (red), watch it fail, then
write the minimal code to make it pass (green). At the end of each group, run the
focused test file for that group; run the full quality gate in the final group.

## Group 1 — Dependency smoke (`requirements.txt`)

- Add `google-genai` (pinned `< 3.0.0`) to `requirements.txt`.
- `pip install google-genai` and confirm `from google import genai` imports.

## Group 2 — Service (`services.py`) — TDD

- Replace the transcribe stub test in `tests/test_services.py`:
  - `transcribe_audio` calls Gemini and returns the transcript string. To avoid a
    real network call in tests, monkeypatch the module's `genai.Client` (or the
    specific class instantiated) with a fake that returns a canned `response.text`.
  - Keep the `NotImplementedError` tests for `rewrite_story` and `narrate_story`
    (unchanged).
- Run `pytest tests/test_services.py` and watch the new test fail (red) because
  the stub still raises.
- Implement `services.py`:
  - Build a `genai.Client(api_key=config.get_gemini_api_key())` and call
    `client.models.generate_content` with the audio bytes as an `inline_data`
    part (mime_type from the param) plus a transcription prompt, using model
    `gemini-3.5-transcribe`. Return `response.text`.
  - Keep `@logged` on all three functions; leave `rewrite_story` and
    `narrate_story` as stubs.
- Run `pytest tests/test_services.py` until green.

## Group 3 — Route + persistence (`app.py`) — TDD

- Update `tests/test_app.py`:
  - Replace `test_transcribe_stub_returns_501`: a transcribe POST now returns
    `200` with `{"transcript": "..."}` and saves the transcript. To avoid a real
    network call, monkeypatch `services.transcribe_audio` to return a canned
    transcript. Assert the transcript row is persisted in the temp DB
    (`fetch_transcript` / direct query).
  - Keep the `missing_audio` 400 test and the `/` and `/api/health` tests
    unchanged.
  - Keep the `rewrite`/`narrate` 501 stub tests unchanged.
- Run `pytest tests/test_app.py` and watch the new expectations fail (red).
- Implement in `app.py`:
  - In the transcribe handler success path, call
    `db.save_transcript(transcript)` and still return
    `jsonify(asdict(TranscriptResponse(transcript=transcript)))`.
  - Handle Gemini/API failures with a clean structured error, keeping the
    existing success/`NotImplementedError` branches intact.
- Run `pytest tests/test_app.py` until green.

## Group 4 — Frontend (`frontend/static/app.js`) — TDD

- Extend the frontend tests (`frontend/tests/`) for a new pure helper that builds
  the `multipart/form-data` body from a `Blob` (field name `audio`), so the
  upload shape is testable without a browser. (Node's `FormData`/`Blob` are
  available under `node --test`.)
  - The helper returns a `FormData` whose `audio` entry holds the blob.
- Run `npm test --prefix frontend` and watch the new test fail (red).
- Implement in `app.js`:
  - Export the `FormData` builder helper.
  - In `onStop` (or a follow-up), build the body and `await fetch("/api/transcribe", {method: "POST", body})`.
  - On success, set the transcript panel content from `json.transcript`.
- Run `npm test --prefix frontend` and `npm run lint --prefix frontend` until green.

## Group 5 — Quality gate and manual verification

- Run and fix until green:
  - `ruff check .` and `ruff format --check .`
  - `mypy .` (strict)
  - `pytest`
  - `npm run lint --prefix frontend` and `npm test --prefix frontend`
  - `pre-commit run --all-files`
- Start the server (`python app.py`, bound to `0.0.0.0:3000`) and verify through
  the Codio public URL (per AGENTS.md: announce the URL, curl it to confirm):
  - `curl -X POST http://localhost:3000/api/transcribe` (no file) → `400` with
    the `missing_audio` structured error (unchanged).
  - A real end-to-end transcribe with a recorded webm/ogg file and a valid
    `GEMINI_API_KEY` → `200` `{"transcript": "..."}` (requires the key set in the
    environment and an actual audio file).
