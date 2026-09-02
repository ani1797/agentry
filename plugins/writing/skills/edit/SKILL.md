---
name: edit
description: >-
  Use this skill to revise an existing draft for clarity, accuracy, voice,
  and structure without changing its intended meaning. **WORKFLOW SKILL**.
  USE FOR: line-editing a draft essay or post; tightening structure and
  voice; checking factual support before publishing. DO NOT USE FOR: writing
  a first draft or gathering the initial brief.
license: MIT
allowed-tools:
  - bash
  - web_search
  - web_fetch
metadata:
  category: writing
  workflow: editing
  version: "1.0"
---

# Edit

Use this workflow to improve an existing draft without changing its intended meaning.

1. Check audience fit and whether the stated purpose is fulfilled.
2. Check structure, flow, and headings.
3. Tighten language for precision and concision.
4. Check voice and terminology consistency.
5. Check factual support, attribution, and uncertainty.
6. Check accessibility, including descriptive link text and readable lists.
7. Return the revised draft and a short list of material factual gaps or editorial decisions.

Do not silently rewrite verified technical meaning.

## Example

Input: a full draft essay plus its approved brief.
Output: the revised draft, with a short list of factual gaps or editorial decisions the author must confirm.

## Common issues

- Ambiguous claims — flag them in the gap list rather than resolving them silently.
- Voice drift — check edits against the brief's stated voice traits before finalizing.
