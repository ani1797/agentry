# agentry
GitHub Copilot CLI Marketplace

## Finance

The `finance` plugin includes **Plutus**, a personal financial-planning
advisor for budgeting, debt, savings, investing, insurance, and retirement,
and three reusable skills:

| Skill | Purpose |
|---|---|
| `financial-statements` | CIBC Online Banking and Wealthsimple CSV/JSON exports |
| `financial-baseline` | Reconciled account/profile records and versioned planning assumptions |
| `financial-modeling` | Offline statistics, backtesting, FIRE simulations, tax/CPP/RESP calculations, and withdrawal schedules |

Install with `copilot plugin install finance@agentry` after registering
this marketplace. Select Plutus with `/agent`, or invoke the downloader
with `/financial-statements`. If a user-level copy of that skill is already
installed, keep only one active copy to avoid name collisions; this plugin
does not remove the original.

Plutus provides advice, not transaction execution or licensed professional
services. Statement downloads run separately and require Python 3 and the
Playwright MCP server; 1Password is optional. See the skill's
[setup guide](plugins/finance/skills/financial-statements/references/getting-started.md).
Financial records remain outside the plugin under `~/Documents/statements`
by default; do not commit personal records to this repository.

The modeling toolkit uses Python's standard library and synthetic examples,
not personal data or embedded market forecasts. See its
[model contracts](plugins/finance/skills/financial-modeling/references/models.md)
for input formats and limitations. Canadian income-tax estimates currently
support **Ontario 2026 only**; CPP timing requires a verified age-65 estimate.
These are planning tools, not complete tax-return or statutory pension engines.
