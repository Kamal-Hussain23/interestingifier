# The "More Drama!" Re-roll — Validation

Date: 2026-09-08
Feature: SPECS/2026-09-08-more-drama/requirements.md

This step is complete when all of the following pass. The Verifier agent audits
the work against this file before the branch is considered done.

## Automated checks

- `pytest` — complete and green, including the new cases:
  - service: `DRAMA_TWISTS` non-empty; `pick_drama_twist(pick)` deterministic
    with an injected pick; `rewrite_story(…, twist="…")` threads the twist into
    the contents; no-twist calls are byte-for-byte as before.
  - api: `parse_drama_flag` lenient (absent/`false`/junk → `False`,
    `true`/`"true"` → `True`); `drama: true` re-rolls with a picked twist and
    saves a **new** stories row; no flag → unchanged behaviour. All pre-existing
    tests stay green.
- `npm test --prefix frontend` — `buildRewriteBody(transcript, absurdity,
  drama)` covered: `false`/omitted → the exact legacy body; `true` appends
  `"drama": true`; works without an absurdity choice. Pre-existing frontend
  tests stay green.
- `ruff check .`, `ruff format --check .`, `mypy .` — clean; strict typing holds.
- `npm run lint --prefix frontend` — ESLint clean.
- `pre-commit run --all-files` — all hooks green without `GEMINI_API_KEY`.

## TDD evidence

- Red→Green history for at least one test per group in `plan.md`: service
  twists, API drama flag, frontend body builder. The pure helpers
  (`pick_drama_twist`, `parse_drama_flag`, `buildRewriteBody`) are covered by
  tests first; the DOM wiring is manual verification.

## Manual verification

- On load the More Drama! button is disabled; after recording (transcript
  lands) it becomes enabled.
- Three rapid More Drama! clicks produce three *distinctly different* stories
  and re-narrate each one; clicks never need re-recording.
- `interestingifier.db` shows three story rows sharing the one transcript id —
  nothing overwritten.
- `curl -X POST /api/rewrite` with `"drama": true` returns a story rewritten
  with a twist; without the flag the behaviour is unchanged (byte-identical
  response contract).
- The Absurdity Slider path still works exactly as before (the re-roll is
  additive).
- The server answers through the Codio public URL (per AGENTS.md: bind to
  `0.0.0.0`, curl `https://${CODIO_HOSTNAME}-3000.codio.io/`).

## Spec sync

- On merge, update ROADMAP.md to mark "'More Drama!' re-roll" done and record
  any approved deviations + implementation notes here (as the previous features
  did).

## Out of scope (must NOT be present)

- No new endpoint, response-contract, schema, or model-field changes.
- No absurdity escalation ladder (re-roll stays at the user's selected level).
- No history UI work and no overwrite/delete of existing story rows.
- No new library, framework, or DB tooling.