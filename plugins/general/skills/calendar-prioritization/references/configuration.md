# Configuration

Settings live in **Steward's** config file so the two stay in sync:
`$COPILOT_HOME/configuration/steward.md` (`$COPILOT_HOME` defaults to
`~/.copilot`), under a `calendar:` block in the YAML frontmatter. Every
key is optional; anything absent uses the default below. Steward's
Markdown body still applies as standing instructions (e.g. "never move
Friday afternoon").

```yaml
---
autonomy: balanced
calendar:
  company_domain: contoso.com
  manager_email: jane.doe@contoso.com
  skip_manager_email: john.smith@contoso.com
  work_hours: "09:00-17:00"
  work_days: Mon,Tue,Wed,Thu,Fri
  lunch_window: "12:00-13:00"
  breaks: ["10:00-10:15", "15:00-15:15"]
  meeting_buffer: 5
  learning_keywords: [office hours, learning session, brown bag, training]
---
```

## Keys

| Key | Default | Meaning |
|---|---|---|
| `company_domain` | *(none)* | Your email domain. **Without it nothing is classified external** and `[EXT]` never appears. |
| `manager_email` | *(none)* | Elevates meetings with your manager to T2. |
| `skip_manager_email` | *(none)* | Same, for your skip-level. |
| `work_hours` | `09:00-17:00` | Bounds the search for alternative times. |
| `work_days` | `Mon,Tue,Wed,Thu,Fri` | Days eligible for alternatives. |
| `lunch_window` | `12:00-13:00` | T0 block. Synthesized only if no real lunch event exists that day. |
| `breaks` | `10:00-10:15`, `15:00-15:15` | T0 blocks, same rule. |
| `meeting_buffer` | `5` | Minutes required between kept meetings; violations are flagged. |
| `learning_keywords` | office hours, learning session, brown bag, lunch and learn, training | Subject/category match → T3. |
| `high_value_keywords` | high-value, customer-escalation, escalation | Internal match → T4. |
| `protected_keywords` | lunch, break, focus time, focus block, do not book, no meetings, blocked, hold | Your own solo events matching these become T0. |
| `large_meeting_threshold` | `15` | At/above this attendee count a meeting is never rescheduled. |
| `lunch_flex_minutes` | `30` | Maximum ± shift of lunch, and only for a T1/T2 call. |

## Tiers

| Tier | Label | Determined by |
|---|---|---|
| T0 | Protected block | Configured lunch/breaks, or your own solo event matching `protected_keywords`. Yields only lunch, ±`lunch_flex_minutes`, only to T1/T2. |
| T1 | `[EXT]` Customer / external | Any attendee or the organizer has a domain ≠ `company_domain`. |
| T2 | Manager / skip-manager | `manager_email` or `skip_manager_email` attends. |
| T3 | Office hours / learning | Matches `learning_keywords`. Never declined or rescheduled — only marked tentative. |
| T4 | Internal high-value | All-internal and matches `high_value_keywords`. |
| T5 | Internal routine | All-internal, nothing special. |

First match wins, evaluated T0 → T5.

## Conflict rules

1. Within a set of overlapping meetings, the lowest tier number is kept.
   Resolution is **pairwise**: a meeting only yields to something it
   actually overlaps, so a chain never demotes an innocent third meeting.
2. Ties break on earlier start, then larger attendee count.
3. Everything that yields is marked tentative with this note — tier
   labels are never exposed:
   > Kindly notifying you of a double-booked time slot. Here are some
   > alternative times from my calendar: [times]. If rescheduling isn't
   > possible and my attendance is required, please message me directly.
4. T3 and meetings at/above `large_meeting_threshold` get no reschedule
   ask — they are marked tentative only, and large ones carry a note that
   rescheduling isn't feasible within 2 weeks.
5. Alternatives are open slots inside `work_hours` on `work_days`, never
   in the past, with `meeting_buffer` on both sides.

## Non-blocking events

All-day banners, `showAs: free` / `workingElsewhere`, and meetings you
already declined are reported but never create conflicts — this is what
keeps all-day PTO rows from swallowing a day.
