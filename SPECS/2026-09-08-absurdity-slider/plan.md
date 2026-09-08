# The Absurdity Slider — Plan

Date: 2026-09-08
Feature: SPECS/2026-09-08-absurdity-slider/requirements.md

TDD note: in every group, write the failing test first (red), watch it fail, then
write the minimal code to make it pass (green). Run the focused test file at the
end of each group; run the full quality gate in the final group.

Order matters: models before services before route before frontend.

## Group 1 — Models (`models.py`) — TDD

- Add `tests/test_models.py`:
  - `Absurdity` members have the exact wire tokens
    (`slightly_weird`, `unhinged`, `total_fever_dream`).
  - `Absurdity.from_token` parses each token
    (`Absurdity.from_token("unhinged") is Absurdity.UNHINGED`).
  - `Absurdity.from_token` raises `ValueError` for an unknown token and the
    message lists the allowed tokens.
  - `Story` includes an `absurdity` field (construct with it, assert equality).
- Run `pytest tests/test_models.py` and watch it fail (red) — the enum does not
  exist yet.
- Implement in `models.py`: the `Absurdity` enum (with `from_token` raising a
  clear `ValueError`) and the `absurdity: str` field on `Story`.
- Run `pytest tests/test_models.py` until green.

## Group 2 — Persistence (`db.py`) — TDD

- Update `tests/test_db.py`:
  - A freshly initialised DB has an `absurdity` column on `stories`
    (inspect `PRAGMA table_info`).
  - A DB created with the *old* schema (no column) is upgraded by `init_db`:
    the column appears and pre-existing rows read back `unhinged`.
  - `save_story(transcript_id, text, absurdity="total_fever_dream")` persists
    the level and `fetch_story` / `list_stories` return it.
  - Omitting `absurdity` from `save_story` stores the default
    (`unhinged`) via the column's DEFAULT — keep the signature simple.
- Run `pytest tests/test_db.py` and watch the new tests fail (red).
- Implement in `db.py`:
  - Add `absurdity TEXT NOT NULL DEFAULT 'unhinged'` to the `stories`
    `CREATE TABLE`; keep `save_story`/`fetch_story`/`list_stories` reading and
    writing it (add a small helper to upgrade an existing table via
    `PRAGMA table_info(stories)` + idempotent `ALTER TABLE`, called from
    `init_db` after the `executescript`).
- Run `pytest tests/test_db.py` until green.

## Group 3 — Service (`services.py`) — TDD

- Update `tests/test_services.py` (the fake `build_client` seam already captures
  `last_kwargs`):
  - `rewrite_story(transcript, Absurdity.SLIGHTLY_WEIRD)` sends the *Slightly
    Weird* prompt as the first `contents` element.
  - Same for `UNHINGED` and `TOTAL_FEVER_DREAM` — one test per level asserting
    the right prompt is used, and that the three prompts differ.
  - Calling without a level uses the `UNHINGED` prompt (backward compatible).
  - Existing rewrite/transcribe/narrate tests stay green (update any that
    reference the old `REWRITE_PROMPT` constant to the new map).
- Run `pytest tests/test_services.py`, watch the new level tests fail (red).
- Implement in `services.py`: `REWRITE_PROMPTS: dict[Absurdity, str]` (the old
  prompt is the `UNHINGED` entry; add Slightly Weird and Total Fever Dream
  texts) and `rewrite_story(transcript, absurdity=Absurdity.UNHINGED)` that
  sends `REWRITE_PROMPTS[absurdity]` as the first `contents` element.
- Run `pytest tests/test_services.py` until green.

## Group 4 — Route (`app.py`) — TDD

- Update `tests/test_app.py`:
  - Rewrite POST with `{"transcript": "...", "absurdity": "total_fever_dream"}`
    → `200` and the story persisted with that level
    (monkeypatch `services.rewrite_story` and check the returned enum / the row).
  - Rewrite POST without `absurdity` → `200` and the `UNHINGED` default used.
  - Rewrite POST with an unknown token (e.g. `"chaotic"`) →
    `400` with error code `invalid_absurdity` and the allowed tokens in the
    message.
  - Existing `missing_transcript` / `no_transcript` / success tests stay green.
- Run `pytest tests/test_app.py`, watch the new tests fail (red).
- Implement in `app.py`:
  - In the rewrite handler, read optional `absurdity`; if absent default to
    `Absurdity.UNHINGED`; if present parse via `Absurdity.from_token` and return
    the structured `400 invalid_absurdity` on `ValueError`.
  - Pass the enum to `services.rewrite_story`, and
    `db.save_story(transcript_id, story, absurdity=absurdity.value)`.
- Run `pytest tests/test_app.py` until green.

## Group 5 — Frontend (`frontend/static/`) — TDD

- Update/extend the `node:test` suite (`frontend/tests/rewrite-body.test.js`):
  - `buildRewriteBody(transcript)` (no level) → `{"transcript": ...}` (backward
    compatible).
  - `buildRewriteBody(transcript, "total_fever_dream")` → body includes
    `"absurdity": "total_fever_dream"`.
  - A helper that maps the selected toggle to its token (e.g.
    `absurdityToken(checked)` or reading `data-token`) is covered.
- Run `npm test --prefix frontend`, watch the new tests fail (red).
- Implement in `index.html`/`app.js`/`style.css`:
  - Add the three-button segmented toggle (default Unhinged), styled to match
    the kitsch brand.
  - Keep the latest transcript in a variable; `buildRewriteBody` now includes
    the selected level; on toggle change, if a transcript exists, re-run
    `rewriteStory(transcript)` in place (which already re-narrates).
- Run `npm test --prefix frontend` and `npm run lint --prefix frontend` until
  green.

## Group 6 — Quality gate, live verification, spec sync

- Run and fix until green:
  - `ruff check .` and `ruff format --check .`
  - `mypy .` (strict)
  - `pytest`
  - `npm run lint --prefix frontend` and `npm test --prefix frontend`
  - `pre-commit run --all-files`
- Start the server (`setsid nohup python app.py &`, bound to `0.0.0.0:3000`),
  verify through the Codio public URL (per AGENTS.md: announce it, curl it):
  - `curl -X POST -H "Content-Type: application/json" \
    -d '{"transcript":"I burnt the toast.","absurdity":"slightly_weird"}' \
    http://localhost:3000/api/rewrite` → `200`, visibly *blander* story than the
    default.
  - Repeat with `"unhinged"` and `"total_fever_dream"` → `200`, each noticeably
    more chaotic; the loudest level reads like a fever dream.
  - `-d '{"transcript":"x","absurdity":"chaotic"}'` → `400 invalid_absurdity`.
  - Confirm the persisted `stories.absurdity` values in SQLite (old rows show
    `unhinged`).
  - UI: record → transcript appears → story generates at Unhinged → flip to
    Total Fever Dream → a new, more absurd story replaces it and its narration
    plays.
- Spec sync: update this `validation.md` and ROADMAP's stretch-feature entry
  (approved deviations, implementation notes, merge record).