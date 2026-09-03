---
name: calendar-prioritization
description: >
  Enforce configurable calendar rules that prevent over-commitment, guard breaks and lunch,
  label external calls with [EXT], enforce meeting buffers, and rank customer, manager, and learning sessions.
  USE FOR: reviewing upcoming calendar for conflicts, applying priority rules to meeting requests, protecting break and lunch
  blocks, surfacing high-value or customer calls, scheduling recurring calendar audits with /every or /loop.
  DO NOT USE FOR: creating calendar events from scratch, sending meeting invites, modifying other people's calendars,
  travel or expense scheduling.
---

**WORKFLOW SKILL**

# Calendar Prioritization

Classifies meetings into tiers (T0–T5), resolves conflicts by tier,
labels external calls **[EXT]**, and protects breaks/lunch. Full tier
table, conflict rules, and tentative-message templates are in
[references/configuration.md](references/configuration.md).

## Steps

1. **Load config** from `~/calendar.md`; on first run create it via
   WorkIQ inference + defaults. Accept WorkIQ EULA automatically.
2. **Fetch calendar** via WorkIQ tools for the next 14 weekdays.
   Use `/explore` for extra attendee context.
3. **Classify** each meeting (domain check → [EXT], manager match,
   `learning_keywords`) and assign tier T0–T5.
4. **Enforce buffer** (default 5 min) between consecutive meetings.
5. **Resolve conflicts** — keep highest tier accepted; mark lower-tier
   tentative with polite note and alternative times (see reference).
   T3 and large-attendance meetings are never declined.
6. **Protect T0 blocks** (lunch flexes ±30 min for customer calls).
7. **Present** ranked summary; use `/tasks` for follow-ups.
8. **Schedule** hourly recurring run via `/every` if none exists.

## Example

> "Review my calendar for next week, protect lunch, prioritize
> customer calls."

## Common issues

- **No data**: verify WorkIQ connection and EULA acceptance.
- **Wrong [EXT] label**: check `company_domain` in `~/calendar.md`.
- **Manager not elevated**: confirm manager email matches calendar.
- **Bad alt-times**: check `work_hours`/`work_days` defaults.
