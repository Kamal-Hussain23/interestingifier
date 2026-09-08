# Vocalizing the Absurd — Plan

Date: 2026-09-03
Feature: SPECS/2026-09-03-vocalizing-the-absurd/requirements.md

TDD note: in every group, write the failing test first (red), watch it fail, then
write the minimal code to make it pass (green). At the end of each group, run the
focused test file for that group; run the full quality gate in the final group.

## Group 1 — Service (`services.py`) — TDD

- Replace the narrate stub test in `tests/test_services.py`:
  - `narrate_story` calls Gemini TTS and returns audio bytes. To avoid a
    real network call in tests, monkeypatch the module's `build_client`
    with a fake that returns a canned response containing base64 audio data.
  - Keep the existing tests for `transcribe_audio` and `rewrite_story` unchanged.
- Run `pytest tests/test_services.py` and watch the new test fail (red) because
  the stub still raises.
- Implement `services.py`:
  - Add `TTS_MODEL = "gemini-3.1-flash-tts-preview"`.
  - Add `TTS_PROMPT` with Aussie accent instruction.
  - `narrate_story(story)` builds a client, calls
    `client.models.generate_content` with:
    - model: `TTS_MODEL`
    - contents: `[TTS_PROMPT, story]`
    - `generation_config` with `response_modalities: ["AUDIO"]` and
      `voice_config` using a prebuilt voice (e.g., "Aoede") with Aussie accent
      guidance in the prompt.
    - Extract the base64 audio from `response.candidates[0].content.parts[0].inline_data.data`,
      decode to bytes, and return.
  - Keep `@logged` on all three functions.
- Run `pytest tests/test_services.py` until green.

## Group 2 — Route (`app.py`) — TDD

- Update `tests/test_app.py`:
  - Replace `test_narrate_stub_returns_501`: a narrate POST now returns
    `200` with audio bytes and correct MIME type. Monkeypatch
    `services.narrate_story` to return canned audio bytes.
  - Keep the `missing_story` 400 test and all other tests unchanged.
- Run `pytest tests/test_app.py` and watch the new expectations fail (red).
- Implement in `app.py`:
  - In the narrate handler success path, call `services.narrate_story(story)`,
    return `Response(audio, mimetype=NARRATION_CONTENT_TYPE)`.
  - Update `NARRATION_CONTENT_TYPE` to `"audio/wav"`.
  - Handle Gemini/API failures with a clean structured error (`502 narration_failed`),
    keeping the existing success/`NotImplementedError` branches intact.
- Run `pytest tests/test_app.py` until green.

## Group 3 — Frontend (`frontend/static/app.js`) — TDD

- Extend the frontend tests (`frontend/tests/`) for a pure helper that builds
  the JSON body for the narrate request, and test the narration flow.
- Run `npm test --prefix frontend` and watch the new test fail (red).
- Implement in `app.js`:
  - After `rewriteStory()` succeeds, automatically call `narrateStory(story)`.
  - `narrateStory(story)` POSTs to `/api/narrate` with `{"story": story}`,
    receives audio blob, creates object URL, sets `previewAudio.src`, shows
    the playback panel.
- Run `npm test --prefix frontend` and `npm run lint --prefix frontend` until green.

## Group 4 — Quality gate and manual verification

- Run and fix until green:
  - `ruff check .` and `ruff format --check .`
  - `mypy .` (strict)
  - `pytest`
  - `npm run lint --prefix frontend` and `npm test --prefix frontend`
  - `pre-commit run --all-files`
- Start the server (`python app.py`, bound to `0.0.0.0:3000`) and verify through
  the Codio public URL (per AGENTS.md: announce the URL, curl it to confirm):
  - `curl -X POST -H "Content-Type: application/json" -d '{"story":"THE BUS FEARED HIM."}' \
    http://localhost:3000/api/narrate` → `200` with audio bytes (requires
    valid `GEMINI_API_KEY`).
  - End-to-end: record through UI → transcript appears → story appears →
    audio plays in playback panel with Aussie accent.