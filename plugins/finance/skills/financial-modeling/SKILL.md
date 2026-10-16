---
name: financial-modeling
description: >
  Run reusable offline calculations for user-defined financial scenarios.
  USE FOR: descriptive statistics, historical backtesting, FIRE projections,
  Monte Carlo or block-bootstrap simulations, Canadian tax estimates,
  CPP timing, RESP funding, retirement withdrawal schedules.
  DO NOT USE FOR: executing financial transactions; downloading statements;
  certifying tax returns or guaranteed investment outcomes.
compatibility: Requires Python 3.10+ (standard library only); optional uv. See references/getting-started.md.
license: MIT
---

**WORKFLOW SKILL**

# Financial modeling

Reuse the bundled engine. Examples are synthetic, not history.
Keep personal inputs and outputs outside repositories.

## Steps

1. Confirm jurisdiction, currency, source dates, horizon, timing, and
   nominal/real basis. Follow [contracts](references/models.md) and
   [validation](references/validation.md). Unknown is not zero.
2. Build private scenario JSON or dated returns CSV. Start with a synthetic
   [example](assets/fire-example.json), not historical personal defaults.
3. Run from this skill's root:
   ```bash
   python3 scripts/finance_model.py project /absolute/path/scenario.json
   python3 scripts/finance_model.py simulate /absolute/path/scenario.json
   ```
   Other commands: `summarize`, `analyze`, `backtest`, `tax`, `cpp`,
   `resp`, `withdrawals`. See [contracts](references/models.md).
4. Compare equal budgets, horizons, spending, and tax treatment. Report
   assumptions, paths, hashes, percentiles, shortfalls, sensitivity, and
   limitations. For Canadian rules, check
   [dated sources](references/canadian-rules.md) before relying on them.
   Ontario 2026 is the only implemented income-tax jurisdiction/year.

## Example

"Compare FIRE at 50 versus 55 with a bad early-return sequence, then
backtest the same spending plan." Use `project` and `simulate` with common
paths; disclose historical `backtest` timing. Simulated frequencies
are not guarantees.

## Common issues

Unsupported fields, dates, provinces, gaps, or assumptions fail
explicitly. Historical replay is not a
forecast; CPP uses a verified age-65 estimate, not a reconstructed
entitlement. If a model lacks a required feature, state the limitation
before using it for advice.
