# Manifest templates and validation

## `plugins/<name>/plugin.json`

```json
{
  "name": "<name>",
  "description": "One concrete sentence: what it does, when to use it.",
  "version": "0.1.0",
  "author": { "name": "Jane Doe", "email": "jane@example.com" },
  "license": "MIT",
  "keywords": ["example"],
  "hooks": "hooks.json",
  "mcpServers": ".mcp.json",
  "lspServers": "lsp.json"
}
```

Only `name` is required (kebab-case, letters/numbers/hyphens, max 64 chars).
Component paths (`agents`, `skills`, `hooks`, `mcpServers`, `lspServers`)
default to `agents/` and `skills/` for `agents`/`skills` — `hooks`,
`mcpServers`, and `lspServers` have no default path, so every plugin wires
all three explicitly to the stub files below.

## `.github/plugin/marketplace.json` entry

```json
{
  "name": "<name>",
  "source": "plugins/<name>",
  "description": "Same description as plugin.json.",
  "version": "0.1.0"
}
```

Keep `description`/`version` identical to `plugin.json` at every commit
that touches either file.

## `plugins/<name>/hooks.json`

Every scaffolded plugin ships this stub — all 14 supported hook events
present as empty arrays, ready to fill in later. Wire it via `plugin.json`'s
`"hooks": "hooks.json"` field.

```json
{
  "version": 1,
  "hooks": {
    "agentStop": [],
    "errorOccurred": [],
    "notification": [],
    "permissionRequest": [],
    "postToolUse": [],
    "postToolUseFailure": [],
    "preCompact": [],
    "preToolUse": [],
    "sessionEnd": [],
    "sessionStart": [],
    "subagentStart": [],
    "subagentStop": [],
    "userPromptSubmitted": [],
    "userPromptTransformed": []
  }
}
```

## `plugins/<name>/.mcp.json`

Every scaffolded plugin also ships this empty stub. Wire it via
`plugin.json`'s `"mcpServers": ".mcp.json"` field.

```json
{
  "mcpServers": {}
}
```

## `plugins/<name>/lsp.json`

Every scaffolded plugin also ships this empty stub, for structural parity
with `hooks.json`/`.mcp.json` — even though `lspServers` has no fixed set
of names to pre-populate (each server key is arbitrary). Note:
`lsp-config/servers.json` appears in the CLI docs only under Open Plugin
Spec (opted into via a `$schema` declaration); plain `plugin.json` plugins
like ours have no default LSP path, so a flat file wired explicitly is
equivalent and matches `hooks.json`/`.mcp.json`. Wire it via `plugin.json`'s
`"lspServers": "lsp.json"` field.

```json
{
  "lspServers": {}
}
```

## Validation

```bash
jq -e . plugins/<name>/plugin.json > /dev/null
jq -e . plugins/<name>/hooks.json > /dev/null
jq -e . plugins/<name>/.mcp.json > /dev/null
jq -e . plugins/<name>/lsp.json > /dev/null
jq -e . .github/plugin/marketplace.json > /dev/null
jq -r '.plugins[].source | select(type == "string")' .github/plugin/marketplace.json \
  | while read -r p; do test -d "$p" || echo "missing plugin dir: $p"; done
```

## Install and smoke-test

```bash
copilot plugin install ./plugins/<name>
copilot plugin list
```

In an interactive session, confirm components loaded with `/agent` and
`/skills list`.
