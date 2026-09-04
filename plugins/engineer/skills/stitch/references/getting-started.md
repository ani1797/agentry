# Getting started with the Stitch skill's MCP servers

This skill depends on three MCP servers already declared in
`plugins/engineer/.mcp.json`: `stitch`, `context7`, and `playwright`.
If a tool call fails with "server not found" or an auth error, check:

## stitch

- Remote HTTP server: `https://stitch.googleapis.com/mcp`.
- Requires `STITCH_API_KEY` set in the environment before the CLI
  starts (referenced as `${STITCH_API_KEY}` in `.mcp.json`).
- No local install needed; connectivity to `googleapis.com` is required.

## context7

- Remote HTTP server: `https://mcp.context7.com/mcp`.
- Requires `CONTEXT7_API_KEY` in the environment
  (`${CONTEXT7_API_KEY}` in `.mcp.json`). Get a free key at
  https://context7.com/dashboard.

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
confirm `stitch`, `context7`, and `playwright` show as connected before
invoking this skill.
