# WorkIQ recipes (verified against Microsoft Graph paths)

All calls go through the `workiq` MCP server. OData parameters must be
**URL-encoded** (`%24select`, not `$select`) — a literal `$` inside the
JSON argument breaks the request.

## 1. Lean window fetch (always first)

`fetch` with a single entity URL. Omitting `attendees` is the whole
optimization: for a real 21-event / 2-day window this returned **23 KB
instead of 216 KB**.

```
/me/calendarView
  ?startDateTime=2026-09-03T00:00:00Z
  &endDateTime=2026-09-04T00:00:00Z
  &%24select=id,subject,start,end,isAllDay,showAs,categories,responseStatus,isOrganizer,bodyPreview,location,organizer
  &%24orderby=start/dateTime
  &%24top=50
```

- `startDateTime` / `endDateTime` are UTC instants; convert the user's
  local window before building the URL.
- Times come back in UTC — pass the user's IANA zone as `timezone` in the
  script input, never convert by hand.
- `bodyPreview` is what makes the summary informative; the script strips
  Teams/Zoom join boilerplate from it.

## 2. Targeted attendee fetch (second)

One `fetch` call, many entity URLs — batched, ~5 KB per event:

```
/me/events/{event-id}?%24select=id,attendees
```

Send only the ids the script listed under `needs_attendees`. Add
`needs_attendees_optional` **only** when the window is a single day and
the user wants `[EXT]` labels on every meeting.

Merge results into the script input as:

```json
{ "attendees": { "<event id>": [ { "emailAddress": { "address": "a@b.com" } } ] } }
```

## 3. Mark a meeting tentative

`do_action` on `/me/events/{event-id}/tentativelyAccept`. Verified
request body (note the capitalized keys):

```json
{
  "Comment": "<the script's message field, verbatim>",
  "SendResponse": true
}
```

Never paste the tier label (`T4`, `T5`, …) into `Comment` — the
script's `message` is already written for an external reader.

`ProposedNewTime` accepts `{ "start": {...}, "end": {...} }` if you want
to propose a new slot; use one of the script's `alternatives`.

## 4. Create or move a protected block

`create_entity` with parent `/me/events` (run `get_schema` first if the
tenant rejects the body):

```json
{
  "subject": "Lunch",
  "showAs": "busy",
  "isReminderOn": false,
  "start": { "dateTime": "2026-09-04T12:00:00", "timeZone": "America/Toronto" },
  "end":   { "dateTime": "2026-09-04T13:00:00", "timeZone": "America/Toronto" }
}
```

To flex an existing block, `update_entity` on `/me/events/{event-id}`
with just `start` and `end`. Only a T1/T2 call may move lunch, and only
by up to `lunch_flex_minutes`; the script decides this and reports it
under `protected_blocks`.

## Cost guardrails

| Call | Real measurement |
|---|---|
| 2-day lean `calendarView`, 21 events | 23 KB |
| Same window including `attendees` | ~216 KB |
| Batched attendee fetch, 4 events | 22 KB |

If a run is about to exceed roughly 10 attendee fetches, narrow the
window instead — the skill is designed to run a day at a time.

## Tools deliberately not used

`ask` and `retrieve` are semantic M365 Copilot calls: slow, non-repeatable,
and they cannot return the structured fields the scorer needs. Use `fetch`.
