# Review checklist and rewrite guidance

Use this when reviewing an existing doc against the Diátaxis framework.

## Quadrant drift

- [ ] Does the doc stay in one quadrant's voice throughout, or does it
      slide between teaching, instructing, informing, and explaining?
- [ ] Are there paragraphs that belong in a different quadrant entirely
      (e.g. a design-rationale aside inside a how-to guide)? Flag them as
      candidates to move into an Explanation doc and link instead.

## Missing expected sections

Check the doc against its quadrant's structure template
(`references/quadrants.md`):

- [ ] Tutorial missing a clear "what you'll build" opener or a verifiable
      end state?
- [ ] How-to missing explicit preconditions, or teaching concepts instead
      of assuming them?
- [ ] Reference inconsistent in per-entry shape, or organized by
      narrative instead of lookup order?
- [ ] Explanation jumping straight to conclusions without stating the
      question/tension it's addressing?

## Audience assumptions

- [ ] Does the doc state (implicitly or explicitly) what the reader
      already knows? A how-to that silently assumes tool installation a
      tutorial never covered is a gap, not a shortcut.
- [ ] Is the doc's entry point discoverable from the quadrant a reader
      would actually search in (e.g. a tutorial buried in reference docs)?

## Proposing a rewrite

1. State the specific defect found (quote or reference the section) —
   don't just say "this is unclear."
2. Identify which quadrant the content should live in, if it's misplaced.
3. Draft the concrete replacement (or a restructuring outline for a
   larger doc) rather than only describing what's wrong.
4. Present the rewrite as a proposal for the requester to accept, adjust,
   or reject — never silently overwrite an existing doc's meaning.

## Common false positives

- Cross-references between quadrants (a how-to linking to an explanation
  for background) are correct Diátaxis practice — don't flag links as
  drift, only content that's duplicated or inlined across quadrants.
- Short clarifying asides (one sentence) inside a how-to are fine; the
  drift signal is paragraphs of sustained explanation-voice, not any
  mention of "why."
