# The Kitsch-Styled Frontend Shell — Validation

Date: 2026-08-14
Feature: SPECS/2026-08-14-kitsch-frontend-shell/requirements.md

This step is complete when all of the following pass. The Verifier agent audits
the work against this file before the branch is considered done.

## Automated checks

- `npm run lint --prefix frontend` — ESLint passes over `static/` and `tests/`.
- `npm test --prefix frontend` — `node:test` passes, including
  `frontend/tests/recorder-state.test.js` covering:
  - valid transitions of the record-state machine
    (`idle+start → recording`, `recording+stop → recorded`,
    `recorded+clear → idle`),
  - invalid transitions throwing.
- `node --version` — v20.x is the resolved `node` on PATH (so the pre-commit
  hooks run the modern tooling).
- `ruff check .`, `ruff format --check .`, `mypy .`, `pytest` — the backend is
  untouched by this step and all remain green.
- `pre-commit run --all-files` — gitleaks, Ruff, mypy, pytest, frontend lint,
  and frontend tests all pass.
- `package-lock.json` is committed; `node_modules/` is gitignored.

## TDD evidence

- The recorder-state test file was committed before (or in the same commit as)
  `app.js`'s implementation, and the git history shows the red→green sequence
  for the recording logic in group 4.

## Manual verification (via the Codio public URL)

- `bash setup.sh` completes successfully and is idempotent (runs again without
  error), and `node --version` is v20.x afterwards.
- The page loads at `https://${CODIO_HOSTNAME}-3000.codio.io/` with the full
  kitsch aesthetic visible: leopard-print background, neon gradients,
  glow/"rhinestone" borders, clashing colors, playful fonts. It reads as loud,
  joyful, and *finished* — never bare-bones.
- The record/stop flow works end-to-end at the UI level:
  - Clicking the big button prompts for the microphone and starts recording;
    the button and status line switch to the recording state.
  - Clicking stop ends recording, reveals the preview control, and the recorded
    clip plays back in the browser.
  - Recording again from the `recorded` state resets cleanly.
  - Denying the microphone shows a friendly message in the status line and does
    not crash.
- The input/output panels (`Your boring anecdote` / `The interestingified
  version`) are present and empty, ready for later milestones.
- The history section shows the "No Interestingifications yet" empty state.
- Narrowing the window keeps the layout usable.
- No upload happens: the browser Network tab shows no POST of the audio — the
  Blob is held client-side only.

## Spec sync

- The implemented UI and recording seam match this spec and the roadmap
  (Cycle 1, Step 2). Verified 2026-08-14 on branch
  `feature/2026-08-14-kitsch-frontend-shell`.
- **All automated checks passed**, and the user confirmed in a browser that the
  kitsch site renders and the record/listen loop works end-to-end through the
  Codio public URL.
- **Approved deviations / notes:**
  - The captured Blob is built in the recorder's `onstop` handler and consumed
    into the preview object URL. It is not yet retained in a module-level
    variable — the Cycle 2 upload milestone will formalise that seam when it
    adds the POST.
  - `setup.sh` pins nvm `v0.40.1`; any recent nvm release behaves the same.
  - Operational note (not a code deviation): the server must run detached
    (`setsid nohup python app.py &`) to survive the terminal, otherwise the
    public URL returns 502 while the box is otherwise healthy.

## Out of scope (must NOT be present)

- No `fetch`/POST of recorded audio anywhere in the frontend.
- No Gemini API calls, keys, or AI service helpers.
- No new backend endpoints and no changes to `app.py` or `db.py`.
- No database/schema changes.
- No dynamically populated history data.
- No story/Text-to-Speech playback — the only playable audio is the user's own
  just-recorded preview.
- No external web fonts or image assets (works fully offline in the box).