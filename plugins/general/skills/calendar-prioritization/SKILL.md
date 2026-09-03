---
name: calendar-prioritization
description: >
  Prioritize and protect your calendar by enforcing configurable rules that prevent over-commitment, guard breaks and lunch,
  elevate customer and high-value calls, and rank manager or skip-manager meetings above routine internal ones.
  USE FOR: reviewing upcoming calendar for conflicts, applying priority rules to meeting requests, protecting break and lunch
  blocks, surfacing high-value or customer calls, scheduling recurring calendar audits with /every or /loop.
  DO NOT USE FOR: creating calendar events from scratch, sending meeting invites, modifying other people's calendars,
  travel or expense scheduling.
---

**WORKFLOW SKILL**

# Calendar Prioritization

## Steps

1. **Load configuration.** Read the user's configurable settings (company
   domain, manager/skip-manager names and emails, custom notes). If no
   custom config is provided, fall back to sensible defaults — see
   [references/configuration.md](references/configuration.md).
2. **Fetch calendar data.** Use `workiq` tools to retrieve the user's
   upcoming calendar entries for the target window (today, this week, etc.).
   Use `/researcher` or `/explorer` if additional context about attendees
   or meeting topics is needed.
3. **Apply priority rules** in order:
   - **Never over-commit**: flag time slots with overlapping meetings;
     recommend which to decline or reschedule.
   - **Protect breaks/lunch**: ensure designated break and lunch windows
     remain unblocked; suggest moves for conflicts.
   - **Customer & high-value calls first**: elevate meetings with
     external (non-company-domain) attendees or tagged as high-value.
   - **Manager / skip-manager priority**: rank meetings with configured
     manager or skip-manager above remaining internal-only calls.
4. **Present recommendations.** Output a ranked summary: conflicts,
   protected blocks, high-priority meetings, and suggested actions
   (accept, decline, reschedule). Use `/tasks` to track follow-ups.
5. **Schedule recurring runs (optional).** Use `/every` or `/loop` to
   re-run the audit on a cadence (e.g. every morning, every Sunday
   evening) so the calendar stays healthy without manual invocation.

## Example

> "Review my calendar for next week and make sure I'm not over-booked.
> Protect my lunch from 12–1 PM and prioritize any customer calls."

Load config → fetch next week's events → flag overlaps → lock
12–1 PM lunch → boost customer meetings → present ranked list with
action suggestions.

## Common issues

- **No calendar data returned**: confirm `workiq` tools are connected
  and the correct calendar account is authorized.
- **Wrong domain filtering**: update `company_domain` in configuration
  so external attendees are correctly identified.
- **Manager meetings not elevated**: verify manager/skip-manager names
  and emails match the calendar entries exactly.
- **Recurring run not firing**: ensure `/every` or `/loop` is set up
  with a valid cron or interval expression.
