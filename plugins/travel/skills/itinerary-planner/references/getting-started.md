# Getting started: `flights` MCP server

This skill queries flight options through the `flights` MCP server,
configured in `plugins/travel/.mcp.json` as:

~~~json
{
  "mcpServers": {
    "flights": {
      "type": "local",
      "command": "uv",
      "args": ["run", "--with", "flights[mcp]", "fli-mcp"],
      "env": {},
      "tools": ["*"]
    }
  }
}
~~~

## Install `uv`

If `uv` isn't already installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

See https://docs.astral.sh/uv/getting-started/installation/ for other
platforms.

## Verify

```bash
uv run --with "flights[mcp]" fli-mcp --help
```

`uv` will fetch the `flights` package and its `mcp` extra on first run, so
the first invocation may take longer while dependencies resolve.
