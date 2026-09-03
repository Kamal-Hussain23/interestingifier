# TECH.md

## Technology stack

- **Frontend:** Plain HTML5, custom CSS (styled with eccentric-kitsch flair), and Vanilla JavaScript.
- **Audio capture & playback:** Native browser APIs — `MediaRecorder` to record from the microphone and `AudioContext` to play audio back.
- **Backend:** A lightweight Python server (Flask or FastAPI) that manages endpoints, validates and handles `multipart/form-data` uploads, and coordinates AI requests.
- **Persistence:** A simple SQLite database (`interestingifier.db`) storing raw transcripts, rewritten stories, and metadata.
- **AI:** The Python backend orchestrates three [Gemini API](https://ai.google.dev/gemini-api/docs/models) capabilities:
  1. Speech-to-Text (transcribe the anecdote)
  2. Generative Text (rewrite it as an absurd story)
  3. Text-to-Speech (narrate the story aloud)

All external API calls flow strictly through backend endpoints — never from the browser — so API keys stay safe and payloads stay consistent.

## Codio box notes

The project runs inside a Codio box, which has a few quirks worth remembering:

- **Old Node by default.** The box ships Node 12, but the frontend tooling (ESLint 9, `node:test`) requires Node 18+. `setup.sh` installs **Node 20 LTS via nvm** and symlinks `node`, `npm`, and `npx` into `~/bin` (already on PATH), so every shell — including the non-interactive pre-commit hooks — resolves the modern Node. Run `bash setup.sh` after cloning, before relying on the frontend hooks.
- **Public URL.** A server must bind to `0.0.0.0` on a port in 1024–9499 (default 3000) to be reachable at `https://${CODIO_HOSTNAME}-3000.codio.io/`. Full rules live in `AGENTS.md`.
- **Long-running servers.** When starting the server by hand, launch it detached (`setsid nohup python app.py &`) so it keeps running after the terminal session ends; the box may 502 on the public URL while the server is down.

## Engineering standards

- **Red/Green TDD.** Write a failing test first, watch it fail (red), then write the minimal code to make it pass (green), and refactor as needed.
- **Spec-driven development.** All work starts from a written specification (requirements / plan / validation). Code must trace back to an approved spec.
- **Strict typing.** Strict type checking is on (`mypy --strict`). Type-safety is not traded away for convenience.
- **Contracts and strict models over custom logic.** Prefer explicit schemas, contracts, and typed models over ad-hoc parsing, regexes, or stringly-typed code.
- **DRY.** Don't repeat yourself — extract shared logic at the right seams instead of copying code.
- **Decoupled logging.** Log comprehensively via decorators (or similar), keeping the logging separate from the business logic.
- **Simplicity over complexity.** Prefer solutions that are simple, elegant, and general. Minimise arbitrarieness.

## Conventions

- Line length 100; code formatted with Ruff, double-quoted strings, space indentation.
- A pre-commit hook runs: gitleaks (secrets), Ruff (lint + format), mypy (types), pytest, and frontend lint/tests.
- The Verifier agent independently audits work against its spec before it is considered done.
- The repository is a **brownfield** codebase: students extend an existing, near-production-ready scaffold and respect its established patterns rather than rewriting them.