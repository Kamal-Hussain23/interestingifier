# ROADMAP.md

The work is split into two cycles:

- **Cycle 1 (ours):** building the near-production-ready scaffold that the students will inherit.
- **Cycle 2 (students):** the small set of missing features students add on top of that scaffold.

When the students finish Cycle 2, Interestingifier™ is a complete, production-ready app.

---

## Cycle 1 — Build the Inherited Scaffold (the brownfield codebase)

Our goal is a polished, fun, production-ready web app that *feels* finished but is missing a few deliberate core features. Students should open it and think "wow, this almost works" — then add what's missing with Spec-Driven Development.

### Step 1: Project foundation
- Create the repo layout: backend (`app.py`, `db.py`), frontend (`static/` with `index.html`, `style.css`, `app.js`), and `requirements.txt`.
- Define the empty-SQLite schema in `db.py` (tables for transcripts, stories, and metadata) and a DB init on startup.
- Set up a minimal Flask/FastAPI skeleton with a `/` route serving the frontend and a few stub API endpoints.

**Status: ✅ Done (2026-08-14) — spec: `SPECS/2026-08-14-project-foundation`**

### Step 2: The kitsch-styled frontend shell
- Build a complete, polished `index.html` with the eccentric-kitsch UI: a big record button, an input/output area, a place to play back audio, and a history of past Interestingifications.
- Style it fully with `style.css` — leopard print, neon gradients, rhinestone/glow borders, clashing colors, playful fonts. It must look loud, joyful, and *finished*, never bare-bones.
- Wire up `app.js` with the recording plumbing: a working record/stop toggle using `MediaRecorder` that captures audio and is ready to POST it. The record button works end-to-end at the UI level.

