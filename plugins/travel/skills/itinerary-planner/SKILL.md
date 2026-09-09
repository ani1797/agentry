---
name: itinerary-planner
description: >
  Build a day-by-day, budget-aware travel itinerary from a destination, date
  range, traveler preferences, and real flight options pulled from the
  `flights` MCP server, then write it out as a single structured document.
  USE FOR: planning multi-day trip itineraries, comparing flight options and
  candidate travel dates, organizing daily activities/lodging/transport
  logistics into one itinerary doc. DO NOT USE FOR: booking or paying for
  travel, visa/immigration advice, real-time flight status tracking, or a
  single restaurant/activity recommendation unrelated to a broader trip.
compatibility:
  tools: flights MCP server (uv + fli-mcp); see references/getting-started.md
allowed-tools: write(docs/travel/**)
---

**WORKFLOW SKILL**

# Itinerary Planner

## Steps

1. Gather destination(s), dates, traveler count, budget, interests. Ask if
   any is missing.
2. Query the `flights` MCP server for candidate flights; shortlist 2-3 by
   price/duration.
3. Draft a day-by-day plan (travel, activities, meals, rest) referencing
   the chosen flight(s).
4. Write `docs/travel/<trip-name>-itinerary.md` using
   [references/itinerary-template.md](references/itinerary-template.md).
5. Review with the user and iterate.

## Example

> "Plan a 5-day Tokyo itinerary, flying from SF, Nov 10-15, budget $3000."

Gather constraints, search flights, draft the plan, write
`docs/travel/tokyo-nov-itinerary.md`, then review.

## Common issues

- `flights` MCP server unavailable: see
  [references/getting-started.md](references/getting-started.md).
- Missing constraints: ask the user, don't guess dates/budget.

## References

- [references/itinerary-template.md](references/itinerary-template.md)
- [references/getting-started.md](references/getting-started.md)
