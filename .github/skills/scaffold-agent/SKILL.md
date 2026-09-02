---
name: scaffold-agent
description: >
  Scaffold a new custom agent (.agent.md) inside an existing agentry
  plugin, covering required frontmatter, tool selection, and validation.
  USE FOR: adding a specialist-role agent to a plugin that already exists.
  DO NOT USE FOR: creating a brand-new plugin (scaffold-plugin) or adding a
  workflow skill (scaffold-skill).
---

**WORKFLOW SKILL**

# Scaffold a new agent

## Overview

An agent is a specialist role scoped to one plugin's domain. This
scaffolds a new `.agent.md` in an existing plugin's `agents/` directory,
fills in required frontmatter, and verifies it loads. Pick the plugin by
domain fit first — an agent belongs to the plugin that owns its domain.

## Steps

1. Pick the plugin the agent belongs to (use `scaffold-plugin` first if
   none fits).
2. Create `plugins/<plugin>/agents/<name>.agent.md` with `name` and
   `description` frontmatter (required) and only the `tools` it needs —
   see [references/frontmatter.md](references/frontmatter.md) for the
   template, optional fields, and validation/reinstall commands.
3. Validate the frontmatter parses as YAML.
4. Reinstall the plugin locally and confirm with `/agent`, then invoke it.

## Example

> "Add a `reviewer` agent to `release-notes` that checks drafted notes
> against the merged PR list."

Create `agents/reviewer.agent.md` with minimal `tools` (likely
`read`/`search`, not `edit`), validate, reinstall, confirm with `/agent`.

## Common issues

- Agent missing from `/agent`: install is cached; rerun
  `copilot plugin install ./plugins/<plugin>`.
- Frontmatter fails to parse: usually an unquoted colon in `description`
  or bad indentation under `tools:`.
- Overly broad `tools:` grant: trim to what the agent's role requires —
  a common review blocker.
