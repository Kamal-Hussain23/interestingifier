# Interestingifier™

**Take boring. Make it interesting.**

Interestingifier™ is a web app that turns dull, everyday anecdotes into hilarious, over-the-top theatrical stories — and narrates them aloud in an energetic Aussie accent. You say your story out loud; Interestingifier gives you back an absurd retelling, told with joyful drama.

Built for students who are just learning to program: vanilla HTML, CSS, and JavaScript on the frontend, a lightweight Python backend, and simple SQLite persistence.

## How it works

1. **Record** your boring anecdote in the browser.
2. **Transcribe** — the backend turns your audio into text using Gemini Speech-to-Text.
3. **Transformation** — Gemini rewrites the text into an over-the-top story.
4. **Narrate** — Gemini Text-to-Speech reads the story aloud in the browser.

## Setup

```bash
bash setup.sh
```

This installs the backend dependencies and Node 20 (needed by the frontend lint/test tooling). The project runs inside a Codio box; start the server and open it through the box's public URL (see `AGENTS.md`).

## The constitution

Read these files before writing any code. They are the project's governance:

- `SPECS/MISSION.md` — the project's purpose, values, and non-negotiables
- `SPECS/TECH.md` — the technology stack and engineering standards
- `SPECS/ROADMAP.md` — current state, next steps, and long-term vision

Feature work lives in dated spec folders under `SPECS/` (each with `requirements.md`, `plan.md`, and `validation.md`), created via the `feature-specification` skill.

## Working with OpenCode

- `/read-constitution` — read the constitution and stand by (your first move each session).
- Agents: `spec-implementer` builds features, `verifier` audits them, `pr-reviewer` reviews PRs.
- Skills: `create-constitution`, `feature-specification`, `serve-website`.

Pre-commit hooks (gitleaks, Ruff, mypy, pytest, frontend lint/tests) run automatically. The project's coding standards are defined in `pyproject.toml`.