"""Reproducible annual cash-flow scenarios and tax-aware withdrawal schedules."""

from __future__ import annotations

import math
import random
import statistics

from canada import fields, integer, number, rrif_factor, tax_estimate


def percentiles(values):
    ordered = sorted(values)
    result = {}
    for p in (5, 25, 50, 75, 95):
        position = (len(ordered) - 1) * p / 100
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        result[f"p{p}"] = ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
    return result


def summarize(data):
    fields(data, ("values",), ("values",))
    values = data["values"]
    if not isinstance(values, list) or not 2 <= len(values) <= 100000:
        raise ValueError("values requires 2 to 100000 numeric observations")
    values = [number(v, "observation") for v in values]
    return {
        "count": len(values), "mean": statistics.fmean(values),
        "sample_standard_deviation": statistics.stdev(values),
        "minimum": min(values), "maximum": max(values), "percentiles": percentiles(values),
        "limitations": ["Descriptive sample statistics; no distribution, causality or independence inferred."],
    }


def _events(events, horizon_start, horizon_end):
    if not isinstance(events, list):
        raise ValueError("events must be lists")
    result = []
    for event in events:
        fields(event, ("name", "start_age", "end_age", "annual_amount"),
               ("name", "start_age", "end_age", "annual_amount"))
        if not isinstance(event["name"], str) or not event["name"].strip():
            raise ValueError("each event needs a non-empty name")
        start = integer(event["start_age"], "event start_age", horizon_start, horizon_end - 1)
        end = integer(event["end_age"], "event end_age", start, horizon_end - 1)
        amount = number(event["annual_amount"], "event annual_amount", 0)
        result.append((start, end, amount, event["name"]))
    return result


def scenario_inputs(data):
    fields(data, (
        "current_age", "retirement_age", "end_age", "initial_balance", "annual_savings",
        "annual_retirement_spending", "annual_return", "annual_volatility", "annual_fee",
        "inflation", "income_events", "expense_events", "return_path", "trials", "seed",
        "historical_returns", "bootstrap_block_years", "method", "retirement_ages",
    ), ("current_age", "retirement_age", "end_age", "initial_balance", "annual_savings",
        "annual_retirement_spending", "annual_return", "inflation"))
    start = integer(data["current_age"], "current_age", 0, 119)
    end = integer(data["end_age"], "end_age", start + 1, 120)
    retirement = integer(data["retirement_age"], "retirement_age", start, end - 1)
    initial = number(data["initial_balance"], "initial_balance", 0)
    savings = number(data["annual_savings"], "annual_savings", 0)
    spending = number(data["annual_retirement_spending"], "annual_retirement_spending", 0)
    mean = number(data["annual_return"], "annual_return", -.99, 1)
    volatility = number(data.get("annual_volatility", 0), "annual_volatility", 0, 1)
    fee = number(data.get("annual_fee", 0), "annual_fee", 0, .99)
    inflation = number(data["inflation"], "inflation", -.99, 1)
    income = _events(data.get("income_events", []), start, end)
    expenses = _events(data.get("expense_events", []), start, end)
    path = data.get("return_path")
    if path is not None:
        if not isinstance(path, list) or len(path) != end - start:
            raise ValueError("return_path requires exactly one annual nominal return per modeled year")
        path = [number(v, "return_path", -.999999, 10) for v in path]
    return start, retirement, end, initial, savings, spending, mean, volatility, fee, inflation, income, expenses, path


