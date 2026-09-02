# Manifest templates and validation

## `plugins/<name>/plugin.json`

```json
{
  "name": "<name>",
  "description": "One concrete sentence: what it does, when to use it.",
  "version": "0.1.0",
  "author": { "name": "Jane Doe", "email": "jane@example.com" },
  "license": "MIT",
  "keywords": ["example"]
}
```

Only `name` is required (kebab-case, letters/numbers/hyphens, max 64 chars).
Component paths (`agents`, `skills`, `hooks`, `mcpServers`, `lspServers`)
default to `agents/` and `skills/` — omit them unless you need non-default
paths.

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

## Validation

```bash
jq -e . plugins/<name>/plugin.json > /dev/null
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
