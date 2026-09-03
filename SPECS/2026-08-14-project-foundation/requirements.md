# Project Foundation — Requirements

Date: 2026-08-14
Source: ROADMAP.md, Cycle 1, Step 1 (Project foundation)

## Feature summary

Establish the repository layout and a minimal, runnable Flask skeleton with an
empty SQLite schema. This is the first brick of the scaffold that students will
inherit and grow into a complete, production-ready app.

## Scope — in

- Repo layout: `app.py` and `db.py` at the repo root, frontend assets under
  `frontend/`, tests under `tests/`, and a `requirements.txt`.
- Empty-SQLite schema defined in `db.py` (tables: `transcripts`, `stories`,
  `metadata`) plus a database init that runs on startup.
- Minimal Flask app with two routes:
  - `GET /` — serves the frontend placeholder page.
  - `GET /api/health` — a JSON health-check stub.
- Server binds to `0.0.0.0` on port `3000` and announces the Codio public URL.
- A decoupled, decorator-based logging helper (business logic stays clean).
- A minimal `frontend/package.json` with `lint` and `test` scripts so the
  pre-commit hooks pass.
- Tests written first (Red/Green TDD) for the DB init and the app boot.

## Scope — out (later steps / later specs)

- The kitsch-styled UI (ROADMAP Step 2).
- Gemini service helpers and the pipeline endpoints — transcribe, rewrite,
  narrate (ROADMAP Step 3).
- Real save/fetch persistence functions (ROADMAP Step 4).
- Any Gemini API calls or API-key handling.

## Decisions

- **Framework: Flask.** Simplest fit for students; matches "simple over clever".
- **Minimal stubs now.** Only `/` and `/api/health` are added in this step. The
  Gemini-facing endpoints are intentionally left for the Step 3 spec so each
  spec stays small and reviewable.
- **Frontend layout.** Assets live in `frontend/static/` (`index.html`,
  `style.css`, `app.js`). Flask serves that folder via `static_folder`. The
  `frontend/` directory is also the npm root, which satisfies the existing
  pre-commit hooks (`npm run lint --prefix frontend`, `npm test --prefix
  frontend`).
- **Frontend tooling is deferred.** `package.json` ships with no-op `lint` and
  `test` scripts (exit 0) just so pre-commit stays green. The real frontend
  lint/test tooling is decided in the Step 2 spec.
- **DB location.** SQLite file `interestingifier.db` at the repo root; tables
  created on startup if they do not exist. Simple, beginner-friendly schema and
  plain queries — no ORM, no migrations.
- **Requirements.** `requirements.txt` lists runtime deps (Flask) plus `pytest`
  so tests run both via pre-commit and directly.
- **Repository hygiene.** A minimal `.gitignore` keeps generated files out of
  the repo: `__pycache__/`, `*.py[cod]`, `*.db`, `.venv/`, `node_modules/`.
- **pytest import path.** `pyproject.toml` sets `pythonpath = ["."]` so the
  plain `pytest` command (as run by the pre-commit hook) can import `app`,
  `db`, and `logging_config`.
- **Mypy via system Python.** The pre-commit mypy hook runs the installed mypy
  (`language: system`, `mypy --ignore-missing-imports .`). The previously
  pinned `mirrors-mypy` env has no Flask installed, so `app.route` was typed as
  `Any` and strict mypy reported "untyped decorator" errors on the route
  handlers; the system mypy (2.3.0) resolves this.
- **Backward compatibility.** Not applicable — this is a greenfield foundation
  with no legacy code yet.

## Context

The roadmap is split into two cycles: we build the scaffold (Cycle 1), then
students add the three core features on top (Cycle 2). Everything downstream —
recording, transcription, rewriting, narration, persistence — builds on the
layout, the DB schema, and the routing established here. Getting the seams right
now (Flask, `db.py`, logging helper) is what lets later steps stay "just fill in
the Gemini call + save the result".