def project(data, returns=None):
    (start, retirement, end, balance, savings, spending, mean, _, fee, inflation,
     income, expenses, explicit_path) = scenario_inputs(data)
    path = returns if returns is not None else explicit_path
    if path is None:
        path = [mean] * (end - start)
    if len(path) != end - start:
        raise ValueError("annual return path must span the complete horizon")
    rows = []
    first_shortfall = None
    total_shortfall = 0.0
    for index, age in enumerate(range(start, end)):
        opening = balance
        contribution = savings if age < retirement else 0
        income_amount = sum(amount for low, high, amount, _ in income if low <= age <= high)
        expense = (spending if age >= retirement else 0) + sum(
            amount for low, high, amount, _ in expenses if low <= age <= high
        )
        available = balance + contribution + income_amount
        shortfall = max(0, expense - available)
        balance = max(0, available - expense)
        nominal = number(path[index], "annual return", -.999999, 1e6)
        real_factor = (1 + nominal) * (1 - fee) / (1 + inflation)
        balance *= real_factor
        if not math.isfinite(balance):
            raise ValueError("projection exceeds finite numeric range")
        if shortfall > 0 and first_shortfall is None:
            first_shortfall = age
        total_shortfall += shortfall
        rows.append({
            "age": age, "opening_real_balance": opening, "real_savings": contribution,
            "real_other_income": income_amount, "real_spending": expense,
            "real_shortfall": shortfall, "nominal_return": nominal,
            "closing_real_balance": balance,
        })
    return {
        "schedule": rows, "terminal_real_balance": balance,
        "success": first_shortfall is None, "first_shortfall_age": first_shortfall,
        "total_real_shortfall": total_shortfall, "assumptions": dict(data),
        "limitations": [
            "Annual beginning-year cash flows; end_age is exclusive. Values are today's purchasing power.",
            "Savings and income events must be after-tax; no tax/account wrappers or contribution room modeled.",
            "Income events are additive to savings; do not include salary already used to derive savings.",
            "Before retirement, annual_savings is net of routine spending; expense_events are incremental.",
            "Constant inflation and fees; longevity is supplied, not predicted. No mortality model.",
            "Success means no spending shortfall in any year, not a guaranteed safe withdrawal rate.",
        ],
    }


def simulate(data):
    (start, retirement, end, _, _, _, mean, volatility, _, _, _, _, path) = scenario_inputs(data)
    if path is not None:
        raise ValueError("use project for an explicit return_path, not simulate")
    trials = integer(data.get("trials", 1000), "trials", 1, 10000)
    seed = integer(data.get("seed", 0), "seed", 0, 2**32 - 1)
    ages = data.get("retirement_ages", [retirement])
    if not isinstance(ages, list) or not ages or len(ages) > 50:
        raise ValueError("retirement_ages requires 1 to 50 unique ages")
    ages = [integer(age, "retirement age", start, end - 1) for age in ages]
    if len(set(ages)) != len(ages):
        raise ValueError("retirement_ages must be unique")
    if trials * (end - start) * len(ages) > 2000000:
        raise ValueError("simulation exceeds 2000000 annual steps; reduce trials or scenarios")
    method = data.get("method", "lognormal")
    if method not in ("lognormal", "bootstrap"):
        raise ValueError("method must be lognormal or bootstrap")
    historical = data.get("historical_returns")
    if method == "bootstrap":
        if not isinstance(historical, list) or len(historical) < 2:
            raise ValueError("bootstrap needs at least two annual historical_returns")
        historical = [number(r, "historical return", -.999999, 10) for r in historical]
        block = integer(data.get("bootstrap_block_years", 1), "bootstrap_block_years", 1, len(historical))
    elif historical is not None or "bootstrap_block_years" in data:
        raise ValueError("historical_returns and bootstrap_block_years require method bootstrap")
    sigma = math.sqrt(math.log1p((volatility / (1 + mean)) ** 2))
    mu = math.log1p(mean) - sigma**2 / 2
    comparisons = []
    for retirement_age in ages:
        rng = random.Random(seed)
        terminals, shortfalls = [], []
        successes = 0
        for _ in range(trials):
            if method == "lognormal":
                returns = [math.expm1(rng.gauss(mu, sigma)) for _ in range(end - start)]
            else:
                returns = []
                while len(returns) < end - start:
                    offset = rng.randrange(len(historical) - block + 1)
                    returns.extend(historical[offset:offset + block])
                returns = returns[:end - start]
            scenario = {**data, "retirement_age": retirement_age}
            result = project(scenario, returns)
            terminals.append(result["terminal_real_balance"])
            shortfalls.append(result["total_real_shortfall"])
            successes += result["success"]
        probability = successes / trials
        z = 1.959963984540054
        denominator = 1 + z*z/trials
        centre = (probability + z*z/(2*trials)) / denominator
        radius = z * math.sqrt(probability*(1-probability)/trials + z*z/(4*trials**2)) / denominator
        comparisons.append({
            "retirement_age": retirement_age, "trials": trials, "successful_paths": successes,
            "conditional_success_rate": probability,
            "simulation_sampling_interval_95": [max(0, centre-radius), min(1, centre+radius)],
            "terminal_real_balance_mean": statistics.fmean(terminals),
            "terminal_real_balance_percentiles": percentiles(terminals),
            "total_real_shortfall_percentiles": percentiles(shortfalls),
            "percentile_population": "all paths, including zero-shortfall successes",
        })
    return {
        "scenarios": comparisons, "seed": seed, "method": method, "assumptions": dict(data),
        "limitations": [
            "Conditional model frequencies, not real-world probabilities or investment advice.",
            "95% Wilson interval measures simulation sampling error only, not model/parameter uncertainty.",
            "Lognormal parameters match supplied nominal arithmetic mean and standard deviation.",
            "Lognormal annual returns are IID; regime shifts, fat tails and changing correlations are absent.",
            "Bootstrap uses contiguous non-wrapping blocks sampled with replacement; short histories "
            "and block choices materially limit conclusions. No automatic historical data source.",
            "Retirement-age comparisons reuse the same seed/paths and initial budget.",
            "Use project for the shared timing, real-dollar and tax limitations.",
        ],
    }


