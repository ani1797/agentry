# Calendar Prioritization — Configuration

## Configurable settings

Provide these when invoking the skill or store them for recurring runs.
Any omitted setting uses its default.

| Setting | Description | Default |
|---|---|---|
| `company_domain` | Your company's email domain (e.g. `acme.com`). Used to classify meetings as internal or external by comparing every attendee's domain. | *(none — all attendees treated as external)* |
| `manager_name` | Display name of your direct manager. | *(none)* |
| `manager_email` | Email address of your direct manager. | *(none)* |
| `skip_manager_name` | Display name of your skip-level manager. | *(none)* |
| `skip_manager_email` | Email address of your skip-level manager. | *(none)* |
| `custom_notes` | Free-form notes: things to prioritize ("always keep Friday focus time") or avoid ("no meetings before 9 AM"). | *(none)* |
| `lunch_window` | Time range to protect for lunch (24 h format). | `12:00–13:00` |
| `break_windows` | Comma-separated time ranges for breaks. | *(none)* |
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
| T1 | Customer / external | At least one attendee's email domain ≠ `company_domain`. |
| T2 | Manager / skip-manager | Attendee matches `manager_email` or `skip_manager_email` (internal). |
| T3 | Office hours / learning | Title or category matches any `learning_keywords` entry. **Always accepted** — never declined, only marked tentative when conflicting with T0–T1 so the user retains the option to join. |
| T4 | Internal high-value | All attendees share `company_domain`, meeting tagged high-value or flagged in `custom_notes`. |
| T5 | Internal routine | All attendees share `company_domain`, no special tag. |

### Internal vs external classification

A meeting is **external** if any attendee's email domain differs from
`company_domain`. It is **internal** if every attendee shares the same
domain as the user.

### Conflict resolution

When two or more meetings occupy the same time slot:

1. The meeting with the lowest tier number (highest priority) stays accepted.
2. Each remaining meeting is marked **tentative** with a reason:
   - *"Double-booked — conflicts with T1 customer call at 10:00 AM"*
   - *"Triple-booked — conflicts with T1 and T2 meetings at 14:00"*
3. **T3 (office hours / learning) are never declined.** When they
   conflict with a higher-tier meeting, they are marked tentative
   (not declined) so the user retains the option to join.
4. A suggested alternative time is provided by scanning the next
   available open slot within `work_hours` on `work_days`.

## Example configuration

```
company_domain: acme.com
manager_name: Jane Doe
manager_email: jane.doe@acme.com
skip_manager_name: John Smith
skip_manager_email: john.smith@acme.com
lunch_window: 12:00–13:00
break_windows: 10:00–10:15, 15:00–15:15
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
