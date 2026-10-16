---
name: financial-baseline
description: >
  Build and reconcile a reusable local financial-planning baseline.
  USE FOR: documenting a financial profile, consolidating account ownership,
  holdings, liabilities, benefits, cost basis, reconciling statement
  coverage, revising shared planning assumptions.
  DO NOT USE FOR: signing into financial portals; executing transactions;
  running statistical simulations or certifying tax filings.
license: MIT
---

**WORKFLOW SKILL**

# Financial baseline

Create only user-authorized local artifacts outside repositories; never
package private profiles with this plugin.

## Steps

1. Confirm a private output path and sources the user authorizes reading.
   Use the [baseline template](assets/baseline-template.md); ask only
   decision-critical questions. Existing facts require date confirmation.
2. Record jurisdiction/currency, household, income, spending, goals,
   risk capacity, ownership, account wrappers, holdings, debts, benefit
   terms, tax cost basis, and verified contribution room. Keep unknowns
   explicit. Do not request full identifiers or credentials.
3. Reconcile institution totals against account balances and position
   values plus cash. Separate personal, corporate, joint, and third-party
   money. Flag price dates, FX assumptions, missing holdings, duplicates,
   and pending transactions. Never infer ACB from market value.
4. Reconcile cash flow without double-counting internal transfers,
   credit-card repayments, gross/net compensation, or reinvested income.
   Capture unresolved discrepancies rather than inventing balancing entries.
5. Assign one versioned assumption set to all models. When it changes,
   mark dependent advice stale and rerun relevant `financial-modeling`
   scenarios. Keep a correction log; never silently mix versions.

## Example

"Consolidate these statements and revise the spending assumption used
across my FIRE and withdrawal plans." Produce the reconciled baseline,
assumption revision, open questions, and list of models needing reruns.

## Common issues

Statements are not always current balances or complete holdings. Unseen
insurance terms and contribution room stay unknown. Do not assume a
budgeting service, ledger, or knowledge vault is running: use the user's
existing preferred format and link to it instead of creating conflicting
systems of record. Downloads belong to `financial-statements`; simulations
belong to `financial-modeling`.
