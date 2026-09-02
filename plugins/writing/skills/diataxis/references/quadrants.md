# The four Diátaxis quadrants

Each quadrant answers one reader need. A doc should serve exactly one.

## Tutorial — "I want to learn"

- **Orientation:** learning-oriented. The reader is a beginner; the goal
  is building confidence and familiarity through a guided, hands-on
  lesson, not efficiency.
- **Voice:** imperative, hand-holding, encouraging. Concrete steps with
  a predictable, working result at the end. Avoid options or
  alternatives — one path only.
- **Structure template:**
  1. What you'll build/learn (one sentence).
  2. Prerequisites (exact versions/setup, no ambiguity).
  3. Numbered steps, each with an expected observable result.
  4. A working end state the reader can verify.
- **Out of scope:** explaining *why* something works (that's
  Explanation), covering edge cases or alternatives (that's How-to /
  Reference).

## How-to guide — "I need to do X"

- **Orientation:** task-oriented. The reader already knows the basics and
  wants to accomplish a specific, real-world goal.
- **Voice:** terse, direct, assumes competence. No teaching, no
  hand-holding — get to the goal.
- **Structure template:**
  1. The goal, stated as a title ("How to ...").
  2. Preconditions/assumptions (what the reader must already have/know).
  3. Steps or a recipe, allowing branches for real variations.
  4. What "done" looks like.
- **Out of scope:** teaching concepts from scratch (Tutorial), exhaustive
  option listings (Reference).

## Reference — "I need the facts"

- **Orientation:** information-oriented. The reader is looking something
  up, not reading start to finish.
- **Voice:** exhaustive, neutral, consistent structure across entries so
  the reader can skim and jump.
- **Structure template:**
  1. Consistent per-entry shape (e.g. name, signature, parameters,
     return value, example) applied uniformly.
  2. Organized for lookup (alphabetical, by module, by command) — not by
     narrative order.
- **Out of scope:** narrative explanation of design rationale
  (Explanation), step-by-step task framing (How-to).

## Explanation — "I want to understand why"

- **Orientation:** understanding-oriented. The reader wants context,
  background, trade-offs, and the reasoning behind a design or behavior.
- **Voice:** discursive, unhurried, allowed to explore alternatives and
  history.
- **Structure template:**
  1. The question or tension being addressed.
  2. Background/context.
  3. Discussion of trade-offs, alternatives, or rationale.
  4. Where this connects to other parts of the system (links out, not
     duplicated steps).
- **Out of scope:** actionable steps (How-to/Tutorial), exhaustive
  parameter listings (Reference).

## Classification heuristic

When content could fit more than one quadrant, ask: *what is the reader
trying to do in the moment they open this page?* Classify by that
immediate need, not by topic. If a single doc genuinely serves two needs,
split it into two docs and cross-link them — don't merge the voices.
