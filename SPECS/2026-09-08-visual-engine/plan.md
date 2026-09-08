# The Visual Engine — Plan

Date: 2026-09-08
Feature: SPECS/2026-09-08-visual-engine/requirements.md

TDD note: write the failing test first (red), watch it fail, then write the
minimal code to make it pass (green). This feature is pure frontend; the
automated groups live in the frontend `node:test` suite, and the DOM/CSS
effects are verified manually (the repo's frontend test suite has no headless
DOM, and DOM wiring is already manual-verification scope by precedent).

## Group 1 — Pure confetti generator (`app.js`) — TDD

- Add `frontend/tests/confetti.test.js`:
  - `makeConfettiPieces(60, pick)` returns exactly 60 pieces.
  - With an injected `pick` that always returns 0.5, every piece is
    deterministic and within contract ranges: `left` 0–100, `delay` within
    [0, 0.4] s, `duration` within [1.2, 2.5] s, `size` within [6, 14] px,
    `spin` within [±420], and `color` drawn from the kitsch palette constant.
  - All 60 `color` values are members of the exported `CONFETTI_PALETTE`
    (guards against typos in the palette list).
  - `count = 0` returns an empty list (safe no-op).
- Run `npm test` and watch the new file fail (red) — `makeConfettiPieces` and
  `CONFETTI_PALETTE` do not exist yet.
- Implement in `app.js`: export `CONFETTI_PALETTE` (neon pink, neon green,
  neon blue, gold, sunset orange — reuse the existing `--neon-*`/`--gold`
  hexes so it matches the brand) and `makeConfettiPieces(count, pick =
  Math.random)` returning descriptor objects with clamped, formatted values
  (`left` as a percentage string, `delay`/`duration` as seconds with `s`,
  `size` as a pixel string, `spin` as a rotation degrees string).
- Run `npm test` until green.

## Group 2 — DOM celebration wiring (`app.js`, inside `main()`) — manual verify

- Implement browser-only helpers next to the other DOM wiring:
  - `celebrateStory()` (module-level, guarded by `typeof document`):
    - Clears any running celebration first (remove an existing
      `.confetti-layer`, clear the max-duration timer) so bursts never stack.
    - Builds a `.confetti-layer` appended to `main.stage`, filled with one
      `.confetti-piece` span per `makeConfettiPieces(CONFETTI_COUNT)`; each
      span's style sets `--left`, `--delay`, `--duration`, `--drift`, `--spin`,
      `--size`, `--color` from its descriptor.
    - Adds `panel--celebrating` to `#story-panel`.
    - Tears down on `animationend` of the last piece, plus a belt-and-braces
      `setTimeout(CONFETTI_WINDOW_MS)` that removes the layer and the class so
      the page always settles back to normal.
  - Call `celebrateStory()` in `rewriteStory()` immediately after
    `storyText.textContent = data.story;` — the single trigger point.
- Exported constants for the plan's reviewers: `CONFETTI_COUNT` (60),
  `CONFETTI_WINDOW_MS` (2500).
- Manual verification (no automated DOM test — matches repo precedent):
  - Load `/` — no confetti until a story generates; the slider is not present
    on this branch yet (spec branch is off `main`).
  - Record a clip → transcription → a new story text lands → confetti falls
    across the stage and the story panel's border flashes a rainbow, then both
    reset after ~2.5 s.
  - Record again → celebration re-fires.
  - Cats-on-keyboard check: rapidly re-rewriting never leaves stacked layers or
    a stuck rainbow border (restart path tears down first).

## Group 3 — CSS (`style.css`) — manual verify

- Add the kitsch celebration styles:
  - `.confetti-layer` — `position: fixed; inset: 0; pointer-events: none;
    overflow: hidden; z-index` above the page but below nothing interactive.
  - `.confetti-piece` — absolutely positioned at `left: var(--left)`, a small
    neon rectangle using `background: var(--color)`, `width/height` from
    `var(--size)`, slight initial rotation, and `animation:
    confetti-fall var(--duration) ease-in var(--delay) forwards`.
  - `@keyframes confetti-fall` — from `translateY(-5vh) rotate(0deg)` toward
    `translateY(110vh) rotate(var(--spin))` with a horizontal sway
    (`translateX` percent from `--drift`), fading in then holding at the end.
  - `.panel--celebrating` — `animation: rainbow-border 1.2s linear infinite;`
    with `@keyframes rainbow-border` cycling `border-color` and a bright
    `box-shadow` through the neon palette; the panel's normal dotted gold
    border returns when the class is removed.
  - No `prefers-reduced-motion` guard (user decision: always animate).
- Manual verify: the burst covers the full stage width, pieces can't be
  clicked/blocked (`pointer-events: none`), the story panel reads as
  "celebrating rainbow" while the class is present and is pixel-identical to
  before once it settles.

## Group 4 — Quality gate, live verification, spec sync

- Run and fix until green:
  - `npm run lint --prefix frontend` and `npm test --prefix frontend`
  - `ruff check .` and `ruff format --check .` (guards the repo for the
    unchanged Python)
  - `mypy .` and `pytest`
  - `pre-commit run --all-files`
- Start the server (`setsid nohup python app.py &`, bound to `0.0.0.0:3000`)
  and verify through the Codio public URL (per AGENTS.md): the page loads, and
  curl of `/`, `/static/app.js`, `/static/style.css`, `/api/health` all 200.
- Manual end-to-end against the live URL: record once → story appears with
  confetti + rainbow border → celebration resets; slider re-rewrites (once that
  feature is merged) also celebrate because they share `rewriteStory`.
- Spec sync: update this `validation.md` and ROADMAP's stretch-feature entry
  (approved deviations, implementation notes, merge record).