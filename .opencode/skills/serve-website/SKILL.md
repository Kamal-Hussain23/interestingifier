---
name: serve-website
description: >-
  Use when the user asks to run, serve, start, launch, or preview the website,
  web app, or server ("start the server", "serve it", "run the site", "is it
  running?", "show me the page"). Starts the dynamic server bound to 0.0.0.0,
  verifies it through the Codio public URL, and reports the live URL to the
  user. See AGENTS.md for the Codio environment rules.
---

You are running in a Codio box. Any web server you start must be reachable
through the box's public URL so the user can open it in any browser. Follow the
rules in AGENTS.md (bind `0.0.0.0`, never `127.0.0.1`, allowed port ranges,
build the URL from `CODIO_HOSTNAME`).

## Steps

1. Decide the port. Prefer `3000` unless the user asked for a specific one.
   Confirm the port is in the Codio HTTP range (1024–9499) or HTTPS range
   (9500–9999).

2. Start the server so it binds to **`0.0.0.0`** on that port:
   - If the app already does this, just run it.
   - If not, run it the same way the project convention dictates, but make
     sure the listen address is `0.0.0.0` (e.g. `ThreadingHTTPServer(("0.0.0.0", PORT), ...)`).
   - Run it in the background or via a long-lived command, and keep enough
     context to restart it later.
   - Useful Python snippet for the URL (works outside Codio too):
     ```python
     host = os.environ.get("CODIO_HOSTNAME")
     url = f"https://{host}-{PORT}.codio.io/" if host else f"http://localhost:{PORT}/"
     ```

3. Wait for the server to start listening (check `ss -ltn` or curl in a loop
   with a short sleep) before proceeding.

4. Verify before announcing:
   - `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:PORT/` must return
     a 2xx/3xx, and
   - `curl -s -o /dev/null -w "%{http_code}" "https://OPTIONAL_HOST-PORT.codio.io/"` must succeed.

5. Report to the user the live URL:
   `Your site is live at https://HOSTNAME-PORT.codio.io/`
   - `HOSTNAME` and `PORT` above are **placeholders** — substitute the actual
     Codio hostname (from `CODIO_HOSTNAME`) and the chosen port. Report the
     real, resolved URL, not the template literally.
   - Pasted as a clickable link.
   - With no instructions to use the Codio UI or look up anything.
   - If the page does not load, investigate the port range and whether a
     previous server is still holding the port before telling the user it is up.