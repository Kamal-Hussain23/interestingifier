# The "More Drama!" Re-roll — Plan

Date: 2026-09-08
Feature: SPECS/2026-09-08-more-drama/requirements.md

TDD groups in order. Write each Red test first, watch it fail, then the minimal
Green code. Keep everything green before moving on.

## Group 1 — Service: twists + `rewrite_story` keyword (`services.py`) — TDD

- Add `tests/test_services.py` cases (Red first, fake `build_client` pattern):
  - `DRAMA_TWISTS` is a non-empty list of non-empty strings (guards typos).
  - `pick_drama_twist(pick)` returns exactly `pick(...)` — with an injected
    `pick = lambda seq: seq[2]` the third twist comes back (deterministic).
  - `rewrite_story(transcript, twist="New angle")` sends contents
    `[REWRITE_PROMPTS[level], "New angle", transcript]` (assert the fake
    received exactly that list).
  - `rewrite_story(transcript)` with no twist sends contents
    `[REWRITE_PROMPTS[level], transcript]` — unchanged from today.
- Implement `DRAMA_TWISTS`, `pick_drama_twist`, and the `twist: str | None =
  None` parameter on `rewrite_story` (contents list built conditionally). Mine
  the twist list from the kitsch voice in the existing prompts.
- `ruff`, `mypy`, GREEN.

## Group 2 — API route (`app.py`) — TDD

- Add `tests/test_app.py` cases (Red first, existing services-patch pattern):
  - `parse_drama_flag({})` → `False`; `parse_drama_flag({"drama": True})` →
    `True`; `parse_drama_flag({"drama": "true"})` → `True`;
    `parse_drama_flag({"drama": "nonsense"})` → `False` (lenient).
  - `POST /api/rewrite` with `{"transcript": ..., "drama": true}` calls
    `services.rewrite_story` with a `twist=` from `pick_drama_twist` (patch
    both and assert the twist is threaded in).
  - The same request saves a **new** stories row for the transcript (two
    re-rolls → two distinct story ids sharing one `transcript_id`).
  - No `drama` flag → `rewrite_story` called with default/no twist — existing
    rewrite tests keep passing unchanged.
- Implement `parse_drama_flag` (mirrors `parse_absurdity` as a single lenient
  validation point) and the `drama` → `pick_drama_twist()` wiring in
  `rewrite()`. Persistence needs no change (`save_story` already inserts a row
  per request).
- `ruff`, `mypy`, `pytest`, GREEN.

## Group 3 — Frontend pure body builder (`app.js`) — TDD

- Add `frontend/tests/` cases (Red first):
  - `buildRewriteBody("T", "unhinged", false)` → `{"transcript":"T", "absurdity":"unhinged"}` (today's exact body).
  - `buildRewriteBody("T", "unhinged", true)` → `{"transcript":"T", "absurdity":"unhinged", "drama":true}`.
  - `buildRewriteBody("T", null, true)` → `{"transcript":"T", "drama":true}` (twist without a slider choice).
  - No-side-effects check: the old two-arg call stays byte-identical.
- Implement the `drama` third parameter on `buildRewriteBody`.
- `npm test` (frontend) + `npm run lint --prefix frontend`, GREEN.

## Group 4 — Browser wiring + CSS (`app.js`, `index.html`, `style.css`) — manual verify

- `rewriteStory(transcript, drama = false)` passes `drama` into
  `buildRewriteBody`.
- New `#more-drama-btn` in the story panel, disabled until `currentTranscript`
  is set (enable inside `uploadForTranscription` when the transcript lands);
  click handler: `if (currentTranscript) { rewriteStory(currentTranscript,
  true); }` — the fresh story re-narrates exactly like a slider re-rewrite, and
  the Visual Engine/headline features (when merged) inherit it via the same
  seam.
- Kitsch button styles in `style.css` (neon, hover glow) consistent with the
  slider; disabled state visually muted.
- Manual verification:
  - Page load: the button is disabled, no transcript.
  - Record → transcript appears → button enabled.
  - Press More Drama! several times: each click lands a *different* story and
    re-narrates; stored rows accumulate (ids increase, one transcript).

## Group 5 — Quality gate, live verification, spec sync

- Run and fix until green: `ruff check .`, `ruff format --check .`, `mypy .`,
  `pytest`, `npm test --prefix frontend`, `npm run lint --prefix frontend`,
  `pre-commit run --all-files` (no `GEMINI_API_KEY` dependency).
- Start the server bound to `0.0.0.0:3000` and verify through the Codio public
  URL (per AGENTS.md): `/`, `/static/app.js`, `/static/style.css`,
  `/api/health` all 200.
- Manual end-to-end on the live URL: record once, then three More Drama! clicks
  in a row — distinct stories each time, audio re-narrated, and
  `interestingifier.db` shows three story rows on one transcript. `curl` a
  `POST /api/rewrite` with `"drama": true` and without to compare bodies.
- Spec sync: update this `validation.md` and ROADMAP's stretch entry (approved
  deviations, implementation notes, merge record).