# The Kitsch-Styled Frontend Shell — Plan

Date: 2026-08-14
Feature: SPECS/2026-08-14-kitsch-frontend-shell/requirements.md

TDD note: in group 4 (recording logic), write the failing test first (red), then
the minimal code to make it pass (green). At the end of each group, run the
quality gate from group 6. Styling and layout are verified manually in the
browser — they are not unit-testable.

## Group 1 — Node 20 and frontend tooling

- Create `setup.sh` (idempotent):
  - `pip install -r requirements.txt` (backend deps).
  - If nvm is absent, install it (standard `install.sh` from the nvm repo).
  - `source` nvm, `nvm install 20` (installs Node 20 LTS).
  - Symlink `node`, `npm`, `npx` from the nvm version dir into `~/bin` (already
    on PATH) with `ln -sf` so they win over the system Node 12 in every shell,
    including non-interactive pre-commit runs.
- Run `bash setup.sh`; verify `node --version` reports v20.x and `npm --version`
  is the matching npm.
- Update `frontend/package.json`:
  - Add `"type": "module"`.
  - Add devDependencies: `eslint` (^9), `@eslint/js` (^9), `globals`.
  - Replace the no-op scripts:
    - `"lint": "eslint static tests"`
    - `"test": "node --test tests/"`
- Add `frontend/eslint.config.js` (flat config): `@eslint/js` recommended rules,
  a `static` block with browser globals (`globals.browser`), and a `tests` block
  with node globals (`globals.node`).
- Run `npm install` in `frontend/` so `node_modules` and `package-lock.json`
  appear; commit the lockfile.
- Verify `npm run lint` and `npm test` both pass with the current placeholder
  files (empty `tests/` dir may make `node --test tests/` error, so the test
  file from group 4 must exist before the gate run — see note in group 4).

## Group 2 — HTML shell (`frontend/static/index.html`)

- Rebuild `index.html` as a `<script type="module">` page with the shell from
  requirements:
  - Header with the brand and tagline.
  - Main record section: the big record/stop `<button>` (with an accessible
    label and `aria-pressed` reflecting state) and a `<p>` status line.
  - Input/output panels: *Your boring anecdote* and *The interestingified
    version*, each a labelled empty region.
  - Playback area: a hidden `<audio controls>` element.
  - History section with the empty-state message.
- Give every JS hook a stable, clearly-named `id` (e.g. `record-btn`,
  `status-line`, `preview-audio`, `transcript-panel`, `story-panel`,
  `history-list`). No inline JS.

## Group 3 — Kitsch styling (`frontend/static/style.css`)

- Define the kitsch palette as CSS custom properties on `:root` (clashing neon
  pinks/greens, golds, plus shared border-radius and glow tokens).
- Style the whole page:
  - Leopard-print background from stacked gradients (no images).
  - Neon gradient hero/panels and "rhinestone" glow borders via `box-shadow`.
  - Playful local/system font stack (e.g. `"Comic Sans MS", "Chalkboard SE",
    "Comic Neue", cursive` fallbacks) with bold, colourful text styling.
  - Record button states: idle / recording / recorded (distinct colour, glow,
    and label-appropriate style driven by a `.recording` / `.recorded` class).
  - Hidden-by-default preview element revealed when there is audio.
  - Reasonable narrow-width responsiveness (panels stack, button stays big).
- Manual check: the page is loud, joyful, and clearly finished (per MISSION.md).

## Group 4 — Recording logic (`frontend/static/app.js`) — TDD

- **Write the failing test first** (`frontend/tests/recorder-state.test.js`,
  using `node:test` + `node:assert/strict`):
  - Valid transitions of the pure `nextState(state, action)` helper:
    `idle + start → recording`, `recording + stop → recorded`,
    `recorded + clear → idle`.
  - Invalid transitions throw (e.g. `recording + start`, `idle + stop`,
    unknown state/action). Assert with `assert.throws`.
- Run `npm test` and watch it fail (red). (This also satisfies the empty-tests
  concern from group 1.)
- Implement `app.js` as an ES module:
  - Export the pure helpers (the record-state machine, and any tiny helpers
    like a `statusText(state)` map) with no DOM access at module scope.
  - Guard the DOM wiring so it only runs when a `document` exists (so Node can
    import the module).
  - DOM wiring (`main`):
    - Clicking the button toggles the state machine; the button label, class,
      and status line follow the state.
    - On `start`: `navigator.mediaDevices.getUserMedia({ audio: true })` →
      `new MediaRecorder(stream)` (default mimeType; no format forcing) →
      collect `dataavailable` chunks.
    - On `stop`: `new Blob(chunks)` → `URL.createObjectURL(blob)` → set
      `<audio src>` and reveal the preview. Keep the Blob on a module-level
      variable, documented as the seam the later upload milestone reuses.
    - Stop the stream tracks when recording stops.
  - Error handling: if `MediaRecorder` or `getUserMedia` is missing, or the mic
    is denied, show a friendly message in the status line and return the state
    machine to `idle`. No crashes.
- Run `npm test` until green; run the full quality gate.

## Group 5 — README and docs

- Update `README.md` Setup: `bash setup.sh` now installs backend deps **and**
  Node 20 for the frontend tooling.

## Group 6 — Quality gate and manual verification

- Run and fix until green:
  - `npm run lint --prefix frontend`
  - `npm test --prefix frontend`
  - `ruff check .` and `ruff format --check .` (backend untouched, still green)
  - `mypy .`
  - `pytest`
  - `pre-commit run --all-files`
- Start the server (`python app.py`) and verify through the Codio public URL:
  - The page loads with full kitsch styling (leopard print, neon, glow).
  - Click record → mic permission prompt → speak → click stop → the preview
    plays back the recording; button state and status line update correctly.
  - Recording again resets cleanly (`recorded + clear → idle` flow).
  - The history section shows the empty state.
  - Narrow the window: layout still looks good.