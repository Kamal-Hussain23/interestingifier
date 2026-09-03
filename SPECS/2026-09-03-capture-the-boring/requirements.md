# Capture the Boring — Requirements

Date: 2026-09-03
Source: ROADMAP.md, Cycle 2, feature 1 ("Capture the Boring")

## Feature summary

Wire the browser's already-working `MediaRecorder` record button all the way to a
spoken transcript. When a recording is stopped and held as a `Blob`, the frontend
packages it as `multipart/form-data`, POSTs it to the existing
`POST /api/transcribe` endpoint, and the backend forwards the audio to Gemini
Speech-to-Text. The returned transcript is saved to SQLite and shown
automatically in the "Your boring anecdote" panel.

This is the first of three Cycle 2 features. It should be genuinely simple and
General, per TECH.md: transcribe, persist, surface the text. Nothing else.

## Scope — in

- **Frontend (`frontend/static/app.js`)**: When recording stops (the existing
  `onStop` seam), build a `multipart/form-data` body containing the audio `Blob`
  in field `audio`, and `POST` it to `/api/transcribe`. On success, place the
  returned `transcript` text into the "Your boring anecdote" transcript panel
  (replacing the empty-state placeholder).
- **Backend (`services.py`)**: Implement `transcribe_audio(audio: bytes,
  mime_type: str) -> str` for real. Call Gemini Speech-to-Text via the
  `google-genai` SDK with model `gemini-3.5-transcribe`, and return the
  transcript text. Read the API key through the existing
  `config.get_gemini_api_key()` seam. Keep the `@logged` decorator; no business
  logic logging.
- **Backend (`app.py`)**: Update the `POST /api/transcribe` handler so that, on
  success, it saves the transcript to SQLite with `db.save_transcript` and
  returns `200` with the `TranscriptResponse` JSON (`{"transcript": "..."}`).
  The existing 400 `missing_audio` validation stays as-is.
- **Dependency (`requirements.txt`)**: add `google-genai` (pinned, `< 3.0.0`
  per the SDK's guidance).
- **Tests**: written first (Red/Green TDD) for the service, the route, and the
  persistence integration.

## Scope — out (later milestones / later specs)

- No story rewriting or narration — those are Cycle 2 features 2 and 3. The
  `/api/rewrite` and `/api/narrate` endpoints and their `services` stubs are
  unchanged (still `NotImplementedError` → `501`).
- No fallback model retry. If Gemini fails, return a clean structured error. The
  `gemini-2.5-flash` fallback noted in ROADMAP is intentionally deferred.
- No Absurdity Slider, Visual Engine, Clickbait Title, or "More Drama!" stretch
  features.
- No change to the existing `/`, `/api/health`, `/api/rewrite`, or `/api/narrate`
  routes (the transcribe success path is the only behavioural change).
- No change to the SQLite schema — `db.save_transcript` already exists.

## Decisions

- **Model: `gemini-3.5-transcribe`.** ROADMAP originally named
  `gemini-3.1-flash-lite` for transcription, but that is its generative-text
  model; the current dedicated Speech-to-Text model is `gemini-3.5-transcribe`.
  (User-confirmed deviation — see the roadmap update in validation.md.)
- **Persist the transcript in this milestone.** Though ROADMAP listed
  "persist both transcript and story" under feature 2, the user confirmed saving
  the transcript now, so feature 2 only saves the story. (User-confirmed.)
- **`google-genai` SDK.** The official, beginner-friendly SDK. It needs a
  `GEMINI_API_KEY` at request time; the app still boots without a key set.
  (User-confirmed.)
- **No auto-fallback.** Keep milestone 1 simple: on any Gemini failure (bad key,
  model error, empty response) the route returns a clear structured error; the
  fallback retry is a later concern. (User-confirmed.)
- **Endpoint + response contract unchanged.** The transcribe endpoint keeps its
  exact `multipart/form-data` `audio` upload and `TranscriptResponse` JSON shape,
  so the existing frontend/test contracts hold; only the success path now
  actually transcribes and saves.
- **Reuse existing seams.** `@logged`, `config.get_gemini_api_key()`,
  `db.save_transcript`, and the `TranscriptResponse` model are all reused as-is.
  No new logging, config, or schema machinery.

## Context

`app.py` already has three structured endpoints; the transcribe one validates the
`audio` upload and returns `501` because `services.transcribe_audio` raises
`NotImplementedError`. The frontend (`app.js`) already records with `MediaRecorder`
and holds the resulting `Blob` "ready to POST". `db.save_transcript` already
persists a transcript and returns a typed `Transcript`. This feature joins those
dots: upload → transcribe → save → show. When it lands, the user records a story
and immediately sees it as text in the transcript panel.

## Status

Planned 2026-09-03 pending implementation. See `validation.md` for the
spec-sync record once merged.