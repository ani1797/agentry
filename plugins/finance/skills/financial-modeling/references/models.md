# Model contracts

All rates are **decimals** (`0.05`, not `5`), monetary values are in one
user-declared currency, and booleans are not numbers. JSON inputs reject
unknown fields, duplicate keys, non-finite values, and missing required
inputs rather than silently assuming support. Input examples are synthetic.
Tax-specific dollar inputs must be CAD. Do not mix nominal and real data.

Run `python3 scripts/finance_model.py COMMAND INPUT` from this skill's root.
See [setup](getting-started.md), [validation](validation.md), and
[Canadian sources](canadian-rules.md).

## Descriptive statistics

`summarize`: `{"values": [100, 120, 80]}` accepts arbitrary scenario outcomes,
costs, or other numeric observations. Reports sample mean/standard deviation,
range, and interpolated percentiles, not causal or inferential claims.

`analyze FILE.csv [--column return] [--kind returns|prices]
[--periods-per-year 1|12|252|365]` reports arithmetic/geometric annualized
return, sample volatility, drawdown, and individual-period percentiles.
At least two returns are needed. Input CSV has a canonical ISO `date`
column and the selected numeric column, strictly ascending without duplicates.

Annual dates must be contiguous anniversaries, monthly rows consecutive
calendar months, 252-period daily rows consecutive weekdays (no holiday
calendar), and 365-period rows consecutive calendar days. Missing required
observations fail; do not manufacture zero returns to bridge gaps. For
holiday-aware market data, aggregate validated data to months outside the
tool and record the transformation. Price inputs convert consecutive
positive levels to simple returns; the tool does **not** infer that prices
are dividend/split adjusted. Returns <= -100% are unsupported.

## Historical backtesting

`backtest FILE.csv` shares CSV options above and requires `--initial-balance`.
Optional `--annual-cashflow` is positive for deposits and negative for
withdrawals; `--annual-fee`, `--inflation`, and `--rolling-years` control
replay. Default cash flows are fixed **nominal**, split equally per period,
after returns and fees. Nominal balances and a deflated terminal value
are reported. Set `--cashflow-timing beginning --index-cashflow` for
beginning-period, inflation-indexed flows when comparing
real-spending FIRE scenarios, and keep that choice in the run manifest.

Every complete rolling window is replayed with the same initial conditions;
no cherry-picked start dates or fitting on future returns. Overlapping
windows are dependent observations. Sequence, shortfalls, cumulative fees,
contributions, and withdrawals are explicit. No automatic investment
selection, portfolio-weight fitting, FX, transaction costs, or tax model.
For multi-asset replay supply an independently constructed, documented
portfolio total-return series with a stated rebalance convention.

## Cash-flow projection and FIRE

`project` and `simulate` use the fields in
[`fire-example.json`](../assets/fire-example.json).
Required: integer `current_age`, `retirement_age`, exclusive `end_age`,
`initial_balance`, `annual_savings`, `annual_retirement_spending`,
nominal arithmetic `annual_return`, and `inflation`.
Optional `annual_fee` and `annual_volatility` default to zero.

All amounts are **today's purchasing power**, with annual beginning-year
cash flows and nominal investment returns converted using
`(1 + return) * (1 - fee) / (1 + inflation)`. Savings occur only before
retirement and already exclude ordinary living costs and income tax.
Retirement spending starts at retirement. `income_events` and
`expense_events` accept named nonnegative `annual_amount` streams from
`start_age` through inclusive `end_age`; use a single-age event for a lump
sum. Income is additive to savings: do not add salary already used to
derive savings. Income events must be after-tax. Before retirement,
expense events represent costs not already deducted from annual savings.

`project` optionally accepts `return_path`, exactly one nominal annual
return per modeled year. Otherwise it uses the constant nominal arithmetic
return; this is a deterministic illustration, not a median forecast.
No borrowing is assumed when assets run out: each unmet expense is recorded,
and any later recovery does not erase the earlier failure.

`simulate` rejects an explicit path. It accepts `method: "lognormal"` or
`"bootstrap"`, `trials` (default 1000, max 10000), `seed` (default 0), and
`retirement_ages` for comparisons. Lognormal parameters match the supplied
arithmetic mean and standard deviation, **not** the geometric mean.
Bootstrap requires `historical_returns` (annual decimal total returns),
and optional `bootstrap_block_years` (default 1). It draws complete
non-wrapping contiguous blocks with replacement, truncating the last
block at the horizon. Parameters remain in assumptions even if unused.

Retirement-age comparisons share the same seed and paths. Outputs include
conditional success frequencies, terminal/shortfall percentiles, and
95% Wilson intervals for simulation sampling error, **not** model certainty.
Percentiles include **all** paths, including zero-shortfall successes;
they are not conditional on failure. Terminal arithmetic mean is also reported.
There is a 2-million annual-step limit. Run multiple return, spending,
inflation, longevity and bad-early-sequence assumptions; one random seed
or estimated distribution is not a soundness certificate.

## Canadian income-tax estimate

