# Getting started with the Stitch skill's MCP servers

This skill depends on two MCP servers already declared in
`plugins/engineer/.mcp.json`: `stitch`, and `playwright`.
If a tool call fails with "server not found" or an auth error, check:

## stitch

- Remote HTTP server: `https://stitch.googleapis.com/mcp`.
- Requires `STITCH_API_KEY` set in the environment before the CLI
  starts (referenced as `${STITCH_API_KEY}` in `.mcp.json`).
- No local install needed; connectivity to `googleapis.com` is required.

## playwright

- Local server launched via `npx -y @playwright/mcp@latest`.
- Requires Node.js/npm on PATH and outbound network access the first
  time, to fetch the package (and browser binaries on first navigate).
- If browser launch fails with a missing-browser error, run
  `npx playwright install` once in the environment running the CLI.

## Verifying the servers are wired up

```bash
copilot plugin install ./plugins/engineer
```

Then in an interactive session, run `/mcp list` (or equivalent) to
confirm `stitch`, and `playwright` show as connected before
invoking this skill.

## If `stitch` tools don't appear at all

This isn't the same as an auth error — it means the CLI session never
loaded the server. Observed cause: `.mcp.json` or `STITCH_API_KEY` was
added/changed *after* the current session started. MCP servers are
read at session/plugin-install time, so:

1. Confirm `STITCH_API_KEY` is actually exported in the shell the CLI
   launches from (`echo $STITCH_API_KEY`), not just written to a
   dotfile in a *different* still-open shell.
2. Re-run `copilot plugin install ./plugins/engineer` and start a
   fresh CLI session — don't keep debugging inside the session that
   predates the config change.
