# Vocalizing the Absurd — Requirements

Date: 2026-09-03
Source: ROADMAP.md, Cycle 2, feature 3 ("Vocalizing the Absurd")

## Feature summary

Take the rewritten story (from feature 2) and narrate it aloud using Gemini
Text-to-Speech. The TTS config must **explicitly request a funny, energetic
Aussie accent** (MISSION.md's signature voice) — not a plain, accent-free
read-out. Play the resulting audio in the browser through the existing
playback panel.

This is the third and final Cycle 2 feature. When complete, the full
end-to-end pipeline works: record → transcribe → rewrite → persist → narrate → play.

## Scope — in

- **Backend (`services.py`)**: Implement `narrate_story(story: str) -> bytes`
  for real. Call Gemini TTS via the `google-genai` SDK with model
  `gemini-3.1-flash-tts-preview`. The TTS config must explicitly request a
  funny, energetic Aussie accent (via voice config and/or prompt). Return the
  audio bytes. Read the API key through the existing
  `config.get_gemini_api_key()` seam. Keep the `@logged` decorator.
- **Backend (`app.py`)**: Update the `POST /api/narrate` handler so that, on
  success, it returns `200` with the audio bytes and the correct MIME type.
  The existing 400 `missing_story` validation stays as-is.
- **Frontend (`frontend/static/app.js`)**: After a successful rewrite
  (the existing `rewriteStory` flow), POST the story to `/api/narrate` with
  JSON body `{"story": "..."}`. On success, play the returned audio in the
  existing `<audio id="preview-audio">` element and show the playback panel.
- **Tests**: written first (Red/Green TDD) for the service, the route, and the
  frontend integration.

## Scope — out (later milestones / later specs)

- No fallback model retry. If Gemini fails, return a clean structured error.
  The `gemini-2.5-flash-preview-tts` fallback noted in ROADMAP is intentionally
  deferred.
- No Absurdity Slider, Visual Engine, Clickbait Title, or "More Drama!" stretch
  features.
- No change to the existing `/`, `/api/health`, `/api/transcribe`, or
  `/api/rewrite` routes.
- No new database schema or persistence changes.

## Decisions

- **Model: `gemini-3.1-flash-tts-preview`.** ROADMAP names this for TTS.
- **Aussie accent:** Explicitly requested via TTS generation config. The
  `google-genai` SDK supports `generation_config` with `response_modalities:
  ["AUDIO"]` and `voice_config` for prebuilt voices. We'll use a clear
  Australian voice (e.g., "Aoede" with accent instructions) plus prompt
  guidance.
- **Audio format:** Live verification with the installed SDK showed the
  `google-genai` SDK returns `inline_data.data` as **already-decoded bytes**
  and the TTS model emits raw L16 PCM (`audio/l16; rate=24000; channels=1`),
  not base64 and not a WAV. So `narrate_story` wraps the PCM in a standard WAV
  container before returning it. MIME type is `audio/wav`. (Approved deviation
  from the earlier base64/WAV assumption — see validation.md.)
- **`google-genai` SDK.** Already added in feature 1. Reuse the existing
  `build_client` seam.
- **No auto-fallback.** Keep milestone simple: on any Gemini failure, the
  route returns a clear structured error; fallback retry is a later concern.
- **Endpoint contract unchanged.** The narrate endpoint keeps its exact JSON
  `{"story": "..."}` request and audio response shape.
- **Reuse existing seams.** `@logged`, `config.get_gemini_api_key()`,
  and the `NARRATION_CONTENT_TYPE` constant are reused as-is.
- **Playback:** Use the existing `<audio id="preview-audio" controls>` element
  — no new UI elements needed.

## Context

`app.py` already has a structured `/api/narrate` endpoint that validates the
`story` input and returns `501` because `services.narrate_story` raises
`NotImplementedError`. The frontend (`app.js`) already records, transcribes,
and rewrites, showing the transcript and story. This feature joins the final
dots: story → narrate → play. When it lands, the user records a story, sees
the transcript, sees the absurd retelling, and hears it narrated in a funny
Aussie accent.

## Status

Implemented and verified 2026-09-08. See `validation.md` for the spec-sync
record, including the approved audio-format deviation.