`tax` requires `province: "ON"`, `tax_year: 2026`, and nonnegative
`ordinary_income`. Optional nonnegative `capital_gains` use 50% inclusion;
`rrsp_deduction` reduces taxable income. Optional `net_income` supplies the
distinct BPA means-test base; default is taxable income and a supplied
value cannot be below taxable income in this simplified model.

Includes federal/Ontario brackets, basic personal amounts, federal BPA
phaseout, Ontario basic tax reduction without dependants, surtax, and
health premium. It is **not take-home pay or a complete T1**: excludes
CPP/EI, employment/age/pension/family credits, dividends, AMT, OAS recovery,
benefits, foreign credits, loss deductions and other adjustments.
Unsupported years/provinces and dividend fields fail explicitly. Never
infer RRSP deductibility or contribution room from this calculation.

## CPP timing

`cpp` requires a verified `monthly_at_65` and `start_age_months` (720 to
840). Optional `end_age` defaults to 95, `real_discount_rate` to zero,
and `valuation_age_months` to 720 (age 60). Use the same valuation date and
earnings-history assumption across comparisons. Benefits in today's
dollars get -0.6% per month before 65 or +0.7% afterwards. Outputs include
monthly/annual benefit, cumulative benefits and discounted value.

This deliberately does **not** estimate earned entitlement from years
worked. Official age-65 estimates can assume future earnings: confirm
their assumptions before comparing early retirement. Enhanced CPP is not
subject to the same dropout calculation as base CPP. No tax, survivor,
mortality or post-retirement contribution model is included.

## RESP

`resp` uses the example's `start_age`, annual `contributions`, aggregate
`prior_contributions`, `prior_cesg`, `unused_cesg_room`,
`eligible_at_16_17` boolean, and `available_budget`. Currently only new
plans are accepted (zero prior contributions/grants/balance); historical
CESG room may be supplied for an older beneficiary. Contributions across
all subscribers must not exceed $50,000; overcontribution is an error,
not silently clipped. CESG accrues $500 eligibility room/year to age 17,
pays 20% of contributions up to $1,000 with available carryforward, and
is capped at $7,200 lifetime. Confirm eligibility/residency. Age-16/17
grants also require sufficient contributions before age 16 in the modeled
history; the confirmed flag alone cannot override a missing history.

Optional nominal `annual_return`, `student_effective_tax_rate`, and
`taxable_capital_gains_rate` default to zero. The latter is the **effective
tax rate on a full realized gain**, not the inclusion rate. Beginning-year
contributions/grants earn that year's return.

`available_budget` is available **from day one** for every strategy.
Uncontributed funds stay invested in a taxable account; contributions
liquidate it proportionally with ACB and tax gross-up. An insufficient
outside budget after losses/tax fails. Comparison includes the outside
residual, terminal gain tax, and simplified student EAP tax, so money does
not disappear and grant maximization is not the only metric.

Contributions are not deductible. CLB, additional/provincial grants,
ongoing distributions, fees, non-education/AIP outcomes, rollovers, family
transfers, and detailed payout ordering are not implemented. The simplified
loss allocation is not a grant-repayment quote. Do not advise withdrawals
without confirming promoter rules and the student's income.

## Withdrawal schedules

`withdrawals` requires `province: "ON"`, `tax_year: 2026`, January-1
`start_age`, exclusive `end_age`, `balances` with each of `taxable`, `tfsa`,
`rrsp`, `rrif`, `taxable_acb`, `annual_real_spending`, `annual_real_income`,
`return_path`, `inflation`, and `strategy`. `annual_fee` defaults to zero.
Spending and fully taxable other income can each be a constant or a list
with one value/year, allowing CPP to start later. Pass **gross** CPP here,
unlike the after-tax income events in generic FIRE projections.

Strategy lists all four account names exactly once, in desired withdrawal
order. RRIF minimums always occur first; additional withdrawals are solved
against incremental tax to meet spending. RRSP converts at the start of
the year with January-1 age 72 (after the year turning 71). Modern RRIF
minimums use January-1 owner age; an initial RRIF is assumed already
established. Surplus mandatory withdrawals are reinvested in taxable
assets and increase ACB. Gains use proportional tax basis; no assumed
benefit from capital losses. Returns/fees affect all assets uniformly
after beginning-year withdrawals. Nominal ACB deflates with inflation.

Outputs show each year's gross withdrawals, tax, shortfall, reinvested
surplus, account balances and tax basis, plus an indicative after-tax
estate value. Estate tax assumes full disposition/distribution and no
other terminal-year income or spousal rollover. Compare **after-tax
household wealth plus funded spending**, not just taxes paid.

This uses a constant-real-2026 simplified tax system, **not** legislated
future indexation. Ontario fixed-dollar thresholds would not all track
inflation in reality. Excludes LIRA/LIF maximums/unlocking (jurisdiction
must be verified), spouse-age elections, OAS recovery, pension splitting,
registered contributions, TFSA room recycling, dividends and distributions.
Do not label this globally optimal or a complete Canadian decumulation
model; run multiple explicit orders and review omitted features first.
