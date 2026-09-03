# Persistence is real — Requirements

Date: 2026-08-14
Source: ROADMAP.md, Cycle 1, Step 4 (Persistence is real)

## Feature summary

The SQLite schema already exists (`db.py`'s `init_db` creates `transcripts`,
`stories`, and `metadata`), and the app boots and initialises it. This step
makes persistence actually *usable*: add small, tested functions to save and
fetch transcripts and stories, plus a history helper to list saved stories.

This is the storage layer Cycle 2 will call. The Gemini endpoints stay stubbed
(they still return 501), and nothing in this step is wired into a request flow —
the functions exist, are proven by tests, and are ready for Cycle 2's pipeline.
Backend-only; `frontend/` and `app.py` routes are untouched.

## Scope — in

- **`models.py`** — two new frozen dataclasses representing a stored row:
  - `Transcript(id: int, raw_text: str, created_at: str)` — a row from the
    `transcripts` table.
  - `Story(id: int, transcript_id: int, story_text: str, created_at: str)` — a
    row from the `stories` table.
  - `created_at` is stored by SQLite as a string (`datetime('now')`), so the
    dataclass field is a plain `str` — no datetime parsing needed. These live
    in `models.py` next to the API contracts, keeping every typed shape in one
    place (TECH.md: "contracts and strict models over custom logic").
- **`db.py`** — new functions, each accepting an optional `db_path` (defaulting
  to `DB_PATH`) so tests can use a temp file, and each decorated with `@logged`
  so logging stays out of business logic:
  - `save_transcript(raw_text: str, db_path: Path = DB_PATH) -> Transcript` —
    insert a transcript and return the stored row, including its auto-assigned
    `id` and `created_at`.
  - `fetch_transcript(transcript_id: int, db_path: Path = DB_PATH) -> Transcript | None` —
    return the transcript with that id, or `None` if it does not exist.
  - `save_story(transcript_id: int, story_text: str, db_path: Path = DB_PATH) -> Story` —
    insert a story linked to an existing transcript and return the stored row.
  - `fetch_story(story_id: int, db_path: Path = DB_PATH) -> Story | None` —
    return the story with that id, or `None` if it does not exist.
  - `list_stories(db_path: Path = DB_PATH) -> list[Story]` — return every saved
    story, newest first (ordered by `id` descending), ready to feed the
    frontend's history area later.
- **`db.py` internals** — change `get_connection` to set
  `connection.row_factory = sqlite3.Row` so rows expose columns by name
  (`row["raw_text"]`). This is a small, beginner-friendly convenience and stays
  backward compatible: integer indexing (`row[0]`) keeps working, so the
  existing `test_db.py` schema tests are unaffected.
- **`tests/test_db.py`** — extend with save/fetch tests (see `plan.md`):
  - `save_transcript` returns a `Transcript` whose `raw_text` matches and whose
    `id` and `created_at` are populated.
  - `fetch_transcript` returns the saved transcript; `fetch_transcript` for a
    missing id returns `None`.
  - `save_story` returns a `Story` linked to the transcript; `fetch_story`
    returns it; `fetch_story` for a missing id returns `None`.
  - `save_story` with a non-existent `transcript_id` raises `sqlite3.IntegrityError`
    (the schema's foreign key) rather than silently saving a dangling story.
  - `list_stories` returns `[]` when the DB is empty and returns saved stories
    newest first.
  - A round-trip: save transcript + story, then fetch both and check the
    stored text matches.
- **`tests/test_models.py`** — add shape tests for the two new dataclasses.

## Scope — out (later steps / later specs)

- No changes to `app.py` routes or the Flask app — the pipeline endpoints still
  return 501; nothing here is wired to a request flow.
- No frontend changes (`frontend/` untouched; no history UI).
- No real Gemini calls, no Gemini SDK, no HTTP calls to Google.
- No changes to the schema, no migrations, no new tables, no ORM — the existing
  `init_db` schema is used as-is.
- No `metadata` table usage (it exists for future needs; not exercised here).
- No API-key work (`config.py` is untouched).
- No new logging machinery — the existing `@logged` decorator is reused.

## Decisions

- **Typed dataclasses for rows.** Save/fetch functions return `Transcript` /
  `Story` frozen dataclasses instead of raw tuples or `sqlite3.Row` objects.
  This gives students a named, typed shape to work with (mypy-friendly and
  beginner-readable) and matches TECH.md's "contracts and strict models".
  (User-confirmed.)
- **Include `list_stories()`.** The frontend shell has a history area
  (ROADMAP Step 2), so a tiny "list all stories, newest first" helper rounds
  out the storage layer now; Cycle 2 can wire a history endpoint/UI to it.
  (User-confirmed.)
- **db-layer only, no routes.** Step 4 builds the storage foundation; wiring it
  into the live pipeline (and any history endpoint) is Cycle 2 work, keeping
  each step independently spec-able. (User-confirmed.)
- **Reuse the existing schema.** The tables from Step 1 are exactly right for
  what save/fetch need; no schema change is required for this step.
- **Foreign keys enforced via the schema.** `save_story` trusts the declared
  `REFERENCES transcripts(id)`; SQLite raises `IntegrityError` for a dangling
  `transcript_id`. No custom validation logic needed — simple and general.
- **Row factory by name.** Setting `sqlite3.Row` in `get_connection` lets code
  read `row["raw_text"]` instead of `row[1]`, which is easier for beginners and
  resilient to column reordering. Backward compatible with existing tests.
- **Optional `db_path` parameter.** Following the existing `init_db` /
  `get_connection` pattern (`db_path: Path = DB_PATH`) keeps tests hermetic via
  `tmp_path` and keeps production defaults obvious.
- **`created_at` as a plain string.** No parsing to `datetime`; the schema's
  `datetime('now')` string is carried through as-is. Simple and honest.
- **Backward compatibility.** This step is purely additive to `models.py` and
  `db.py`. `get_connection` gains a row factory (non-breaking; integer indexing
  still works), and no existing function's signature or behaviour changes.
  No compatibility decision required.

## Context

Step 4 delivers the persistence half of the "fill in the Gemini call + save the
result" story that Cycle 2 completes: students will call `save_transcript` /
`save_story` in milestone 2 ("The Vibrant Transformation") and `list_stories`
to show history. By proving these functions with tests now, Cycle 2 can trust
the storage layer and focus on the Gemini calls. Step 5 (end-to-end shell runs)
and Step 6 (quality) build directly on this foundation.

## Status

Implemented and verified 2026-08-14 on branch
`feature/2026-08-14-persistence-is-real`; all automated checks and the manual
verification pass. See `validation.md` for the spec-sync record.