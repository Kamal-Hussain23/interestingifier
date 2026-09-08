# The Vibrant Transformation — Requirements

Date: 2026-09-03
Source: ROADMAP.md, Cycle 2, feature 2 ("The Vibrant Transformation")

## Feature summary

Take the transcript saved by feature 1 ("Capture the Boring") and rewrite it as
an over-the-top, hilarious story using Gemini generative text. Persist the story
to SQLite linked to its transcript. The frontend automatically calls the
rewrite endpoint after transcription and displays the absurd story in the
"Interestingified version" panel.

This is the second of three Cycle 2 features. It should be simple and general:
rewrite, persist, surface the story. Nothing else.

## Scope — in

- **Frontend (`frontend/static/app.js`)**: After a successful transcription
  (the existing `uploadForTranscription` flow), POST the transcript to
  `/api/rewrite` with JSON body `{"transcript": "..."}`. On success, place the
  returned `story` text into the "The interestingified version" story panel
  (replacing the empty-state placeholder).
- **Backend (`services.py`)**: Implement `rewrite_story(transcript: str) -> str`
  for real. Call Gemini generative text via the `google-genai` SDK with model
  `gemini-3.1-flash-lite`, using an over-the-top prompt that produces an
  absurd, theatrical retelling. Return the story text. Read the API key through
  the existing `config.get_gemini_api_key()` seam. Keep the `@logged` decorator.
- **Backend (`app.py`)**: Update the `POST /api/rewrite` handler so that, on
  success, it saves the story to SQLite with `db.save_story` (linking it to
  the transcript — but since feature 1 already saved the transcript, we need
  to fetch its ID first) and returns `200` with the `StoryResponse` JSON
  (`{"story": "..."}`). The existing 400 `missing_transcript` validation
  stays as-is.
- **Tests**: written first (Red/Green TDD) for the service, the route, and the
  persistence integration.

## Scope — out (later milestones / later specs)

- No narration — that's Cycle 2 feature 3. The `/api/narrate` endpoint and
  its `services.narrate_story` stub are unchanged (still `NotImplementedError`
  → `501`).
- No fallback model retry. If Gemini fails, return a clean structured error.
  The `gemini-2.5-flash` fallback noted in ROADMAP is intentionally deferred.
- No Absurdity Slider, Visual Engine, Clickbait Title, or "More Drama!" stretch
  features.
- No change to the existing `/`, `/api/health`, `/api/transcribe`, or
  `/api/narrate` routes (the rewrite success path is the only behavioural
  change).
- No change to the SQLite schema — `db.save_story` already exists and expects
  a `transcript_id` foreign key.

## Decisions

- **Model: `gemini-3.1-flash-lite`.** ROADMAP names this for story rewriting.
  (Follows the roadmap as written.)
- **Link story to transcript.** Feature 1 saved the transcript and returned
  it, but not its DB ID. The rewrite endpoint needs to find the transcript ID
  to save the story with the FK. Approach: in the rewrite handler, fetch the
  most recent transcript (or require the client to send the transcript ID).
  Since this is a student learning project, the simplest approach: fetch the
  most recent transcript by `created_at` DESC and link the story to it.
- **`google-genai` SDK.** Already added in feature 1. Reuse the existing
  `build_client` seam.
- **No auto-fallback.** Keep milestone 2 simple: on any Gemini failure, the
  route returns a clear structured error; fallback retry is a later concern.
- **Endpoint + response contract unchanged.** The rewrite endpoint keeps its
  exact JSON `{"transcript": "..."}` request and `StoryResponse` JSON shape.
- **Reuse existing seams.** `@logged`, `config.get_gemini_api_key()`,
  `db.save_story`, and the `StoryResponse` model are all reused as-is.

## Context

`app.py` already has a structured `/api/rewrite` endpoint that validates the
`transcript` input and returns `501` because `services.rewrite_story` raises
`NotImplementedError`. The frontend (`app.js`) already records, uploads for
transcription, and shows the transcript. This feature joins those dots:
transcript → rewrite → save → show. When it lands, the user records a story,
sees the transcript, and moments later sees the absurd retelling in the story
panel.

## Status

Implemented and verified 2026-09-03; frontend rewrite-flow test added 2026-09-08
as a follow-up. See `validation.md` for the spec-sync record.