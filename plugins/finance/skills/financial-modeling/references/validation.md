# Evidence and validation protocol

This toolkit generalizes methods from prior financial-planning work:
reconcile the account-level baseline, maintain one assumption set, model
life events, compare FIRE timing and sequence risk, inspect after-tax
withdrawals, and compare education-funding strategies with opportunity cost.
It packages **methods and corrected invariants**, not private facts,
dated personal recommendations, or unverified old scripts.

## Before calculation

1. Confirm ownership and account restrictions. Personal and corporate tax
   liabilities are different; third-party assets do not fund the user's plan.
2. Reconcile positions plus cash to account totals. Mark unknown cost basis,
   missing policy terms, inaccessible data, and unverified contribution room.
3. Set one versioned baseline: spending, household, currency, real/nominal
   basis, cash-flow timing, return assumptions, fees, tax scope and horizon.
4. Confirm data provenance: total versus price return, dividends, splits,
   FX, frequency, unavailable histories, survivorship and selection effects.
   Employer-stock history is not proof that retaining concentration is wise.

## Comparisons and sensitivities

1. Equalize initial household capital, horizon and consumption. Deferred
   contributions remain invested outside a wrapper; surplus withdrawals
   remain in the household. Count tax when funds move and at terminal sale.
2. Use identical random paths for strategy comparisons. Report every complete
   historical window, not only favorable market regimes; distinguish historical
   frequencies, simulated frequencies and uncertainty about future parameters.
3. Vary spending, inflation, fees, returns, volatility, life-event timing,
   longevity and adverse early returns. A fixed 4% rule is not a guarantee.
4. Validate account access before FIRE: taxable/TFSA/RRSP bridge funding,
   locked-in restrictions and pension start dates cannot be replaced by total
   net worth. Generic FIRE lacks these constraints; follow with withdrawals.
5. Compare after-tax estate **and funded spending**, not lifetime tax alone.
   Demand a new verified CPP estimate if changing future contributions; base
   and enhanced CPP cannot share a crude dropout approximation.
6. Compare RESP tax shelter, grants, student tax and outside-account
   opportunity cost. Contributions are not deductible and child nonattendance
   is a separate risk, not modeled as a free refund.
7. After an input correction, invalidate dependent recommendations and rerun
   every affected model. Never mix an old spending baseline with a new one.

## Reproducibility and acceptance

Keep private inputs, source dates, complete command, output JSON, input
hash, tool version, seed, trial count and baseline ID together outside the
plugin. Review explicit omissions before interpreting results.

Run the synthetic regression suite:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

It checks analytical compounding, spending shortfalls, seeded repeatability,
lognormal parameterization, real/nominal consistency, equal-budget RESP
comparisons, tax/pension/withdrawal boundaries, conserved surplus wealth,
complete rolling windows, data validation and CLI failure behavior.

Tests do not certify advice or a complete tax return. If a requested
scenario cannot be represented, name the missing feature. Do not invent a
one-off untested script, silently omit the feature, or present a simplified
result as comprehensive.

Waza suites live inside each skill's `evals/`; pass the eval path explicitly
to `waza spec verify`. Waza 0.38.7 incorrectly warns that the
`compatibility` frontmatter must be a mapping and may miss nested eval
discovery. The current Agent Skills specification requires a **string**;
retain the valid string rather than changing the skill to satisfy that
validator bug. Runtime suites must execute in an isolated copy with no
live Git remote and must never sign in, retrieve credentials, or download
real statements.