**Status: ✅ Done (2026-08-14) — spec: `SPECS/2026-08-14-kitsch-frontend-shell`.** The record button captures audio with `MediaRecorder`, previews the clip, and holds it ready to POST; frontend lint/test tooling is real (ESLint + `node:test`), and `setup.sh` installs Node 20 (the Codio box's default Node 12 is too old — see `SPECS/TECH.md`).

### Step 3: Backend + Gemini plumbing (stubbed but structured)
- Add the backend endpoints the app will call, with real, structured request/response shapes and clear TODO stubs where the AI calls belong.
- Create small, clean service helpers for the three Gemini interactions (transcribe, rewrite, narrate) and a safe way to read the API key from an environment variable.
- Add helper utilities for structured logging (decorator-based) so business logic stays clean.

**Status: ✅ Done (2026-08-14) — spec: `SPECS/2026-08-14-backend-gemini-plumbing`.** Three POST endpoints (`/api/transcribe`, `/api/rewrite`, `/api/narrate`) with structured 400/501 error contracts, `@logged` service stubs in `services.py`, a lazy `GEMINI_API_KEY` reader in `config.py`, and frozen-dataclass JSON contracts in `models.py`. The `narrate_story` stub reminds Cycle 2 to explicitly request a funny Aussie accent in the TTS config.

### Step 4: Persistence is real
- Make SQLite persistence actually work for the scaffolding: the DB initializes, functions to save and fetch transcripts/stories exist and are tested.

**Status: ✅ Done (2026-08-14) — spec: `SPECS/2026-08-14-persistence-is-real`.** `db.py` saves and fetches transcripts and stories (`save_transcript`, `fetch_transcript`, `save_story`, `fetch_story`, `list_stories`) returning typed `Transcript`/`Story` dataclasses; `get_connection` reads rows by name (`sqlite3.Row`) and enforces foreign keys. The storage layer is tested and ready for Cycle 2; the pipeline endpoints still return 501 until students fill in the Gemini calls.

### Step 5: End-to-end shell runs
- The app starts, serves the polished frontend, records audio, and the pipeline is structured so that each missing feature is just "fill in the Gemini call + save the result."

**Status: ✅ Done (2026-08-14).** The app boots and serves the full kitsch frontend — `/` (HTML), `/static/style.css`, `/static/app.js`, and `/api/health` all respond. The `MediaRecorder` record button works end-to-end at the UI level, and the pipeline endpoints have structured 400/501 contracts so each Cycle 2 feature is a clean "fill in the Gemini call + save the result."

### Step 6: Quality & finish
- Write tests for `db.py` functions and a light smoke test that the app boots and serves the page.
- Make sure Ruff, mypy, pytest, and the pre-commit hooks all pass.
- Verify the site runs in Codio and is reachable through the public URL.

**Status: ✅ Done (2026-08-14).** `db.py` tests and the boot/serves smoke test pass (`pytest`, 40 passed); frontend lint and tests pass (ESLint + `node:test`, 5 passed); Ruff lint/format, mypy (`--strict`), and all pre-commit hooks are clean; and the site is verified live in Codio through the public URL.

**Definition of done for Cycle 1:** students open the repo, run it, see a beautiful, playful, fully-styled app with a working record button — and three clearly-missing, individually spec-able features to build.

---

## Cycle 2 — The Core Features (what students build)

Students build these in order, each with its own dated spec folder under `SPECS/` and its own PR, using the `spec-implementer`, `verifier`, and `pr-reviewer` agents.

### External services & models

All three features call the [Gemini API](https://ai.google.dev/gemini-api/docs/models) through the backend services stubs in `services.py`:

| Feature | Model |
| --- | --- |
| Transcription (Speech-to-Text) | `gemini-3.1-flash-lite` |
| Story rewriting (generative text) | `gemini-3.1-flash-lite` |
| Narration (Text-to-Speech) | `gemini-3.1-flash-tts-preview` |

Fallbacks if a primary model is unavailable or errors: `gemini-2.5-flash` (transcription and story rewriting) / `gemini-2.5-flash-preview-tts` (TTS). Prefer the primary model and only fall back when it fails.

1. **Capture the Boring** — Record audio in the browser (`MediaRecorder`), POST it to the backend (the record button already works; add the actual upload + transcribe step), and transcribe it with Gemini Speech-to-Text (`gemini-3.5-transcribe` — the dedicated STT model, replacing the earlier `gemini-3.1-flash-lite` name). The transcript is saved to SQLite and shown in the transcript panel. Result: a raw text transcript of the user's anecdote, persisted. Spec: `SPECS/2026-09-03-capture-the-boring`.
2. **The Vibrant Transformation** — Take the transcript and rewrite it as an over-the-top story via Gemini generative text (`gemini-3.1-flash-lite`), then persist the story to SQLite (the transcript is already saved in feature 1). **Status: ✅ Done — spec: `SPECS/2026-09-03-vibrant-transformation`.**
3. **Vocalizing the Absurd** — Use Gemini Text-to-Speech (`gemini-3.1-flash-tts-preview`) to narrate the rewritten story aloud, and play the resulting audio in the browser. The TTS config must **explicitly request a funny, energetic Aussie accent** (the signature voice from MISSION.md) — via the voice/prompt parameters — not a plain, accent-free read-out. **Status: ✅ Done — spec: `SPECS/2026-09-03-vocalizing-the-absurd`.** (Approved deviation: the SDK returns decoded bytes and the model emits raw L16 PCM, so the service wraps it in a WAV container — see the spec's validation.md for the audio-format record.)

When all three are done, the full end-to-end pipeline works: record → transcribe → rewrite → persist → narrate → play.

## Fast-finisher stretch features (optional, Cycle 2)

If the core pipeline is complete and verified, students may add extra kitsch for fun:

- An **Absurdity Slider** (`Slightly Weird`, `Unhinged`, `Total Fever Dream`) that changes the story prompt. **Status: ✅ Done (2026-09-08) — spec: `SPECS/2026-09-08-absurdity-slider`.**
- A **Visual Engine** that fires confetti and rainbow borders whenever a story generates. **Spec: `SPECS/2026-09-08-visual-engine`.**
- A **Clickbait Title Generator** that saves a sensationalist headline with each story.
- A **"More Drama!"** re-roll button that creates an alternate spin on the same anecdote without re-recording. **Status: ✅ Done (2026-09-08) — spec: `SPECS/2026-09-08-more-drama`.**

---

## Long-term vision

A complete, working Interestingifier™ where users record a mundane story and, moments later, hear a gloriously absurd, Aussie-accented retelling — with the whole history kept in SQLite — ready to de-unbore the world.