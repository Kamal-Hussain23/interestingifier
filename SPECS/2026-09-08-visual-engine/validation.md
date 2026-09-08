# The Visual Engine — Validation

Date: 2026-09-08
Feature: SPECS/2026-09-08-visual-engine/requirements.md

This step is complete when all of the following pass. The Verifier agent audits
the work against this file before the branch is considered done.

## Automated checks

- `npm test --prefix frontend` — the pure confetti generator is covered:
  - `makeConfettiPieces(60, pick)` returns 60 pieces.
  - With an injected `pick` the descriptors are deterministic and within
    contract ranges (`left` 0–100 %, `delay` 0–0.4 s, `duration` 1.2–2.5 s,
    `size` 6–14 px, `spin` ±420°, `color` in `CONFETTI_PALETTE`).
  - `count = 0` → `[]`.
  All pre-existing frontend tests stay green.
- `npm run lint --prefix frontend` — ESLint clean.
- `ruff check .` and `ruff format --check .` — clean (Python is untouched, but
  the gate still guards the repo).
- `mypy .` — passes under strict; `pytest` — all backend tests still pass.
- `pre-commit run --all-files` — gitleaks, Ruff, mypy, pytest, frontend lint and
  tests all pass. The quality gate must not depend on `GEMINI_API_KEY`.

## TDD evidence

- `frontend/tests/confetti.test.js` was committed before (or in the same commit
  as) `makeConfettiPieces` / `CONFETTI_PALETTE`, and the git history shows the
  red→green sequence for Group 1 in `plan.md`.

## Manual verification

- The page loads with no confetti visible — the celebration only happens when a
  new story lands.
- Record a clip: the transcript appears, then a new story text renders, and at
  that instant confetti pieces fall across the full stage width while the story
  panel's border flashes through rainbow colours, with a bright neon glow.
- After ~2.5 s the layer and the `panel--celebrating` class are gone: the page
  settles back to its normal kitsch state (the panel's dotted gold border and
  the layout are pixel-identical to before).
- Recording again re-fires the celebration. Rapid consecutive rewrites never
  leave stacked layers or a stuck rainbow border.
- Confetti is not interactive-blocking (`pointer-events: none`): the record
  button and slider remain clickable under the falling pieces.
- The server responds through the Codio public URL (bind to `0.0.0.0`, then
  curl the `https://${CODIO_HOSTNAME}-3000.codio.io/` URL).

## Spec sync

- On merge, update ROADMAP.md to mark the stretch feature "Visual Engine" done,
  and record any approved deviations and implementation notes here (as the
  previous features did).

## Out of scope (must NOT be present)

- No Clickbait Title Generator or "More Drama!" re-roll button.
- No changes to `services.py`, `db.py`, `app.py`, or any `/api/*` route.
- No new dependency, library, or framework (no canvas, no confetti package).
- No persistence of the animation state (nothing stored in SQLite).
- No `prefers-reduced-motion` guard (user decision: always animate).