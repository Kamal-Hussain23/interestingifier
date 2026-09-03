# Persistence is real — Plan

Date: 2026-08-14
Feature: SPECS/2026-08-14-persistence-is-real/requirements.md

TDD note: in every group, write the failing test first (red), watch it fail, then
write the minimal code to make it pass (green). At the end of each group, run the
focused pytest file for that group; run the full quality gate in group 4.

## Group 1 — Row dataclasses (`models.py`) — TDD

- Write tests first (extend `tests/test_models.py`):
  - `asdict(Transcript(id=1, raw_text="I missed the bus.", created_at="2026-08-14 10:00:00"))`
    equals the same dict (shape check).
  - `asdict(Story(id=1, transcript_id=2, story_text="THE BUS FEARED HIM.", created_at="2026-08-14 10:00:00"))`
    equals the same dict (shape check).
- Run `pytest tests/test_models.py` and watch the new tests fail (red).
- Implement: add the two frozen dataclasses to `models.py`.
- Run `pytest tests/test_models.py` until green.

## Group 2 — Save and fetch transcripts (`db.py`) — TDD

- Write tests first (extend `tests/test_db.py`; use `tmp_path` for a temp db):
  - `save_transcript("...")` returns a `Transcript` whose `raw_text` matches and
    whose `id` and `created_at` are non-empty (populated by the DB).
  - `fetch_transcript(id)` returns the transcript saved just before.
  - `fetch_transcript(999999)` (missing) returns `None`.
  - `save_transcript` stores the text so a fresh connection sees it (round-trip
    through a second `get_connection`).
- Run `pytest tests/test_db.py` and watch the new tests fail (red).
- Implement in `db.py`:
  - Set `connection.row_factory = sqlite3.Row` inside `get_connection` so
    `row["raw_text"]` style access works.
  - `save_transcript`: open a connection, `INSERT INTO transcripts (raw_text)
    VALUES (?)`, commit, capture `cursor.lastrowid`, then `SELECT` that row back
    (to pick up the DB-assigned `created_at`) and build a `Transcript`.
  - `fetch_transcript`: `SELECT id, raw_text, created_at FROM transcripts
    WHERE id = ?`, return `None` if no row, else build a `Transcript`.
  - Decorate both with `@logged`.
- Run `pytest tests/test_db.py` until green.

## Group 3 — Save and fetch stories + history (`db.py`) — TDD

- Write tests first (extend `tests/test_db.py`; each test that needs a transcript
  saves one first with `save_transcript`):
  - `save_story(transcript_id, "...")` returns a `Story` whose `story_text` and
    `transcript_id` match and whose `id`/`created_at` are populated.
  - `fetch_story(id)` returns the story saved just before.
  - `fetch_story(999999)` (missing) returns `None`.
  - `save_story` with a non-existent `transcript_id` raises
    `sqlite3.IntegrityError` (the schema's foreign key).
  - `list_stories()` returns `[]` for a fresh DB with no stories.
  - Save two transcripts/stories; `list_stories()` returns both, newest first
    (the most recently saved story is `stories[0]`).
- Run `pytest tests/test_db.py` and watch the new tests fail (red).
- Implement in `db.py`:
  - `save_story`: `INSERT INTO stories (transcript_id, story_text) VALUES (?, ?)`,
    commit, capture `lastrowid`, `SELECT` the row back, build a `Story`.
  - `fetch_story`: `SELECT id, transcript_id, story_text, created_at FROM
    stories WHERE id = ?`, `None` if missing, else a `Story`.
  - `list_stories`: `SELECT ... FROM stories ORDER BY id DESC`, build one
    `Story` per row, return as a `list[Story]`.
  - Decorate all three with `@logged`.
- Run `pytest tests/test_db.py` until green.

## Group 4 — Quality gate and manual verification

- Run and fix until green:
  - `ruff check .` and `ruff format --check .`
  - `mypy .` (strict)
  - `pytest`
  - `npm run lint --prefix frontend` and `npm test --prefix frontend`
    (frontend untouched, must stay green)
  - `pre-commit run --all-files`
- Start the server (`python app.py`, bound to `0.0.0.0:3000`) and verify through
  the Codio public URL (per AGENTS.md: announce the URL, curl it to confirm):
  - The app boots and `/` serves the frontend.
  - `curl http://localhost:3000/api/health` → `200` `{"status": "ok"}`.
  - The `interestingifier.db` file is created at startup (schema init already
    existed; confirm it still happens).
- Confirm the persistence functions work against a real file via a tiny REPL
  check against a throwaway db path:
  - `save_transcript` + `save_story` + `list_stories` round-trip returns the
    saved story with its `id`, `transcript_id`, and `created_at` populated.
- Leave the endpoints returning 501 (no wiring this step): a quick
  `curl -X POST -H "Content-Type: application/json" -d '{"transcript":"hi"}'
  http://localhost:3000/api/rewrite` still returns `501 not_implemented`.