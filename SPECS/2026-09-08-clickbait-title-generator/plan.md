# The Clickbait Title Generator — Plan

Date: 2026-09-08
Feature: SPECS/2026-09-08-clickbait-title-generator/requirements.md

TDD groups in order. Write each Red test first, watch it fail, then the minimal
Green code. Proceed group by group; keep everything green before moving on.

## Group 1 — Service: `generate_headline` (`services.py`) — TDD

- Add `tests/test_services.py` cases (Red first, using the existing fake
  `build_client` pattern):
  - `generate_headline(story)` sends a `generate_content` call on
    `HEADLINE_MODEL` with contents `[HEADLINE_PROMPT, story]` (assert the fake
    received the right model + prompt).
  - The returned headline is the model's text uppercased
    (`"big news!!"` → `"BIG NEWS!!"`).
  - Empty `response.text` (fake returns `None`) raises
    `RuntimeError("Gemini returned an empty headline response.")`.
- Implement `HEADLINE_PROMPT`, `HEADLINE_MODEL`, and `@logged
  generate_headline` mirroring `rewrite_story`, returning
  `response.text.upper()`.
- `ruff`, `mypy`, GREEN.

## Group 2 — Persistence (`models.py`, `db.py`) — TDD

- Add `tests/test_db.py` cases (Red first):
  - A fresh `init_db` schema has a `headline` column in `stories` with default
    `''` (`PRAGMA table_info` check).
  - The existing "old stories table without the new column" fixture (built via
    the same trick used for `absurdity`) gets `headline` added by
    `upgrade_stories_schema` idempotently — a second call is a no-op and
    existing rows keep their data with `headline = ''`.
  - `save_story(…, headline="SHOCKING!")` stores it and the returned `Story`
    has it; the no-headline default stays `''`.
  - `fetch_story` and `list_stories` round-trip `headline`.
- Implement: `Story.headline: str = ""`, `stories` CREATE TABLE + the second
  check in `upgrade_stories_schema`, `save_story` param + INSERT + SELECT
  includes, and the two fetch SELECTs rebuild `Story(headline=…)`.
- Existing db tests keep passing unchanged (additive default).
- `ruff`, `mypy`, GREEN.

## Group 3 — API route (`models.py`, `app.py`) — TDD

- Add `tests/test_app.py` cases (Red first):
  - A successful `POST /api/rewrite` returns JSON with both `story` and
    `headline`, where the headline comes from a stubbed/adjusted
    `services.generate_headline` (the suite already swaps services via
    patch/fake).
  - The persisted story row carries that headline.
  - When the fake `generate_headline` raises a generic exception, the response
    is still `200` with the story and `headline: ""`, and the story is saved.
  - When it raises `NotImplementedError`, the route returns the existing
    structured `not_implemented` 501.
  - Existing rewrite tests (no headline involved) keep passing — they use the
    old constructors, exercise the backward-compat defaults.
- Implement: `StoryResponse.headline: str = ""`, and in `rewrite()` call
  `services.generate_headline(story)` (guarding `NotImplementedError` first,
  then degrading any other exception to `""`), pass `headline=` to
  `db.save_story`, and include it in the response.
- `ruff`, `mypy`, `pytest`, GREEN.

## Group 4 — Frontend (`index.html`, `app.js`, `style.css`) — TDD for the pure part

- Add `frontend/tests/` cases (Red first):
  - `formatHeadline(undefined)` → `""`; `formatHeadline(null)` → `""`;
    `formatHeadline("")` → `""`; `formatHeadline("  SHOUT  ")` →
    `"SHOUT"`; a normal string passes through trimmed.
- Implement `formatHeadline` exported from `app.js`, then browser wiring in
  `rewriteStory`:
  - `const storyHeadline = document.getElementById("story-headline");`
  - After `const data = await response.json();` —
    `const headline = formatHeadline(data.headline); storyHeadline.textContent =
    headline; storyHeadline.hidden = headline === "";` then the existing story
    text + narrate calls.
- `index.html`: place `<p id="story-headline" class="headline" hidden></p>`
  between the story panel title and `#story-text`.
- `style.css`: `.headline` — neon gradient text over the panel, bold
  letter-spacing, small bottom margin; `[hidden]` stays hidden.
- `npm test` (frontend) + `npm run lint --prefix frontend` GREEN; manual
  browser check listed in validation.md.

## Group 5 — Quality gate, live verification, spec sync

- Run and fix until green: `ruff check .`, `ruff format --check .`, `mypy .`,
  `pytest`, `npm test --prefix frontend`, `npm run lint --prefix frontend`,
  `pre-commit run --all-files` (no `GEMINI_API_KEY` dependency).
- Start the server bound to `0.0.0.0:3000` and verify through the Codio public
  URL (per AGENTS.md): `/`, `/static/app.js`, `/static/style.css`,
  `/api/health` all 200.
- Manual end-to-end on the live URL: record → transcript → story renders with a
  punchy ALL-CAPS headline above it; an empty-headline failure path (if
  reproducible) shows the story with no caption; the stored row in
  `interestingifier.db` has the headline; slider re-rewrites (once that feature
  merges) get a fresh headline because they share `rewriteStory`.
- Spec sync: update this `validation.md` and ROADMAP's stretch entry (approved
  deviations, implementation notes, merge record).