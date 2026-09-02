---
name: diataxis
description: >
  Classify, structure, draft, and review docs using the Diátaxis
  framework's four quadrants (tutorial, how-to, reference, explanation).
  USE FOR: deciding which quadrant content belongs to, structuring a new
  doc before writing it, reviewing existing docs for quadrant drift or
  missing sections, and proposing structural rewrites. DO NOT USE FOR:
  non-documentation writing (marketing copy, fiction), or verifying the
  technical accuracy of code samples — that needs a domain specialist.
allowed-tools: write
---

**WORKFLOW SKILL**

# Diátaxis

## Overview

Diátaxis holds that docs serve exactly one of four needs at a time —
learning, doing a task, looking up facts, or understanding why. Mixing
needs in one doc is the most common defect this skill catches.

## Steps

1. **Classify.** Identify the reader's need — learn (tutorial), do X
   (how-to), look up facts (reference), or understand why (explanation).
   Heuristic and per-quadrant voice: [references/quadrants.md](references/quadrants.md).
2. **Structure.** Lay out headings/scope from the quadrant's template in
   `references/quadrants.md` before drafting.
3. **Draft or edit.** Write in the quadrant's voice: tutorials imperative,
   how-tos terse, references exhaustive, explanations discursive.
4. **Review.** For existing docs, run
   [references/review-checklist.md](references/review-checklist.md) for
   quadrant drift, missing sections, audience gaps. Report before editing.
5. **Propose a rewrite.** Draft a concrete rewrite per the checklist —
   offer it, don't silently apply it.

## Example

> "Review docs/getting-started.md — it reads like it's trying to be a
> tutorial and a reference at the same time."

Classify each section, flag drift with the checklist, propose a split.

## Common issues

- Mixed quadrants (e.g. a how-to that stops to explain theory) — split,
  don't try to satisfy both needs in one page.
- Content fitting two quadrants — pick by the reader's immediate goal,
  not by topic.
- Never apply a rewrite silently — flag it as a proposal first.