def withdrawals(data):
    fields(data, ("start_age", "end_age", "balances", "taxable_acb", "annual_real_spending",
                  "annual_real_income", "return_path", "inflation", "annual_fee", "strategy",
                  "province", "tax_year"),
           ("start_age", "end_age", "balances", "taxable_acb", "annual_real_spending",
            "annual_real_income", "return_path", "inflation", "strategy", "province", "tax_year"))
    start = integer(data["start_age"], "start_age", 18, 119)
    end = integer(data["end_age"], "end_age", start + 1, 120)
    fields(data["balances"], ("taxable", "tfsa", "rrsp", "rrif"),
           ("taxable", "tfsa", "rrsp", "rrif"))
    balances = {key: number(value, key, 0) for key, value in data["balances"].items()}
    acb = number(data["taxable_acb"], "taxable_acb", 0)
    def amount_path(value, name):
        if isinstance(value, list):
            if len(value) != end - start:
                raise ValueError(f"{name} list must span the complete horizon")
            return [number(item, name, 0) for item in value]
        return [number(value, name, 0)] * (end - start)

    spending_path = amount_path(data["annual_real_spending"], "annual_real_spending")
    income_path = amount_path(data["annual_real_income"], "annual_real_income")
    inflation = number(data["inflation"], "inflation", -.99, 1)
    fee = number(data.get("annual_fee", 0), "annual_fee", 0, .99)
    strategy = data["strategy"]
    if not isinstance(strategy, list) or sorted(strategy) != ["rrif", "rrsp", "taxable", "tfsa"]:
        raise ValueError("strategy must list taxable, tfsa, rrsp and rrif exactly once")
    returns = data["return_path"]
    if not isinstance(returns, list) or len(returns) != end - start:
        raise ValueError("return_path requires one nominal annual return per year")
    returns = [number(value, "return", -.999999, 10) for value in returns]
    tax_base = {"province": data["province"], "tax_year": data["tax_year"]}
    tax_estimate({**tax_base, "ordinary_income": income_path[0]})
    rows = []
    any_shortfall = False
    for index, age in enumerate(range(start, end)):
        income, spending = income_path[index], spending_path[index]
        # RRSP converted by the end of the year turning 71; next Jan 1 has a RRIF minimum.
        if age >= 72:
            balances["rrif"] += balances["rrsp"]
            balances["rrsp"] = 0
        opening = dict(balances)
        mandatory = balances["rrif"] * rrif_factor(age)
        balances["rrif"] -= mandatory
        taken = {key: 0.0 for key in balances}
        taken["rrif"] = mandatory
        realized_gain = 0.0

        def taxes(extra_ordinary=0, extra_gain=0):
            return tax_estimate({
                **tax_base, "ordinary_income": income + taken["rrif"] + taken["rrsp"] + extra_ordinary,
                "capital_gains": realized_gain + extra_gain,
            })["total_income_tax_estimate"]

        cash = income + mandatory
        for account in strategy:
            needed = spending + taxes() - cash
            if needed <= 1e-8:
                break
            available = balances[account]
            gain_fraction = max(0, (available - acb) / available) if account == "taxable" and available else 0

            def net(sale):
                return sale - (taxes(
                    sale if account in ("rrsp", "rrif") else 0,
                    sale * gain_fraction if account == "taxable" else 0,
                ) - taxes())

            if net(available) <= needed:
                sale = available
            else:
                low, high = 0.0, available
                for _ in range(60):
                    middle = (low + high) / 2
                    if net(middle) < needed:
                        low = middle
                    else:
                        high = middle
                sale = high
            if account == "taxable":
                acb -= acb * sale / available if available else 0
                realized_gain += sale * gain_fraction
            balances[account] -= sale
            taken[account] += sale
            cash += sale
        tax = taxes()
        shortfall = max(0, spending + tax - cash)
        surplus = max(0, cash - spending - tax)
        any_shortfall |= shortfall > 1e-6
        # Mandatory withdrawals above spending remain in the household, not lost.
        balances["taxable"] += surplus
        acb += surplus
        real_factor = (1 + returns[index]) * (1 - fee) / (1 + inflation)
        balances = {key: value * real_factor for key, value in balances.items()}
        # ACB is nominal tax cost, expressed in progressively deflated real dollars.
        acb /= 1 + inflation
        if not all(math.isfinite(value) for value in [*balances.values(), acb]):
            raise ValueError("withdrawal projection exceeds finite numeric range")
        rows.append({
            "age_january_1": age, "opening_real_balances": opening,
            "gross_real_withdrawals": taken, "real_income_tax": tax,
            "real_realized_gains": realized_gain, "real_spending": spending,
            "real_surplus_reinvested": surplus, "real_shortfall": shortfall,
            "closing_real_balances": dict(balances), "real_taxable_acb": acb,
        })
    estate_tax = tax_estimate({
        **tax_base, "ordinary_income": balances["rrsp"] + balances["rrif"],
        "capital_gains": max(0, balances["taxable"] - acb),
    })["total_income_tax_estimate"]
    total = sum(balances.values())
    return {
        "schedule": rows, "terminal_real_balances": balances, "terminal_real_taxable_acb": acb,
        "terminal_real_balance_before_estate_tax": total,
        "terminal_real_estate_tax_estimate": estate_tax,
        "terminal_real_after_tax_estate_estimate": total - estate_tax,
        "success": not any_shortfall, "assumptions": dict(data),
        "limitations": [
            "Ontario 2026 simplified tax model only; all its exclusions apply.",
            "Constant-real 2026 tax-system assumption, not forecast future brackets or enacted indexation.",
            "Ages are January 1; end_age exclusive. Beginning-year income/withdrawals, then annual returns.",
            "Other income fully taxable; use an annual list to introduce CPP only from its start age.",
            "Modern RRIF owner-age factors; existing RRIF assumed established before first modeled year.",
            "No LIRA/LIF withdrawals, spouse-age election, withholding/refunds, pension splitting or OAS recovery.",
            "No dividends, taxable distributions, loss deductions, new registered contributions or TFSA-room recycling.",
            "ACB tracked proportionally; aggregate positive gains taxed, losses have no assumed tax benefit.",
            "Terminal estate assumes full deemed disposition/distribution with no spouse rollover, no other "
            "terminal-year income, and the simplified tax credits; not a legal estate calculation.",
        ],
    }
