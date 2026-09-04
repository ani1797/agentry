---
name: stitch
description: >
  Prototype and iterate on UI/UX designs using the Stitch MCP toolset.
  USE FOR: starting a UI prototype, editing screens in a Stitch
  project, building and switching between multiple design systems,
  generating refine/explore/reimagine variants, or re-skinning screens.
  DO NOT USE FOR: hand-writing production frontend code, non-Stitch
  tools (Figma, Sketch), or diagrams (use the mermaid skill).
compatibility:
  mcp: Requires stitch, context7, playwright MCP servers; see references/getting-started.md.
---

**WORKFLOW SKILL**

# Stitch

One design system drives many screens; every change is a scoped edit or
explicit re-skin, never an untracked regen. Details:
[tool-notes.md](references/tool-notes.md).

## Steps

1. Orient: `list_projects`, `get_project`, `list_screens`,
   `list_design_systems`.
2. New project: `create_project`, then `create_design_system` +
   `update_design_system` (paired). Repeat per extra brand/theme —
   track each asset id.
3. New screen: `generate_screen_from_text` with `designSystem` set, or
   it silently defaults to the wrong theme.
4. Small tweak: `edit_screens` (scoped DOM edit), never full regen.
5. Alternatives: `generate_variants` with `creativeRange`
   (`REFINE`/`EXPLORE`/`REIMAGINE`) and scoped `aspects`.
6. Re-skin: `apply_design_system` on `selectedScreenInstances`
   (instance `id` from `get_project`) — pass another asset id to
   switch systems.
7. Verify: `get_screen` for `htmlCode`; drive with
   `playwright-browser_navigate` + `browser_snapshot`.

## Example

> "Prototype a fitness app with a light and a dark design system,
> sharing the same onboarding screen."

## Common issues

- Off-brand screen: wrong/omitted `designSystem` — recheck with
  `list_design_systems`.
- `apply_design_system` no-ops: passed a source screen id, not the
  instance id.
- `delete_project` is irreversible — confirm first.
- Missing MCP tools: [getting-started.md](references/getting-started.md).
