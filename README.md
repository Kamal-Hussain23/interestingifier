# Interestingifier™

**Take boring. Make it interesting.**

Interestingifier™ is a web app that turns dull, everyday anecdotes into hilarious, over-the-top theatrical stories — and narrates them aloud in an energetic Aussie accent. You say your story out loud; Interestingifier gives you back an absurd retelling, told with joyful drama.

## How it works

1. **Record** your boring anecdote in the browser.
2. **Transcribe** — the backend turns your audio into text using Gemini Speech-to-Text.
3. **Transformation** — Gemini rewrites the text into an over-the-top story.
4. **Narrate** — Gemini Text-to-Speech reads the story aloud in the browser.

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | Vanilla HTML, CSS, and JavaScript |
| Backend | Python 3.11 + Flask |
| Database | SQLite (simple persistence, no ORM) |
| AI | Google Gemini API (speech-to-text, text generation, text-to-speech) |

## Project structure

```
├── app.py                  # Flask app — routes and endpoints
├── config.py               # Environment / secret management
├── db.py                   # SQLite database helpers
├── models.py               # Data classes for requests and responses
├── services.py             # Gemini API integration (transcribe, rewrite, narrate)
├── logging_config.py       # Structured logging setup
├── requirements.txt        # Python dependencies
├── setup.sh                # One-command project setup
├── pyproject.toml          # Ruff, mypy, and pytest config
├── frontend/
│   ├── static/
│   │   ├── index.html      # Main page
│   │   ├── style.css       # Kitsch aesthetic styling
│   │   └── app.js          # Browser-side recording and API calls
│   └── tests/              # Frontend JavaScript tests
├── tests/                  # Python backend tests
└── SPECS/                  # Project constitution and feature specs
```

## Getting started

### 1. Run the setup script

```bash
bash setup.sh
```

This installs the Python backend dependencies and Node 20 (needed by the frontend lint/test tooling).

### 2. Set your Gemini API key

```bash
export GEMINI_API_KEY="your-api-key-here"
```

### 3. Start the server

```bash
python app.py
```

The server runs on port 3000. In Codio, open the public URL printed in the terminal.

## Running tests

### Backend

```bash
pytest
```

### Frontend

```bash
cd frontend && npm test
```

## Code quality

Pre-commit hooks run automatically on every commit:

- **Ruff** — Python linting and formatting
- **mypy** — Static type checking
- **pytest** — Python tests
- **ESLint** — JavaScript linting

Configuration lives in `pyproject.toml` (Python) and `frontend/eslint.config.js` (JS).

## The constitution

Read these files before writing any code — they are the project's governance:

- `SPECS/MISSION.md` — the project's purpose, values, and non-negotiables
- `SPECS/TECH.md` — the technology stack and engineering standards
- `SPECS/ROADMAP.md` — current state, next steps, and long-term vision

Feature work lives in dated spec folders under `SPECS/` (each with `requirements.md`, `plan.md`, and `validation.md`).
