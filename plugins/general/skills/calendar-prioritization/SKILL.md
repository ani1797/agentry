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

## Priority tiers

Every meeting is classified into a tier. When time slots conflict, the
higher-tier meeting keeps the slot; lower-tier meetings are marked
**tentative** with a reason and a suggested alternative time within
configured work hours. See
[references/configuration.md](references/configuration.md) for the
full tier table and settings.

| Tier | Label | Criteria |
|------|-------|----------|
| T0 | **Protected block** | Lunch, breaks, focus time — never yielded. |
| T1 | **Customer / external** | Any attendee's email domain ≠ `company_domain`. |
| T2 | **Manager / skip-manager** | Attendee matches configured manager or skip-manager email. |
| T3 | **Internal high-value** | Internal-only but tagged high-value or flagged in `custom_notes`. |
| T4 | **Internal routine** | All attendees share `company_domain`, no special tag. |

**Internal vs external classification**: a meeting is *external* if at
least one attendee's email domain differs from `company_domain`;
*internal* if every attendee shares the same domain as the user.

## Steps

1. **Load configuration.** Read the user's configurable settings (company
   domain, manager/skip-manager info, work hours/days, custom notes).
   Defaults: work hours `09:00–17:00`, work days Mon–Fri — see
   [references/configuration.md](references/configuration.md).
2. **Fetch calendar data.** Use `workiq` tools to retrieve the user's
   upcoming calendar entries for the target window (today, this week, etc.).
   Use `/researcher` or `/explorer` if additional context about attendees
   or meeting topics is needed.
3. **Classify each meeting.**
   - Compare every attendee's email domain against `company_domain`.
     All match → internal; any mismatch → external.
   - Check attendee list against manager/skip-manager emails.
   - Assign the appropriate priority tier (T0–T4).
4. **Detect conflicts and resolve by tier.**
   - For each time slot with overlapping meetings, keep the
     highest-tier meeting accepted.
   - Mark lower-tier meetings **tentative** with a reason
     (e.g. "double-booked — conflicts with T1 customer call").
   - Suggest an alternative time for each tentative meeting by
     scanning open slots within `work_hours` on `work_days`.
5. **Protect breaks/lunch.** Ensure T0 blocks remain unblocked;
   any meeting overlapping a T0 window is moved or marked tentative
   with a suggested alternative.
6. **Present recommendations.** Output a ranked summary grouped by
   tier: conflicts, protected blocks, tentative meetings with
   reasons and suggested reschedule times. Use `/tasks` to track
   follow-ups.
7. **Schedule recurring runs (optional).** Use `/every` or `/loop` to
   re-run the audit on a cadence (e.g. every morning, every Sunday
   evening) so the calendar stays healthy without manual invocation.

## Example

> "Review my calendar for next week and make sure I'm not over-booked.
> Protect my lunch from 12–1 PM and prioritize any customer calls."

Load config → fetch next week's events → classify each meeting by
audience domain → assign tiers → flag overlaps → keep higher-tier,
mark lower-tier tentative with reason and alt time → lock 12–1 PM
lunch → present ranked list grouped by tier.

## Common issues

- **No calendar data returned**: confirm `workiq` tools are connected
  and the correct calendar account is authorized.
- **Wrong internal/external classification**: update `company_domain`
  so attendee domains are compared correctly.
- **Manager meetings not elevated**: verify manager/skip-manager emails
  match the calendar entries exactly.
- **Bad alternative-time suggestions**: check `work_hours` and
  `work_days` in configuration; defaults are 09:00–17:00 Mon–Fri.
- **Recurring run not firing**: ensure `/every` or `/loop` is set up
  with a valid cron or interval expression.
