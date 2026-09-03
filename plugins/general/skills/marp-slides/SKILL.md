---
name: marp-slides
description: >
  Generate Marp/Marpit slide decks from Markdown for quick presentations.
  USE FOR: scaffolding a deck under docs/slides/NAME/, theming/layout,
  backgrounds/icons, visual verification, export to PDF/PPTX/HTML.
  DO NOT USE FOR: long-form docs/reports, standalone diagrams.
allowed-tools: write(docs/slides/**)
compatibility:
  cli: marp — see references/getting-started.md if missing
  browser: Chrome, Edge, or Firefox — required for PDF/PPTX/image export
---

**WORKFLOW SKILL**

# Marp Slides

## Steps

1. `mkdir -p docs/slides/NAME/{assets,output}` (`NAME` kebab-case).
2. Write `main.md`: front matter on line 1 (`marp: true`, `theme`,
   `paginate`, `size`, `title`), slides split by `---`, one idea each.
   Use directives (`_class: lead`, `backgroundImage`, `header`/`footer`,
   `<!-- fit -->`) and image syntax for layout; icons/images go in
   `assets/`. Speaker notes are trailing HTML comments. Full syntax:
   [references/marp-reference.md](references/marp-reference.md).
3. **Verify visually (mandatory).** Render to temp PNGs and `view` each;
   fix overflow, clipping, contrast, or broken assets in `main.md`;
   re-render. Repeat until clean —
   [references/verification.md](references/verification.md).
4. Export to `docs/slides/NAME/output/NAME.{pdf,pptx,html}` via `marp`
   (`--allow-local-files` if using `assets/`) — commands in reference.

## Example

> "Make a quick 6-slide deck introducing our new API, export to PDF."

Scaffold, write slides with a title and a background-image section,
verify renders, export.

## Common issues

- Blank export or `marp` missing: install per
  [references/getting-started.md](references/getting-started.md); add
  `--allow-local-files` for blocked local assets.
- Unstyled preview: front matter must start on line 1.
- Overflow found in verification: split slides, don't shrink text; recheck.
