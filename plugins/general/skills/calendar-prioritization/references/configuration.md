# Calendar Prioritization — Configuration

## Configurable settings

Provide these when invoking the skill or store them for recurring runs.
Any omitted setting uses its default.

| Setting | Description | Default |
|---|---|---|
| `company_domain` | Your company's email domain (e.g. `acme.com`). Used to distinguish internal vs. external attendees. | *(none — all attendees treated as external)* |
| `manager_name` | Display name of your direct manager. | *(none)* |
| `manager_email` | Email address of your direct manager. | *(none)* |
| `skip_manager_name` | Display name of your skip-level manager. | *(none)* |
| `skip_manager_email` | Email address of your skip-level manager. | *(none)* |
| `custom_notes` | Free-form notes: things to prioritize ("always keep Friday focus time") or avoid ("no meetings before 9 AM"). | *(none)* |
| `lunch_window` | Time range to protect for lunch (24 h format). | `12:00–13:00` |
| `break_windows` | Comma-separated time ranges for breaks. | *(none)* |

## Example configuration

```
company_domain: acme.com
manager_name: Jane Doe
manager_email: jane.doe@acme.com
skip_manager_name: John Smith
skip_manager_email: john.smith@acme.com
lunch_window: 12:00–13:00
break_windows: 10:00–10:15, 15:00–15:15
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
