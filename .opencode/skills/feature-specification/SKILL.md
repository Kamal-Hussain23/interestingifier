---
name: feature-specification
description: >-
  Use when the user requests a new feature or the next natural step from
  SPECS/ROADMAP.md needs a feature specification. Read the project constitution
  in SPECS/, then create a dated feature-spec folder under SPECS/ with
  requirements.md, plan.md, and validation.md.
---

Read the files in SPECS/, these are the project's constitution. Then create a feature specification for the feature requested by the user or, if no feature is mentioned, for the most natural next step according to the ROADMAP.md file. Make a branch, ask me about the feature spec.

Create:

- A new directory `YYYY-MM-DD-feature-name` under SPECS/ for this feature work
- In there:
    * plan.md as a series of numbered task groups (remind yourself that if you need to run checks such as linting, tests, etc.)
    * requirements.md for the scope, decisions, context
    * validation.md for how to know that the validation succeeded and can be merged

## Requirements

* All features must include comprehensive logging, privileging decorator-type designs to avoid mixing business logic with logging logic.
* Privilege proper schemas, contracts and models as much as possible over relying on regexes
* Do not assume backward compatibility should be kept, as that could cause legacy code to be kept unnecessarily; ask user in each specific instance where a decision must be made about backward compatibility
* Privilege solutions that are simple, elegant and general; complexity and arbitrariness should be minimised. Feel free to propose the user ways to make the specification simpler and more elegant
* Simple SQLite persistence. The students know basic SQLite and the app is expected to persist data, so features may store data on disk via SQLite. Use only straightforward, beginner-friendly patterns — a simple schema and plain queries. Do not introduce ORMs, migrations, or advanced database tooling the students have not learned.

## Planning strategy

This is a Red/Green TDD repo, so tests must be created *before* feature code and tested against it until they pass.

## Validation

The validation step also includes surfacing differences between what was implemented and the specs in SPECS/ and the feature specs, and updating the specs upon user's approval.

## Important

* You *must* ask the user for clarifications before writing to disk.