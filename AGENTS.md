# Audience

The people working in this repo are students who are just learning to program.
Keep the tone and language simple and friendly. Always explain things in the
simplest terms possible.

They know basic Python, Git, HTML, CSS, a little bit of JavaScript, and basic
SQLite, but they are not experts on syntax or obscure technical quirks.

- Use only vanilla HTML, CSS, and JavaScript (and basic Python where it makes
  sense). Do not use React or any other framework or library — they have only
  heard of vanilla JS.
- Write small, easy-to-read code. Prefer the most obvious solution over clever
  or "professional" tricks.
- When explaining anything, start from what they already know and build up
  slowly. Don't assume they know jargon, abbreviations, or how tools work
  behind the scenes.
- Simple SQLite persistence is fine. The students know basic SQLite and the app
  is expected to store data, so features may persist to disk via SQLite. Use
  only straightforward, beginner-friendly patterns — a simple schema and plain
  queries. Do not introduce ORMs, migrations, or advanced database tooling the
  students have not learned.

# Codio Environment

This project runs inside a Codio box. Every box has a public URL that can be used
to view a running server from any browser — including a browser that is not in
the Codio IDE.

## Public URL

Two environment variables are always set by Codio:

- `CODIO_HOSTNAME` — the box's two-word subdomain prefix (e.g. `navyfinal-eternalbrain`)
- `CODIO_BOX_DOMAIN` — the full public domain, `<hostname>.codio.io`

The public URL for a server listening on `<PORT>` is always:

```
https://${CODIO_HOSTNAME}-${PORT}.codio.io/
```

## Rules when running a server

- **Bind to `0.0.0.0`, never `127.0.0.1`** — a server bound to localhost cannot
  be reached through the public URL.
- Use a port in the range **1024–9499** for HTTP and **9500–9999** for HTTPS.
- Preferred defaults: port `3000` and `https://${CODIO_HOSTNAME}-3000.codio.io/`.
- To build the URL in code: `f"https://{os.environ['CODIO_HOSTNAME']}-{PORT}.codio.io/"`
  (fall back to `http://localhost:PORT/` when `CODIO_HOSTNAME` is unset, so code
  still works outside Codio).

## Always announce the URL

Whenever you start or restart a web server in this project, you MUST do all of
the following before telling the user the site is ready:

1. Print the full public URL, e.g. `Your site is live at https://navyfinal-eternalbrain-3000.codio.io/`.
2. Verify the public URL responds before announcing it (e.g. a `curl` request
   against `http://localhost:PORT/` and/or `https://${CODIO_HOSTNAME}-${PORT}.codio.io/`).
3. Do not ask the student to look up anything in the Codio UI (no "Box Info",
   no port configuration steps). The student should only have to open the URL.