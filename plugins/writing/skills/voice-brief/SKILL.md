---
name: voice-brief
description: >-
  Use this skill first, before drafting, to fix the audience, purpose, voice,
  and constraints as one shared brief. **WORKFLOW SKILL**. USE FOR: kicking
  off a Substack essay, LinkedIn post, or documentation page; capturing voice
  before drafting; re-briefing for a new audience. DO NOT USE FOR: editing a
  draft, researching claims, or publishing.
license: MIT
allowed-tools:
  - bash
  - web_search
  - web_fetch
metadata:
  category: writing
  workflow: audience-brief
  version: "1.0"
---

# Voice brief

Use this workflow before drafting new material or adapting content for a new audience.

1. Collect audience and their context.
2. Collect the desired reader outcome.
3. Collect the author's point of view and voice traits.
4. Collect source material and facts that are approved.
5. Collect format, length, and publication constraints.
6. Collect prohibited claims, phrases, or calls to action.
7. Summarize these decisions as a brief.

Ask focused questions only for details that would materially change the result. Treat unavailable facts as gaps, not assumptions.

## Example

Input: "Brief me for a Substack essay on why small teams ship faster."
Output: a short brief stating the target reader, the promise of the essay, the author's stance, approved evidence, and length constraints.

## Common issues

- Vague audience ("everyone") — ask for one primary reader instead.
- Missing constraints — treat unstated length or format limits as gaps, and note them in the brief rather than guessing.
