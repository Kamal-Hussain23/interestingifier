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

## Implementation record (2026-09-08)

Implemented on branch `feature/2026-09-08-more-drama` (PR #9) via the TDD
groups in plan.md, all Red-first:

- **G1 service** — `DRAMA_TWISTS` (6 kitsch twist phrases), injectable
  `pick_drama_twist(pick=random.choice)`, and `rewrite_story(transcript,
  absurdity, twist=None)` that injects the twist between the level prompt and
  the transcript. No-twist calls stay `[prompt, transcript]`.
- **G2 API** — lenient `parse_drama_flag(data)` (`True`/`"true"` → `True`,
  absent/False/junk → `False`) and `rewrite()` sends
  `twist=pick_drama_twist()` when drama is flagged, else `twist=None`. Each
  re-roll persists as a brand-new `stories` row on the same transcript.
- **G3 frontend pure** — `buildRewriteBody(transcript, absurdity, drama=false)`
  appends `"drama": true` only when requested; legacy bodies byte-identical.
- **G4 browser** — `#more-drama-btn` in the story panel (disabled until a
  transcript lands, enabled in `uploadForTranscription`), click handler calls
  `rewriteStory(currentTranscript, true)`; kitsch `:disabled`-aware styles.
- **G5 gate + live** — `ruff`, `ruff format`, `mypy`, `pytest` (70),
  `npm test` (17), `npm run lint`, and `pre-commit run --all-files` all green.

Live verification through the Codio public URL: a plain rewrite and two
consecutive `"drama": true` re-rolls on the same anecdote returned three
distinct stories; `interestingifier.db` gained three rows sharing one
`transcript_id` (17 plain, 18 + 19 twist spins) — nothing overwritten.

Notes/deviations: existing `test_app.py` rewrite fakes were updated to accept
`twist=None`, because the route now always passes the `twist=` keyword
(a no-flag request sends `twist=None`). No material deviation from this spec.

## Out of scope (must NOT be present)

- No new endpoint, response-contract, schema, or model-field changes.
- No absurdity escalation ladder (re-roll stays at the user's selected level).
- No history UI work and no overwrite/delete of existing story rows.
- No new library, framework, or DB tooling.