---
name: calendar-prioritization
description: >
  Review and rank a Microsoft 365 calendar: tier meetings T0-T5, label external
  calls [EXT], resolve double-bookings by tier, protect lunch.
  USE FOR: finding calendar conflicts, ranking customer, manager and learning
  meetings, marking overlaps tentative with alternative times, enforcing meeting
  buffers, summarizing what meetings are about.
  DO NOT USE FOR: creating meetings, sending invites, editing other calendars,
  drafting email, travel planning.
allowed-tools: write(/tmp/calendar-prioritization/**)
compatibility:
  cli: uv — see references/getting-started.md
  mcp: workiq (Microsoft 365)
---

**WORKFLOW SKILL**

# Calendar Prioritization

Two cheap WorkIQ fetches feed one deterministic scorer.

## Steps

1. Read `calendar:` in Steward's
   `$COPILOT_HOME/configuration/steward.md`; defaults fill the rest —
   [references/configuration.md](references/configuration.md).
2. Fetch the window (default today) **without** `attendees` — ~93% of
   the payload — [references/workiq-recipes.md](references/workiq-recipes.md).
3. Write those events, config, `timezone` and `now` to
   `/tmp/calendar-prioritization/input.json`; run
   `uv run scripts/prioritize.py FILE --stage triage`.
4. Fetch attendees for `needs_attendees` only, in one batched `fetch`;
   merge under `attendees`.
5. Rerun with `--format markdown`. The script owns every tier, conflict,
   buffer and slot decision — never redo it.
6. Report each `purpose` verbatim; for `needs_purpose` ids infer one
   line from subject and organizer.
7. Apply tentative responses and protected blocks with `do_action` and
   `create_entity`.

## Example

> "Sort out tomorrow — protect lunch, keep customer calls."

## Common issues

- All meetings land in T5: `company_domain` unset, or step 4 skipped.
- Slow run: attendees fetched for the window, not `needs_attendees`.
- Wrong times: pass `timezone` and `now`.
- `uv`/WorkIQ missing or EULA unaccepted:
  [getting-started.md](references/getting-started.md).