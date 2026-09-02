---
name: mermaid
description: >
  Validate Mermaid diagrams with the mmdc CLI, as `mermaid` fenced code
  blocks in markdown or standalone docs/diagrams/*.mmd files.
  USE FOR: adding or editing a Mermaid diagram, validating that a diagram's
  syntax renders cleanly before committing, or regenerating a
  docs/diagrams/*.mmd preview image.
  DO NOT USE FOR: generating non-Mermaid images, or writing diagrams in a
  non-Mermaid format such as PlantUML or Graphviz DOT.
allowed-tools: write(docs/diagrams/**)
compatibility:
  cli: Requires mmdc (@mermaid-js/mermaid-cli); see references/validation.md.
---

**WORKFLOW SKILL**

# Mermaid

Produce neat, valid Mermaid diagrams; always validate with `mmdc` before
finishing — never leave an unrendered or broken diagram in a doc.

## Steps

1. Pick diagram type and style:
   [references/diagram-types.md](references/diagram-types.md).
2. Pick placement: **embedded** `mermaid` fenced block in the target
   markdown file, or **standalone** `docs/diagrams/<name>.mmd` referenced
   via `![alt](../diagrams/<name>.svg)`.
3. Write the diagram per the style rules in the same reference doc.
4. Validate with `mmdc` per
   [references/validation.md](references/validation.md); fix reported
   errors and re-validate until exit 0. Delete temp render output for
   embedded blocks; keep the rendered `.svg` for standalone files.
5. Re-render standalone diagrams when their `.mmd` source changes.

## Example

> "Add a sequence diagram to docs/architecture.md showing the auth flow
> between client, API, and token service."

Write a `sequenceDiagram` fenced block, validate with `mmdc`, fix errors,
leave the validated block embedded in the doc.

## Common issues

- Sandbox/Chromium render errors:
  [references/validation.md](references/validation.md).
- Parse-error lines count from the diagram's start keyword, not the file.
- Delete stray `.svg`/`.png` temp files after validating embedded blocks.
