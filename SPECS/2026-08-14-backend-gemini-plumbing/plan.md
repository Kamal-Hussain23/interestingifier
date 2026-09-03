# Backend + Gemini Plumbing — Plan

Date: 2026-08-14
Feature: SPECS/2026-08-14-backend-gemini-plumbing/requirements.md

TDD note: in every group, write the failing test first (red), watch it fail, then
write the minimal code to make it pass (green). At the end of each group, run the
focused pytest file for that group; run the full quality gate in group 5.

## Group 1 — API-key helper (`config.py`) — TDD

- Write tests first (`tests/test_config.py`):
  - `get_gemini_api_key()` returns the environment value when `GEMINI_API_KEY`
    is set (use `monkeypatch.setenv`).
  - `get_gemini_api_key()` raises a `RuntimeError` with a clear message when
    `GEMINI_API_KEY` is unset (use `monkeypatch.delenv`).
  - A blank value (`monkeypatch.setenv("GEMINI_API_KEY", "  ")`) is treated as
    missing and raises.
- Run `pytest tests/test_config.py` and watch it fail (red).
- Implement `config.py`:
  - `GEMINI_API_KEY_ENV = "GEMINI_API_KEY"`.
  - `get_gemini_api_key() -> str` reads `os.environ`, strips whitespace, and
    raises `RuntimeError("Missing environment variable GEMINI_API_KEY ...")`
    when missing or blank.
- Run `pytest tests/test_config.py` until green.

## Group 2 — Contract models (`models.py`) — TDD

- Write tests first (`tests/test_models.py`):
  - `asdict(TranscriptResponse(transcript="..."))` equals
    `{"transcript": "..."}`.
  - `asdict(StoryResponse(story="..."))` equals `{"story": "..."}`.
  - `asdict(ErrorResponse(code="...", message="..."))` equals
    `{"code": "...", "message": "..."}`.
- Run `pytest tests/test_models.py` and watch it fail (red).
- Implement `models.py`: three frozen dataclasses as in the requirements
  (`TranscriptResponse`, `StoryResponse`, `ErrorResponse`).
- Run `pytest tests/test_models.py` until green.

## Group 3 — Gemini service stubs (`services.py`) — TDD

- Write tests first (`tests/test_services.py`):
  - `transcribe_audio(b"fake-audio", "audio/webm")` raises `NotImplementedError`.
  - `rewrite_story("boring anecdote")` raises `NotImplementedError`.
  - `narrate_story("absurd story")` raises `NotImplementedError`.
  - (Optionally) a `caplog` check that a stub call emits log output, proving
    the `@logged` decorator is applied.
- Run `pytest tests/test_services.py` and watch it fail (red).
- Implement `services.py`:
  - Import `logged` from `logging_config`.
  - Three functions with the exact signatures from the requirements, each
    decorated with `@logged` and each raising `NotImplementedError` with a clear
    message naming the Cycle 2 milestone that implements it (e.g. "fill in the
    Gemini Speech-to-Text call here — Cycle 2, milestone 1"). The `narrate_story`
    message must also require an explicit funny Aussie accent in the TTS config.
- Run `pytest tests/test_services.py` until green.

## Group 4 — Endpoints (`app.py`) — TDD

- Write tests first (extend `tests/test_app.py`):
  - `GET /api/health` still returns `200` `{"status": "ok"}` (unchanged).
  - `POST /api/transcribe` with no `audio` file part → `400`, body
    `{"error": {"code": "missing_audio", ...}}`.
  - `POST /api/transcribe` with a file part
    (`client.post("/api/transcribe", data={"audio": (BytesIO(b"fake"), "story.webm")},
    content_type="multipart/form-data")`) → `501`, code `not_implemented`.
  - `POST /api/rewrite` with no JSON body / no `transcript` → `400`, code
    `missing_transcript`.
  - `POST /api/rewrite` with a blank transcript → `400`.
  - `POST /api/rewrite` with a non-blank transcript → `501`, code
    `not_implemented`.
  - `POST /api/narrate` with no `story` → `400`, code `missing_story`.
  - `POST /api/narrate` with a blank story → `400`.
  - `POST /api/narrate` with a non-blank story → `501`, code `not_implemented`.
- Run `pytest tests/test_app.py` and watch the new tests fail (red).
- Implement the three routes in `create_app`, mirroring the existing route
  style (`@app.route(...)` then `@logged`):
  - Extract and validate input, returning `400` `ErrorResponse` JSON on bad
    input.
  - Call the matching `services` function inside a `try`/`except
    NotImplementedError` that maps to `501` `ErrorResponse` with code
    `not_implemented`.
  - Keep the success paths (`jsonify(asdict(...))` / audio `Response`) wired
    even though they are unreachable until Cycle 2 fills in the stubs.
  - Add the `NARRATION_CONTENT_TYPE` constant (`"audio/webm"`), documented as a
    placeholder to confirm when the Gemini Text-to-Speech call lands.
  - Do not touch the `/` or `/api/health` routes.
- Run `pytest tests/test_app.py` until green.

## Group 5 — Quality gate and manual verification

- Run and fix until green:
  - `ruff check .` and `ruff format --check .`
  - `mypy .` (strict)
  - `pytest`
  - `npm run lint --prefix frontend` and `npm test --prefix frontend`
    (frontend untouched, must stay green)
  - `pre-commit run --all-files`
- Start the server (`python app.py`, bound to `0.0.0.0:3000`) and verify through
  the Codio public URL (per AGENTS.md: announce the URL, curl it to confirm):
  - `curl -X POST http://localhost:3000/api/transcribe` (no file) → `400` with
    the structured error body.
  - `curl -X POST -F "audio=@/tmp/sample.webm" http://localhost:3000/api/transcribe`
    → `501` with the structured error body. (A tiny dummy file is fine; it never
    reaches Gemini.)
  - `curl -X POST -H "Content-Type: application/json" -d '{"transcript":"hi"}'
    http://localhost:3000/api/rewrite` → `501`.
  - `curl -X POST -H "Content-Type: application/json" -d '{"story":"hi"}'
    http://localhost:3000/api/narrate` → `501`.
  - The app boots and serves `/` with no `GEMINI_API_KEY` set.