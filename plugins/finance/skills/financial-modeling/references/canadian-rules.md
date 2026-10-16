# Canadian rule provenance and scope

Rules checked **2026-10-16**. Recheck primary sources at advice time; an
old source date is not proof of current law. Future inflation, rates and
benefits are assumptions, not newly enacted rules.

## Income tax: Ontario 2026 only

CRA [T4127 January full formulas](https://www.canada.ca/en/revenue-agency/services/forms-publications/payroll/t4127-payroll-deductions-formulas/t4127-jan/t4127-jan-payroll-deductions-formulas-computer-programs.html)
and [July update](https://www.canada.ca/en/revenue-agency/services/forms-publications/payroll/t4127-payroll-deductions-formulas/t4127-jul/t4127-jul-payroll-deductions-formulas.html)
provide federal BPA, Ontario reduction/premium formulas, and brackets.
Use annual rates, not prorated second-half withholding rates.
Official [rates CSV](https://www.canada.ca/content/dam/cra-arc/formspubs/pub/t4127-jul/rates-income-thresholds-constants-26e.csv)
and [other amounts CSV](https://www.canada.ca/content/dam/cra-arc/formspubs/pub/t4127-jul/other-rates-amounts-26e.csv)
give the dated thresholds.

Federal thresholds: 58,523 / 117,045 / 181,440 / 258,482;
rates: 14% / 20.5% / 26% / 29% / 33%.
BPA: 16,452, linearly reduced to 14,829 over net income
181,440 to 258,482. Ontario thresholds: 53,891 / 107,785 /
150,000 / 220,000; rates: 5.05% / 9.15% / 11.16% / 12.16% /
13.16%; BPA 12,989. Ontario surtax: 20% above basic tax 5,818,
plus 36% above 7,446. Basic tax-reduction amount 300, with
dependant enhancements excluded. Health premium follows the official
piecewise formula independently of the reduction.

Capital gains inclusion is modeled as one-half; see
[CRA's inclusion-rate update](https://www.canada.ca/en/revenue-agency/news/newsroom/tax-tips/tax-tips-2025/update-canada-revenue-agency-administration-proposed-capital-gains-taxation-changes.html).
This is a planning subset, not an implementation of payroll or all T1
provisions. Its omissions matter for low incomes, retirees, dividend
portfolios, high incomes subject to AMT, and OAS recipients.

## CPP

[Service Canada start-age adjustments](https://www.canada.ca/en/services/benefits/publicpensions/cpp/when-start.html):
0.6% reduction/month before 65 to 60; 0.7% increase/month
after 65 to 70. The engine requires the user's verified age-65
entitlement estimate and never copies a maximum or average benefit
into personal projections. Changing the retirement date can change the
underlying entitlement independently of these timing factors.

## RESP / CESG

[ESDC amounts and eligibility](https://www.canada.ca/en/services/benefits/education/education-savings/estimating-amounts.html)
and [CRA contribution rules](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/registered-education-savings-plans-resps/resp-contributions.html):
$50,000 lifetime contributions across all subscribers; contributions
are not deductible. Basic CESG pays 20% up to $500/year, or
$1,000 with unused room, capped at $7,200 lifetime through the
year turning 17. Before the end of the year turning 15, age-16/17
eligibility requires at least $2,000 contributed and not withdrawn,
or $100 in each of four years. Grant timing is calendar-year based.
The model excludes additional/provincial grants and non-education payouts.

## RRIF

[CRA prescribed factor table](https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/completing-slips-summaries/t4rsp-t4rif-information-returns/payments/chart-prescribed-factors.html):
modern RRIF factors, 1/(90-age) through age 70; 5.28% at 71,
5.40% at 72, increasing to 20% at 95+. Age is at January 1.
[CRA RRIF minimum guidance](https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/completing-slips-summaries/t4rsp-t4rif-information-returns/payments/minimum-amount-a-rrif.html)
describes owner/spouse elections; only owner-age factors are implemented.
The first-year RRIF exception is not inferred for an input RRIF:
initial balances must represent a previously established RRIF.

## Explicitly not bundled as authoritative models

Corporate planning, CPP contribution-history entitlement, OAS/GIS,
LIRA/LIF maximums/unlocking, RESP non-education outcomes, and
full provincial tax systems require their own verified inputs and
calculation tests. Do not fill these gaps with remembered rules or
the user's older planning conclusions.
