---
name: draft
description: >-
  Use this skill to turn an approved brief and outline into a complete,
  reader-focused draft. **WORKFLOW SKILL**. USE FOR: writing a first draft
  of an essay, LinkedIn post, or documentation page; turning an outline into
  prose. DO NOT USE FOR: gathering a brief, researching sources, or line
  editing an existing draft.
license: MIT
allowed-tools:
  - bash
  - web_search
  - web_fetch
metadata:
  category: writing
  workflow: drafting
  version: "1.0"
---

# Draft

Use this workflow after the audience, purpose, and evidence are clear.

1. Confirm the reader outcome, structure, and format from the brief and outline.
2. Write a complete draft that fulfills the stated reader outcome.
3. Use concrete language and active verbs.
4. Distinguish fact from interpretation.
5. Include only claims supported by the available material.
6. Preserve placeholders for missing information.

Do not fabricate quotations, statistics, examples, personal experience, links, or citations.

## Example

Input: an approved brief plus a research-outline for a LinkedIn post on remote-team onboarding.
Output: a complete draft that follows the outline's section order, with `[NEEDS SOURCE]` placeholders where evidence is missing.

## Common issues

- Missing evidence — insert a placeholder and flag it instead of inventing a statistic or quotation.
- Outline mismatch — if the approved outline doesn't fit the material, note the conflict rather than silently restructuring it.
