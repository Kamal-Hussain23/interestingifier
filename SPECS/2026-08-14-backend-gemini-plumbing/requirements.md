# Backend + Gemini Plumbing — Requirements

Date: 2026-08-14
Source: ROADMAP.md, Cycle 1, Step 3 (Backend + Gemini plumbing, stubbed but structured)

## Feature summary

Add the backend endpoints the app will call, with real, structured
request/response shapes and clear TODO stubs where the AI calls belong. Create
small, clean service helpers for the three Gemini interactions (transcribe,
rewrite, narrate) and a safe way to read the API key from an environment
variable. Reuse the existing `@logged` decorator from `logging_config.py` so
business logic stays clean and logging stays out of it.

This step is backend-only. The app boots and the frontend shell is untouched.
Each of the three endpoints is the structured contract that Cycle 2's three
features fill in: the Gemini call plus persistence.

## Scope — in

- **`config.py`** — a new module with a safe, lazy API-key reader:
  - `GEMINI_API_KEY_ENV = "GEMINI_API_KEY"` (the environment-variable name).
  - `get_gemini_api_key() -> str` reads the key from the environment and raises a
    clear, friendly `RuntimeError` if it is missing or blank. The app must boot
    fine without a key set; the error only surfaces when a Gemini service is
    actually used.
- **`models.py`** — a new module with small, frozen dataclasses as the JSON
  contracts (per TECH.md's "contracts and strict models over custom logic"):
  - `TranscriptResponse(transcript: str)` — success body of `/api/transcribe`.
  - `StoryResponse(story: str)` — success body of `/api/rewrite`.
  - `ErrorResponse(code: str, message: str)` — the shared error body.
- **`services.py`** — a new module with three small, typed service helpers, each
  decorated with `@logged`:
  - `transcribe_audio(audio: bytes, mime_type: str) -> str`
  - `rewrite_story(transcript: str) -> str`
  - `narrate_story(story: str) -> bytes` — its `NotImplementedError` message must
    also remind the Cycle 2 implementer to explicitly request a funny, energetic
    Aussie accent in the TTS config (MISSION.md's signature voice), not a plain
    read-out.
  - Each raises `NotImplementedError` with a clear message naming the Cycle 2
    milestone that will fill in the Gemini call. No Gemini SDK or HTTP calls yet.
- **`app.py`** — add three POST routes to the existing Flask app (leaving `/`
  and `/api/health` untouched):
  - `POST /api/transcribe` — accepts a `multipart/form-data` upload in the
    `audio` field. Validates that a non-empty audio file is present, calls
    `transcribe_audio`, and on success returns `200` with the
    `TranscriptResponse` JSON (`{"transcript": "..."}`).
  - `POST /api/rewrite` — accepts JSON `{"transcript": "..."}`. Validates that
    the transcript is present and non-blank, calls `rewrite_story`, and on
    success returns `200` with the `StoryResponse` JSON (`{"story": "..."}`).
  - `POST /api/narrate` — accepts JSON `{"story": "..."}`. Validates that the
    story is present and non-blank, calls `narrate_story`, and on success
    returns `200` with the narrated audio bytes. A `NARRATION_CONTENT_TYPE`
    placeholder (`"audio/webm"`) is documented as subject to change when the
    Gemini Text-to-Speech call lands in Cycle 2.
  - All three routes are decorated with `@logged`, matching the existing route
    style.
- **Structured error behaviour.** Every failure returns JSON in the shared
  `ErrorResponse` shape: `{"error": {"code": "...", "message": "..."}}`.
  - `400 Bad Request` for missing/invalid input (codes such as `missing_audio`,
    `missing_transcript`, `missing_story`).
  - `501 Not Implemented` when a service helper raises `NotImplementedError`
    (code `not_implemented`, message from the stub). This is what the endpoints
    return until Cycle 2 fills in the Gemini calls.
- **Tests written first (Red/Green TDD)** covering `config.py`, `models.py`,
  `services.py`, and the three new routes.

## Scope — out (later steps / later specs)

- No real Gemini API calls, no Gemini SDK, no HTTP calls to Google.
- No persistence writes — nothing is saved to SQLite in this step (ROADMAP
  Step 4 owns that).
- No frontend changes: `frontend/` is untouched (the upload + pipeline wiring is
  Cycle 2, milestones 1–3).
- No changes to the existing `/` or `/api/health` routes.
- No new logging machinery — the existing `@logged` decorator is reused as-is.

## Decisions

- **Three separate endpoints, one per Cycle 2 feature.** Each Cycle 2 milestone
  maps 1:1 to an endpoint (`transcribe` → "Capture the Boring", `rewrite` →
  "The Vibrant Transformation", `narrate` → "Vocalizing the Absurd"), so each
  student feature stays individually spec-able and independently buildable.
  (User-confirmed.)
- **Stubs return HTTP 501 with the structured error body.** Honest and
  unambiguous: until a Gemini call exists, the endpoint says "not implemented"
  rather than pretending to work. (User-confirmed.)
- **Lazy API-key read; the app boots without a key.** `get_gemini_api_key()`
  only raises when a service is invoked, so students can run the UI and see the
  kitsch without configuring a key. (User-confirmed.)
- **Reuse `@logged` only.** No new logging infrastructure; the existing
  decorator is applied to the new services and routes. (User-confirmed.)
- **Frontend untouched this step.** Backend-only, matching the roadmap.
  (User-confirmed.)
- **One shared error contract.** `ErrorResponse` with `code` + `message` is
  reused by every failure path instead of bespoke error bodies per route —
  simple, consistent, general.
- **Contracts as dataclasses.** The three JSON shapes are frozen dataclasses in
  `models.py` (serialised with `dataclasses.asdict`), satisfying TECH.md's
  preference for explicit models over ad-hoc dicts, while staying plain stdlib
  and beginner-readable.
- **`audio` upload field name.** The transcribe route reads `request.files` key
  `"audio"`; Cycle 2's upload milestone will POST to this exact contract.
- **`GEMINI_API_KEY` environment variable.** The conventional, obvious name;
  read only via `get_gemini_api_key()` so there is a single seam.
- **Backward compatibility.** Purely additive: no existing file's contract
  changes. New modules are added; `app.py` only gains three routes; `/` and
  `/api/health` keep their exact behaviour. No removal, no renaming, so no
  compatibility decision is required.

## Context

Step 3 is the seam that makes Cycle 2 "just fill in the Gemini call + save the
result". By locking the request/response shapes, the error contract, the service
signatures, and the API-key seam now, students inherit a structured scaffold they
only need to extend — exactly the brownfield story from MISSION.md and TECH.md.
Persistence (Step 4) and the end-to-end shell run (Step 5) build directly on the
endpoints defined here.

## Status

Implemented and verified 2026-08-14 on branch
`feature/2026-08-14-backend-gemini-plumbing`; all automated checks and the manual
curl verification pass. See `validation.md` for the spec-sync record.