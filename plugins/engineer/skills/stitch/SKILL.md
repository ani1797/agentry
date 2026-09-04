---
name: stitch
description: >
  Prototype and iterate on UI/UX designs via the Stitch MCP toolset.
  USE FOR: starting a UI prototype, editing Stitch screens, building
  or switching design systems, generating variants, or re-skinning
  screens. DO NOT USE FOR: hand-written production frontend code,
  non-Stitch tools (Figma, Sketch), or diagrams (use mermaid).
compatibility:
  mcp: Requires stitch, context7, playwright MCP; see references/getting-started.md.
---

**WORKFLOW SKILL**

# Stitch

One design system drives many screens; build one screen at a time via
Spec → Refine → Build → Verify → Proceed. See
[tool-notes.md](references/tool-notes.md).

## Setup (once per project)

Orient via `list_projects`/`get_project`/`list_screens`/
`list_design_systems`, then `create_project` + paired
`create_design_system`/`update_design_system` (repeat per theme).

## Per-screen loop

One screen at a time; don't start the next until Verify passes.

1. **Spec**: define purpose/content, pick `designSystem` id (else
   defaults wrong).
2. **Refine**: on an existing screen, tighten via `generate_variants`
   (`creativeRange`: `REFINE`/`EXPLORE`/`REIMAGINE`, scoped `aspects`)
   before build.
3. **Build**: `generate_screen_from_text` (new) or `edit_screens`
   (scoped edit, never regen).
4. **Verify**: `get_screen` for `htmlCode`; drive with
   `playwright-browser_navigate`/`browser_snapshot`.
5. **Proceed**: next screen. Re-skin many at once instead via
   `apply_design_system` on `selectedScreenInstances` (id from
   `get_project`).

## Example

> "Prototype a fitness app with light/dark design systems, sharing one
> onboarding screen."

## Common issues

- Off-brand screen or no-op re-skin: wrong `designSystem`, or a screen
  id where an instance id was needed.
- `delete_project` is irreversible — confirm first; use for
  test-project cleanup too.
- Missing tools: restart — [setup](references/getting-started.md).
