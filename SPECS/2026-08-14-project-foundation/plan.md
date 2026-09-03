# Project Foundation — Plan

Date: 2026-08-14
Feature: SPECS/2026-08-14-project-foundation/requirements.md

TDD note: in every group, write the failing test first (red), then the minimal
code to make it pass (green). At the end of each group, run the full quality
gate listed in group 6.

## Group 1 — Repo layout and tooling

- Create the directory structure:
  - `app.py` (Flask app, repo root)
  - `db.py` (schema + init, repo root)
  - `frontend/static/index.html`, `frontend/static/style.css`,
    `frontend/static/app.js` (empty placeholders — styled in Step 2's spec)
  - `frontend/package.json` with no-op `lint` and `test` scripts (exit 0)
  - `tests/` for pytest
  - `requirements.txt` with `Flask` and `pytest`
- Confirm `pyproject.toml` already covers Ruff (line length 100, double quotes)
  and mypy `--strict`; no changes needed there.

## Group 2 — SQLite schema and init (`db.py`)

- Write tests first:
  - `tests/test_db.py`: after `init_db()`, all three tables exist; a second
    call to `init_db()` is harmless (idempotent).
- Implement `db.py`:
  - A small connection helper that opens `interestingifier.db`.
  - `init_db()` creating the tables if they do not exist:
    - `transcripts(id INTEGER PRIMARY KEY AUTOINCREMENT, raw_text TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now')))`
    - `stories(id INTEGER PRIMARY KEY AUTOINCREMENT, transcript_id INTEGER NOT
      NULL REFERENCES transcripts(id), story_text TEXT NOT NULL, created_at TEXT
      NOT NULL DEFAULT (datetime('now')))`
    - `metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)`

## Group 3 — Flask skeleton (`app.py`)

- Write tests first:
  - `tests/test_app.py`: a smoke test using the Flask test client — `GET /`
    returns 200 with HTML, `GET /api/health` returns 200 with a JSON
    `{"status": "ok"}`.
- Implement `app.py`:
  - Create the Flask app with `static_folder="frontend/static"`.
  - `GET /` serves `index.html` from the frontend.
  - `GET /api/health` returns the health JSON.
  - Call `init_db()` at startup.
  - When run directly, bind to `0.0.0.0:3000` and print the Codio public URL
    (`f"https://{os.environ['CODIO_HOSTNAME']}-3000.codio.io/"`, falling back to
    `http://localhost:3000/` when `CODIO_HOSTNAME` is unset).

## Group 4 — Decoupled logging helper

- Add a small logging module (e.g. `logging_config.py`) providing:
  - Basic logging configuration (console output, sensible format).
  - A `@logged` decorator that logs entry/exit and errors for a function,
    keeping logging out of the business logic.
- Test: a decorated function's call produces log output (capture via caplog).
- Apply the decorator to the Flask route handlers so logging is in place from
  day one.

## Group 5 — Frontend placeholder

- `frontend/static/index.html` is a single, valid HTML page with a title
  ("Interestingifier™") and a bare minimum of markup (full styling arrives in
  Step 2's spec).
- `style.css` and `app.js` exist as minimal, valid files.
- Verify `npm run lint --prefix frontend` and `npm test --prefix frontend`
  both exit 0 (no-op scripts).

## Group 6 — Quality gate and manual verification

- Run and fix until green:
  - `ruff check .` and `ruff format --check .`
  - `mypy .` (strict)
  - `pytest`
  - `pre-commit run --all-files`
- Start the server and verify:
  - `curl http://localhost:3000/` returns the HTML page.
  - `curl http://localhost:3000/api/health` returns the health JSON.
  - `sqlite3 interestingifier.db ".tables"` lists the three tables.
  - The server responds through the Codio public URL (bind to `0.0.0.0`, then
    `curl` the `https://${CODIO_HOSTNAME}-3000.codio.io/` URL).