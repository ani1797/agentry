---
name: multi-primitive-update
description: >
  Coordinate a change spanning multiple agentry primitives at once so
  plugin.json, marketplace.json, SKILL.md, and agent.md never drift out of
  sync. USE FOR: renaming or restructuring a plugin, adding several
  components together, or a schema change touching multiple plugins at
  once. DO NOT USE FOR: a change confined to one new plugin, skill, or
  agent — use scaffold-plugin, scaffold-skill, or scaffold-agent instead.
allowed-tools: write(plugins/**) write(.github/plugin/marketplace.json)
---

**WORKFLOW SKILL**

# Coordinate a multi-primitive update

## Overview

A plugin rename touches every path and manifest inside it; a new plugin
ships its first skill and agent together; a schema change ripples across
many `plugin.json` files. Sequences the change so the repo is never left
partially consistent, every touched file landing in one PR with matching
metadata.

## Steps

1. Enumerate every file to touch before editing anything.
2. Edit as one atomic unit per plugin; `git mv` for renames.
3. Keep `name`/`version`/`description` in sync between each `plugin.json`
   and its `marketplace.json` entry.
4. Validate every manifest; run `waza check` on every touched skill.
5. Reinstall every touched plugin; re-verify with `/agent`/`/skills list`.
6. Scope one PR to this change — don't fold in unrelated edits.
7. List every touched primitive (name + path) in the PR description.

Full commands: [references/checklist.md](references/checklist.md).

## Example

> "Rename `release-notes` to `changelog`, add a `notify` skill."

`git mv` the plugin dir, update `name` in both manifests, fix internal
references, use `scaffold-skill` for `notify`, validate, reinstall, list
every touched path in the PR body.

## Common issues

- Stale `marketplace.json` path after a rename: `git mv` doesn't update
  `source` — grep the old name first.
- Version bumped in one manifest, not the other: diff both side by side.
- PR scope creeps to unrelated plugins: split into a separate PR.
