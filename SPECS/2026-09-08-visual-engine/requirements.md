# The Visual Engine — Requirements

Date: 2026-09-08
Source: ROADMAP.md, fast-finisher stretch features ("A **Visual Engine** that
fires confetti and rainbow borders whenever a story generates.")

## Feature summary

Fire a kitsch celebration (glitter confetti bursting across the page plus a
flashing rainbow border on the interestingified-version panel) every time a
brand-new story lands on screen. Purely presentational, purely frontend,
vanilla HTML/CSS/JS — no backend, API, or schema changes.

This is the second fast-finisher stretch feature on top of the completed
pipeline (transcribe → rewrite → narrate → play) and the Absurdity Slider. A
single call site — *after a story's text is rendered* — starts the fireworks, so
both raisers of new stories (the automatic rewrite after recording, and the
slider's re-rewrite when that feature has landed) light them.

## Scope — in

- **Frontend (`frontend/static/app.js`)**:
  - A pure, testable confetti-piece generator, e.g.
    `makeConfettiPieces(count, pick = Math.random)` returning
    `[{ left, delay, duration, color, size, spin }, ...]` with values inside
    documented ranges and colours drawn from the kitsch palette. The random
    source is injected so `node:test` can assert a deterministic seed.
  - A browser-only `celebrateStory()` that:
    - creates a `.confetti-layer` inside the stage filled with
      `.confetti-piece` spans (styled via CSS custom properties set inline),
    - adds a `.panel--celebrating` class to `#story-panel` (the rainbow
      border),
    - removes both again after the celebration window (~2.5 s) using
      `animationend` plus a max-duration `setTimeout`.
    - is **idempotent and restartable**: calling it again while a celebration
      is running clears the old layer/timer and starts fresh (handles rapid
      consecutive rewrites, e.g. slider flipping).
  - Hook it in exactly one place: `rewriteStory()` right after
    `storyText.textContent = data.story;`. Every new story flows through that
    line, so every new story celebrates.
- **Frontend (`frontend/static/style.css`)**:
  - `@keyframes confetti-fall` — an absolutely-positioned piece falls from
    above the viewport to below it with a gentle horizontal sway and spin, using
    per-piece `--fall-duration`, `--delay`, `--drift`, and `--spin` custom
    properties set inline from JS.
  - A `.confetti-layer` / `.confetti-piece` position scheme so the burst spans
    the whole stage width.
  - `@keyframes rainbow-border` — cycles the story panel's `border-color` and
    `box-shadow` through the neon palette while `.panel--celebrating` is
    present; the panel returns to normal when the class is removed.
  - Animation styles deliberately live in the stylesheet (not inline), keeping
    the JS small and the kitsch consistent with the existing brand.
- **Tests**: `node:test` for the pure piece generator (RED first). The DOM
  wiring itself is manual-verification scope (the repo has no headless-DOM
  test runner, and the frontend suite already keeps DOM effects manual while
  testing the pure helpers).

## Scope — out (later milestones / later specs)

- No Clickbait Title Generator or "More Drama!" re-roll button — separate
  stretch features, each with its own spec.
- No changes to `services.py`, `db.py`, `app.py`, or any `/api/*` route.
- No new dependency, library, or framework (no canvas, no confetti package —
  pure CSS + a few absolutely-positioned spans).
- No persistence: the animation is ephemeral by design; nothing is stored.
- No `prefers-reduced-motion` guard — the user decision today is **always
  animate** (the kitsch brand wins).
- No backend logging to add: there is no business logic on the backend for this
  feature. Frontend behaviour is presentational; the existing pattern of
  `console.*` on failure paths in `app.js` is reused where relevant.

## Decisions

- **Confetti across the whole stage + rainbow border on the story panel.**
  Confetti pieces fall over the main `.stage`; the rainbow flash is scoped to
  `#story-panel`'s border/glow. When the celebration ends, both reset — the
  page returns to normal.
- **Fire on every new story text.** The hook is a single call in
  `rewriteStory()` after the story text is written. Because the automatic
  rewrite and the Absurdity Slider's re-rewrite both land new text through that
  one function, both triggers celebrate for free — no separate invocations to
  keep in sync.
- **Always animate (no reduced-motion guard).** Explicit user decision
  (2026-09-08): skip `prefers-reduced-motion` handling; celebrations play for
  everyone.
- **Purely additive, so no backward-compatibility decision exists.** The feature
  adds classes, a dynamic layer, and new keyframes; no existing behaviour is
  changed or removed, and no API contract is touched — nothing to preserve.
- **Celebration window ~2.5 seconds.** Confetti `animation-duration` values
  roughly 1.2–2.5 s; the layer and the `panel--celebrating` class are torn down
  at the window's end. A stray race is impossible because a running celebration
  is always torn-down (not doubled) on restart.
- **Randomness injected for tests.** `makeConfettiPieces(count, pick)` takes the
  random source as an argument and defaults to `Math.random`, so node:test can
  assert exact, deterministic bounds without a browser.

## Context

`app.js` is a vanilla ES module with a clean split: pure helpers are exported
and covered by the `node:test` suite; DOM wiring lives in `main()` and is
guarded by `typeof document`. `rewriteStory(transcript)` is the single function
that writes a new story into `#story-text` and then narrates it — the natural,
single trigger point. `style.css` already carries the kitsch brand (leopard
print, neon gradients, glow shadows) and a `--glow-*` palette, so the rainbow
border reads like an intensification of the existing look rather than a new
aesthetic. No backend changes are needed, which keeps this stretch feature
small and reviewable.

## Status

Spec created 2026-09-08 on branch `feature/2026-09-08-visual-engine`, pending
implementation. See `validation.md` for the spec-sync record.