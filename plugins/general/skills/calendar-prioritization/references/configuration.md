# Calendar Prioritization — Configuration

## Loading configuration

Settings are read from **`~/calendar.md`** at invocation time. If the
file does not exist, all defaults below apply. Any setting present in
the file overrides the default; omitted settings keep their default.

## Configurable settings

| Setting | Description | Default |
|---|---|---|
| `company_domain` | Your company's email domain (e.g. `acme.com`). Used to classify meetings as internal or external by comparing every attendee's domain. | *(none — all attendees treated as external)* |
| `manager_name` | Display name of your direct manager. | *(none)* |
| `manager_email` | Email address of your direct manager. | *(none)* |
| `skip_manager_name` | Display name of your skip-level manager. | *(none)* |
| `skip_manager_email` | Email address of your skip-level manager. | *(none)* |
| `custom_notes` | Free-form notes: things to prioritize ("always keep Friday focus time") or avoid ("no meetings before 9 AM"). | *(none)* |
| `lunch_window` | Time range to protect for lunch (24 h format). May flex ±30 min to accommodate customer calls. | `12:00–13:00` |
| `break_count` | Number of break blocks per day. | `2` |
| `break_duration` | Duration of each break in minutes. | `15` |
| `break_windows` | Explicit time ranges for breaks (overrides count/duration if set). | *(none — auto-placed based on count and duration)* |
| `meeting_buffer` | Minimum gap in minutes between consecutive meetings to avoid back-to-back scheduling. | `5` |
| `work_hours` | Start and end of your workday (24 h format). Used when suggesting alternative times for tentative meetings. | `09:00–17:00` |
| `work_days` | Comma-separated working days. | `Mon, Tue, Wed, Thu, Fri` |
| `learning_keywords` | Comma-separated keywords to identify office-hours and learning sessions by meeting title or category (case-insensitive). | `office hours, learning session, brown bag, lunch and learn, training` |

## Priority tiers

Meetings are assigned a tier based on audience and configuration.
When multiple meetings overlap, the higher-tier meeting keeps the slot;
lower-tier meetings are marked **tentative** with a reason and a
suggested alternative time within `work_hours` on `work_days`.

| Tier | Label | How it's determined |
|------|-------|---------------------|
| T0 | Protected block | Lunch, breaks, focus time from config — never yielded. |
| T1 | [EXT] Customer / external | At least one attendee's email domain ≠ `company_domain`. Labelled **[EXT]**. Lunch may flex ±30 min to accommodate. |
| T2 | Manager / skip-manager | Attendee matches `manager_email` or `skip_manager_email` (internal). |
| T3 | Office hours / learning | Title or category matches any `learning_keywords` entry. **Always accepted** — never declined or rescheduled, only marked tentative when conflicting with T0–T1. |
| T4 | Internal high-value | All attendees share `company_domain`, meeting tagged high-value or flagged in `custom_notes`. |
| T5 | Internal routine | All attendees share `company_domain`, no special tag. |

### Internal vs external classification

A meeting is **external** if any attendee's email domain differs from
`company_domain`. It is **internal** if every attendee shares the same
domain as the user.

### Conflict resolution

When two or more meetings occupy the same time slot:

1. The meeting with the lowest tier number (highest priority) stays accepted.
2. Each remaining meeting is marked **tentative** with a polite note
   (do not expose internal tier labels):
   - *"Kindly notifying you of a double-booked time slot. Here are
     some alternative times from my calendar: [times]. If rescheduling
     isn't possible and my attendance is required, please message me
     directly."*
3. **T3 (office hours / learning) and meetings with large attendance
   lists are never declined or rescheduled.** They are only marked
   tentative so the user retains the option to join.
4. If rescheduling is not feasible within 2 weeks due to a large
   attendee list, note that in the recommendation.
5. A suggested alternative time is provided by scanning the next
   available open slot within `work_hours` on `work_days` (this does
   not apply to T3 or large-attendance meetings).

### Meeting buffer

A configurable gap (`meeting_buffer`, default 5 min) is enforced
between consecutive meetings. Back-to-back meetings that violate this
buffer are flagged in the output.

### Lunch flexibility

When a T1 customer call overlaps the configured `lunch_window`, lunch
may shift up to ±30 minutes rather than declining the customer call.

## Example configuration (`~/calendar.md`)

```
company_domain: acme.com
manager_name: Jane Doe
manager_email: jane.doe@acme.com
skip_manager_name: John Smith
skip_manager_email: john.smith@acme.com
lunch_window: 12:00–13:00
break_count: 2
break_duration: 15
# break_windows: 10:00–10:15, 15:00–15:15  ← overrides count/duration if set
meeting_buffer: 5
work_hours: 09:00–17:00
work_days: Mon, Tue, Wed, Thu, Fri
learning_keywords: office hours, learning session, brown bag, lunch and learn, training
custom_notes: >
  Prioritize anything tagged "customer-escalation".
  Avoid scheduling over Friday afternoon focus time (14:00–17:00).
```

## Using with /every and /loop

Pass the configuration once; subsequent recurring runs reuse it:

```
/every weekday 8:30 AM → /calendar-prioritization
```

Override a single setting for one run by specifying it inline:

```
/calendar-prioritization lunch_window=11:30–12:30
```
