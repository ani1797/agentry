---
name: scaffold-plugin
description: >
  Scaffold a new Copilot CLI plugin for the agentry marketplace: its
  plugin.json manifest, first component, and marketplace.json entry. USE
  FOR: creating a plugin directory under plugins/ and registering it in
  .github/plugin/marketplace.json. DO NOT USE FOR: adding a skill or agent
  to an existing plugin (scaffold-skill / scaffold-agent), or changes
  spanning several plugins (multi-primitive-update).
allowed-tools: write(plugins/**) write(.github/plugin/marketplace.json)
---

**WORKFLOW SKILL**

# Scaffold a new plugin

## Overview

A plugin is agentry's unit of installation: a directory with `plugin.json`
plus any of `agents/`, `skills/`, `hooks.json`, `.mcp.json`. Use once per
new plugin, then `scaffold-skill`/`scaffold-agent` for components. Confirm
a plugin is warranted first — one per business function, not per
workflow; a single workflow belongs as a skill in an existing plugin.

## Steps

1. Branch `plugin/<name>` (kebab-case, matches `plugin.json`'s `name`)
   from `main`; `mkdir -p plugins/<name>/{agents,skills}`.
2. Write `plugin.json` + matching `marketplace.json` entry, plus stub
   `hooks.json` (every event, empty arrays), `.mcp.json`
   (`mcpServers: {}`), `lsp.json` (`lspServers: {}`) — every new plugin
   ships all three, wired into `plugin.json`, before it uses any of them.
   Templates, fields, validation/install commands:
   [references/manifests.md](references/manifests.md).
3. Add one real component (skill or agent) before opening a PR — an empty
   plugin isn't useful.
4. Validate all five files and every `source` path.
5. Install locally; confirm with `copilot plugin list`, `/agent`,
   `/skills list`.
6. Open a PR: small commits, verification in the description.

## Example

> "Scaffold a `release-notes` plugin with a `draft` skill."

Create the dir + `plugin.json`, invoke `scaffold-skill` for `skills/draft`,
add the marketplace entry, validate, install, open the PR.

## Common issues

- Stale cache: rerun `copilot plugin install ./plugins/<name>`.
- Missing dir from `jq`: `source` is relative to repo root, not
  `.github/plugin/`.
- One trivial skill flagged: fold into an existing plugin instead.
