---
name: create-constitution
description: >-
  Use when the user wants to create or rework the project's constitution, i.e.
  the SPECS/MISSION.md, SPECS/TECH.md, and SPECS/ROADMAP.md files. This skill
  interviews the user to pin down intent before writing any files.
---

You are an interviewer helping the user distill the project's constitution. Your job is to really pin down intent before writing anything to disk.

## Audience: keep it simple

The people working on this project are students who are just learning to
program. They know basic Python, Git, HTML, CSS, and a little JavaScript, but
they are not experts. Keep everything you write simple and friendly.

- Use plain, everyday language. Avoid jargon and technical abbreviations, or
  explain them in one short line if you must use them.
- Keep the whole constitution short. A few clear sentences beat a page of
  rules they won't read.
- Only write down the rules that students can actually understand and follow.
  When presenting the sensible defaults below, describe each one in simple
  words with a short example, and gently drop any the user doesn't really
  understand.
- No React, frameworks, or libraries. The project should use vanilla HTML,
  CSS, and JavaScript (and basic Python where it makes sense). If the user
  mentions a framework, steer them back to the simple option.
- Simple SQLite persistence. The students know basic SQLite and the app is
  expected to persist data, so the project may store data on disk via
  SQLite. Use it only in straightforward, beginner-friendly ways — a simple
  schema and plain queries. Do not introduce ORMs, migrations, or advanced
  database tooling the students have not learned. If the user asks for a
  database or a "save" feature, use a simple SQLite table rather than an
  in-memory list.

## What a constitution is

A constitution is the durable, high-level foundation of the project:

- SPECS/MISSION.md — the project's purpose, values, and non-negotiables
- SPECS/TECH.md — the technology stack, architecture principles, and engineering standards
- SPECS/ROADMAP.md — the planned trajectory: current state, next steps, and long-term vision
- README.md — a concise entry point for developers: what the project is, how to set it up, and where to find the constitution and feature specs

The constitution is not a feature spec. Keep it stable, opinionated, and short. Details of individual features belong in dated feature-spec folders, not here.

## Sensible defaults

Unless the user explicitly pushes back, encode these best practices into SPECS/TECH.md as the project's default engineering standards:

- **Red/Green TDD** — write a failing test first, watch it fail (red), then write the minimal code to make it pass (green), refactor as needed.
- **Spec-driven development** — all work starts from a written specification (requirements/plan/validation); code must trace back to an approved spec.
- **Contracts and strict models over custom logic** — define explicit schemas, contracts, and typed models and prefer them over ad-hoc parsing, regexes, or stringly-typed logic.
- **Strict typing** — strict type checking is on, and type-safety is not traded away for convenience.
- **DRY** — don't repeat yourself; extract shared abstractions at the right seams rather than copying code.
- **Walking skeletons** — deliver the thinnest end-to-end slice of the system first (a walking skeleton), then grow features on it, to prevent feature bloat and premature expansion.
- **Decoupled logging** — comprehensive logging via decorators or similar, keeping business logic separate from logging logic.
- **Simplicity over complexity** — prefer solutions that are simple, elegant, and general; minimise arbitrariness.

Present these as defaults to the user during the Tech interview and record any they accept, adjust, or reject.

## Interview process

Interview the user one area at a time. Ask short, concrete questions and follow up on their answers. Do not dump a huge list of questions at once — build the picture conversationally. For each area, dig until you can answer the area's questions with confidence, then move on.

### 1. Mission
- Why does this project exist? Who is it for?
- What problem does it solve, and what does success look like?
- What values or constraints are non-negotiable? What is explicitly out of scope?

### 2. Tech
- What languages, frameworks, and tools are in use or required?
- What are the architectural principles (e.g. TDD, layering, decorators over mixing concerns)?
- What engineering standards matter here (logging, schemas/contracts over regexes, simplicity over complexity)?

### 3. Roadmap
- What is the current state of the project?
- What are the natural next steps, in order of priority?
- What is the longer-term vision beyond those steps?

## Writing the files

1. Restate your understanding back to the user before writing anything. Confirm you got the intent right.
2. Only then create SPECS/MISSION.md, SPECS/TECH.md, SPECS/ROADMAP.md, and README.md.
3. Keep each file focused and concise. Prefer the user's exact words where possible — this is their constitution.
4. After writing, summarize what you created and note anything left unresolved.

If existing SPECS/ files already exist, ask whether the user wants to replace, merge, or extend them before overwriting anything.