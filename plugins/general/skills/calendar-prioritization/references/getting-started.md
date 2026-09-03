# Getting started

## `uv`

The scorer is a standalone [PEP 723](https://peps.python.org/pep-0723/)
script with no third-party dependencies; `uv` just runs it.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install docs: <https://docs.astral.sh/uv/getting-started/installation/>.
Plain `python3 scripts/prioritize.py` also works (Python 3.11+).

## WorkIQ MCP server

The `general` plugin ships the server in its `.mcp.json`:

```json
{ "mcpServers": { "workiq": { "type": "local", "command": "npx",
  "args": ["-y", "@microsoft/workiq@latest", "mcp"] } } }
```

Requires Node.js and a signed-in Microsoft 365 account with a Copilot
licence. On first use the server prompts for sign-in.

## EULA

Full tool access needs the EULA accepted once, via the `accept_eula`
tool with `https://github.com/microsoft/work-iq`. This **requires
explicit user confirmation** — ask, and never auto-accept it.

If calls fail with an authorization error, re-run sign-in and confirm the
tenant allows the WorkIQ endpoint.
