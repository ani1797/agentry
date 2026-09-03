---
name: calendar-prioritization
description: >
  Prioritize and protect your calendar by enforcing configurable rules that prevent over-commitment, guard breaks and lunch,
  label external calls with [EXT], enforce meeting buffers, and rank customer, manager, and learning sessions appropriately.
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
**tentative** with a polite reason and, where feasible, a suggested
alternative time. See
[references/configuration.md](references/configuration.md) for the
full tier table and settings.

| Tier | Label | Criteria |
|------|-------|----------|
| T0 | **Protected block** | Lunch, breaks, focus time — configurable count, duration, and windows. Never yielded. |
| T1 | **[EXT] Customer / external** | Any attendee's email domain ≠ `company_domain`. Labelled **[EXT]** in output. Lunch may shift ±30 min to accommodate. |
| T2 | **Manager / skip-manager** | Attendee matches configured manager or skip-manager email. |
| T3 | **Office hours / learning** | Title or category matches `learning_keywords`. Always accepted — never declined or rescheduled, only marked tentative when conflicting with T0–T1. |
| T4 | **Internal high-value** | Internal-only but tagged high-value or flagged in `custom_notes`. |
| T5 | **Internal routine** | All attendees share `company_domain`, no special tag. |

**Internal vs external classification**: a meeting is *external* (labelled
**[EXT]**) if at least one attendee's email domain differs from
`company_domain`; *internal* if every attendee shares the same domain.

## Steps

1. **Load configuration.** Read settings from `~/calendar.md` if the
   file exists; otherwise fall back to defaults. Settings include company
   domain, manager/skip-manager info, work hours/days, break
   count/duration, lunch window, meeting buffer, and custom notes — see
   [references/configuration.md](references/configuration.md).
2. **Accept WorkIQ EULA.** Automatically accept the WorkIQ EULA via the
   `workiq_accept_eula` tool so calendar queries proceed without manual
   intervention.
3. **Fetch calendar data.** Use WorkIQ tools (`workiq_get_calendar_events`,
   `workiq_search_calendar`) to retrieve the user's upcoming calendar
   entries for the target window (today, this week, etc.). Use `/explore`
   if additional context about attendees or meeting topics is needed.
4. **Classify each meeting.**
   - Compare every attendee's email domain against `company_domain`.
     All match → internal; any mismatch → external (label **[EXT]**).
   - Check attendee list against manager/skip-manager emails.
   - Match title/category against `learning_keywords`.
   - Assign the appropriate priority tier (T0–T5).
5. **Enforce meeting buffer.** Insert a configurable gap (default 5 min)
   between consecutive meetings where possible. Flag back-to-back
   meetings that violate the buffer.
6. **Detect conflicts and resolve by tier.**
   - For each time slot with overlapping meetings, keep the
     highest-tier meeting accepted.
   - Mark lower-tier meetings **tentative** with a polite note:
     *"Kindly notifying you of a double-booked time slot. Here are
     some alternative times from my calendar: … If rescheduling isn't
     possible and my attendance is required, please message me
     directly."*
   - Do **not** include internal tier labels in the tentative reason.
   - If rescheduling is not feasible within 2 weeks due to a large
     attendee list, note that in the recommendation.
   - **T3 (office hours / learning) and meetings with large attendance
     lists are never declined or rescheduled** — they are only marked
     tentative so the user retains the option to join.
   - For T1 customer calls that overlap a lunch block, lunch may shift
     up to ±30 minutes rather than declining the customer call.
7. **Protect breaks/lunch.** Ensure T0 blocks remain unblocked;
   any non-T1 meeting overlapping a T0 window is moved or marked
   tentative with a suggested alternative.
8. **Present recommendations.** Output a ranked summary grouped by
   tier: conflicts, protected blocks, buffer violations, tentative
   meetings with reasons and suggested reschedule times. Use `/tasks`
   to track follow-ups.
9. **Schedule recurring runs (optional).** Use `/every` or `/loop` to
   re-run the audit on a cadence (e.g. every morning, every Sunday
   evening) so the calendar stays healthy without manual invocation.

## Example

> "Review my calendar for next week and make sure I'm not over-booked.
> Protect my configurable lunch block and prioritize any customer calls."

Load config from `~/calendar.md` → accept WorkIQ EULA → fetch next
week's events → classify each meeting by audience domain → label
external calls [EXT] → assign tiers → enforce 5-min buffer → flag
overlaps → keep higher-tier, mark lower-tier tentative with polite
note and alternative times → protect lunch (flex ±30 min for customer
calls) → present ranked list grouped by tier.

## Common issues

- **WorkIQ EULA not accepted**: the skill auto-accepts via
  `workiq_accept_eula`; if it still fails, confirm the tool is
  available in `.mcp.json`.
- **No calendar data returned**: confirm WorkIQ tools are connected
  and the correct calendar account is authorized. Verify
  `workiq_get_calendar_events` returns data.
- **Wrong internal/external classification**: update `company_domain`
  so attendee domains are compared correctly.
- **Manager meetings not elevated**: verify manager/skip-manager emails
  match the calendar entries exactly.
- **Bad alternative-time suggestions**: check `work_hours` and
  `work_days` in configuration; defaults are 09:00–17:00 Mon–Fri.
- **Recurring run not firing**: ensure `/every` or `/loop` is set up
  with a valid cron or interval expression.
