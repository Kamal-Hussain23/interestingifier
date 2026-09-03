# The Vibrant Transformation — Plan

Date: 2026-09-03
Feature: SPECS/2026-09-03-vibrant-transformation/requirements.md

TDD note: in every group, write the failing test first (red), watch it fail, then
write the minimal code to make it pass (green). At the end of each group, run the
focused test file for that group; run the full quality gate in the final group.

## Group 1 — Service (`services.py`) — TDD

- Replace the rewrite stub test in `tests/test_services.py`:
  - `rewrite_story` calls Gemini and returns the story string. To avoid a
    real network call in tests, monkeypatch the module's `build_client`
    with a fake that returns a canned `response.text`.
  - Keep the `NotImplementedError` test for `narrate_story` (unchanged).
- Run `pytest tests/test_services.py` and watch the new test fail (red) because
  the stub still raises.
- Implement `services.py`:
  - Build a `genai.Client(api_key=config.get_gemini_api_key())` and call
    `client.models.generate_content` with the transcript text plus an
    over-the-top rewriting prompt, using model `gemini-3.1-flash-lite`.
    Return `response.text`.
  - Keep `@logged` on all three functions; leave `narrate_story` as a stub.
- Run `pytest tests/test_services.py` until green.

## Group 2 — Route + persistence (`app.py`) — TDD

- Update `tests/test_app.py`:
  - Replace `test_rewrite_stub_returns_501`: a rewrite POST now returns
    `200` with `{"story": "..."}` and saves the story linked to the transcript.
    To avoid a real network call, monkeypatch `services.rewrite_story` to
    return a canned story. Assert the story row is persisted in the temp DB
    and linked to the transcript.
  - Keep the `missing_transcript` 400 test and the `/`, `/api/health`,
    `/api/transcribe`, and `narrate` 501 stub tests unchanged.
- Run `pytest tests/test_app.py` and watch the new expectations fail (red).
- Implement in `app.py`:
  - In the rewrite handler success path:
    - Find the most recent transcript (e.g., `SELECT id FROM transcripts ORDER BY id DESC LIMIT 1`) to get its ID.
    - Call `db.save_story(transcript_id, story)`.
    - Still return `jsonify(asdict(StoryResponse(story=story)))`.
  - Handle Gemini/API failures with a clean structured error, keeping the
    existing success/`NotImplementedError` branches intact.
- Run `pytest tests/test_app.py` until green.

## Group 3 — Frontend (`frontend/static/app.js`) — TDD

- Extend the frontend tests (`frontend/tests/`) for a pure helper that builds
  the JSON body for the rewrite request.
- Run `npm test --prefix frontend` and watch the new test fail (red).
- Implement in `app.js`:
  - After `uploadForTranscription` succeeds (and the transcript panel is filled),
    automatically call `/api/rewrite` with `{"transcript": transcript_text}`.
    On success, set the story panel content from `json.story`.
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
  - `curl -X POST -H "Content-Type: application/json" -d '{"transcript":"hi"}'
    http://localhost:3000/api/rewrite` → `200` `{"story": "..."}` (requires
    valid `GEMINI_API_KEY` and a transcript in the DB).
  - End-to-end: record through UI → transcript appears → story appears in
    "Interestingified version" panel.