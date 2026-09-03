# The Kitsch-Styled Frontend Shell — Requirements

Date: 2026-08-14
Source: ROADMAP.md, Cycle 1, Step 2 (The kitsch-styled frontend shell)

## Feature summary

Replace the bare placeholder frontend with a complete, polished, eccentric-kitsch
shell: a big record button, a status/input area, an audio playback area, and a
history section. Wire up the recording plumbing in `app.js` so the record button
works end-to-end at the UI level — capturing audio with `MediaRecorder` and
holding the result as a Blob, ready to POST in a later milestone. Also stand up
real frontend tooling (ESLint + Node's `node:test`) so the pre-commit hooks do
useful work, and create `setup.sh` (already referenced by the README) which
installs Node 20 so that modern tooling can run.

## Scope — in

- **`frontend/static/index.html`** — a complete shell with:
  - A brand header ("Interestingifier™", tagline "Take boring. Make it
    interesting.").
  - A big record/stop button (the hero element) plus a status line that tells
    the user what is happening ("Recording…", "Got it! Hit play below.").
  - An input/output area with two clearly-labelled panels: *Your boring
    anecdote* (transcript) and *The interestingified version* (story). These are
    empty placeholders in this step — real text arrives in later milestones.
  - A playback area: an `<audio>` element that plays back the just-recorded
    clip. Hidden until there is something to play.
  - A history section titled something like "Past Interestingifications",
    showing a friendly empty state ("No Interestingifications yet — record your
    first one!"). Markup is shaped so later milestones can populate it from the
    API.
- **`frontend/static/style.css`** — full eccentric-kitsch styling that must look
  loud, joyful, and *finished*, never bare-bones:
  - Leopard-print surface achieved with pure CSS gradients (no image files).
  - Neon gradients and glow borders ("rhinestones") built from CSS custom
    properties (a single editable palette).
  - Clashing colors and playful fonts via a local/system font stack (no external
    web fonts — must work offline in the Codio box).
  - Distinct visual states for the record button: idle, recording, recorded.
  - A responsive layout that still looks good at a narrow window width.
- **`frontend/static/app.js`** — an ES module exporting small, pure, testable
  helpers plus the DOM wiring:
  - A tiny record-state machine (`idle` / `recording` / `recorded`) as a pure
    function so it can be unit-tested with `node:test`.
  - Recording plumbing: `getUserMedia({ audio: true })` → `MediaRecorder` →
    on stop, build a Blob, create an object URL, and point the `<audio>` element
    at it so the user can preview their clip. The Blob is held "ready to POST" —
    no fetch happens in this step.
  - Friendly handling when the microphone is denied or `MediaRecorder` /
    `getUserMedia` is unsupported (a clear message in the status line, no
    crash).
  - The DOM wiring runs only when a `document` exists, so the module can be
    imported safely by the test runner.
- **Frontend tooling** — decided here, as deferred by the Step 1 spec:
  - `frontend/package.json` gains `"type": "module"`, an ESLint 9 flat config
    (`eslint.config.js`) with `@eslint/js`, and real scripts:
    - `lint`: `eslint static tests`
    - `test`: `node --test tests/`
  - A `node:test` test file (e.g. `frontend/tests/recorder-state.test.js`) that
    covers the record-state machine (valid and invalid transitions).
  - `node_modules` and `package-lock.json` are created by `npm install`; the
    lockfile is committed, `node_modules` stays gitignored.
- **`setup.sh`** — create it (the README already tells students to run it):
  - Installs backend dependencies from `requirements.txt`.
  - Installs Node 20 LTS via nvm and symlinks `node`, `npm`, and `npx` into
    `~/bin` (already on PATH) so every shell — including the non-interactive
    pre-commit hooks — resolves Node 20.
  - Idempotent: safe to run again.
- **`README.md`** — update the Setup section so it mentions that `setup.sh`
  also installs Node 20 for the frontend tooling.

## Scope — out (later steps / later specs)

- No upload or POST of the recorded audio (the Blob is held ready only).
- No Gemini calls of any kind, no API-key handling.
- No new backend endpoints or backend code changes.
- No database or schema changes.
- No real history data — the history section is a static empty state.
- No playback of generated stories (only the user's own recording preview).
- No kitsch *beyond* the shell: confetti, sliders, clickbait titles, and the
  other stretch features from the roadmap are out of scope.

## Decisions

- **Frontend tooling: ESLint 9 + Node's built-in `node:test`.** No Jest or
  Vitest dependency — the standard Node test runner keeps the toolchain tiny and
  beginner-friendly. ESLint uses the modern flat config.
- **Install Node 20 LTS.** The Codio box ships Node 12, which cannot run
  `node:test` or ESLint 9. `setup.sh` installs Node 20 via nvm and symlinks the
  binaries into `~/bin` (already on PATH, user-writable) so the `language:
  system` pre-commit hooks pick it up in any shell. This was confirmed to work:
  the npm registry is reachable from the box.
- **`app.js` is an ES module** (`<script type="module">`, `"type": "module"` in
  `package.json`). This lets `node:test` import the pure helpers directly.
- **Recording boundary: Blob ready, no POST.** `MediaRecorder` captures audio;
  on stop we hold the Blob and show a playable preview. The actual upload +
  transcribe is Cycle 2 milestone 1, which will reuse this Blob seam.
- **Playback area: preview of the just-recorded clip** via `<audio>` + object
  URL. The same element is reused later for Text-to-Speech output.
- **History: static empty state.** Markup and classes are chosen so a later
  milestone can render real entries from the API without restructuring.
- **Kitsch aesthetic, no external assets.** Leopard print and neon/rhinestone
  effects are pure CSS (gradients + box/text shadows) from a small set of CSS
  custom properties; fonts come from a local playful system stack. This keeps
  the app fully functional offline in the Codio box and respects MISSION.md's
  non-negotiable kitsch.
- **Backward compatibility.** The placeholder `index.html`, `style.css`, and
  `app.js` from Step 1 are intentionally replaced wholesale — they were placeholders
  with no behaviour to preserve. No other files' contracts change.
- **Flask serving is untouched.** The backend already serves `frontend/static`
  as the static folder, so no `app.py` changes are needed.

## Context

This step is the aesthetic heart of the project: MISSION.md is explicit that the
app must look loud, joyful, and finished, and that the kitsch aesthetic is never
negotiable. It also establishes the frontend seams the rest of the product
builds on — the record button produces a Blob for later upload, the transcript
and story panels wait for text, and the playback element is shared with the
future TTS narrator. Because the box's Node is ancient, the tooling decision in
this spec also unblocks every later frontend milestone.

## Status

Implemented and verified 2026-08-14 on branch
`feature/2026-08-14-kitsch-frontend-shell`; user confirmed the kitsch UI and the
record/listen loop work in the browser. See `validation.md` for the spec-sync
record.