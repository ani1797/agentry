"""Dated Canadian planning calculations, not a tax return or benefit estimator."""

from __future__ import annotations

import math


CHECKED = "2026-10-16"
TAX_SOURCE = (
    "https://www.canada.ca/en/revenue-agency/services/forms-publications/payroll/"
    "t4127-payroll-deductions-formulas/t4127-jul/"
    "t4127-jul-payroll-deductions-formulas.html"
)
CPP_SOURCE = "https://www.canada.ca/en/services/benefits/publicpensions/cpp/when-start.html"
RESP_SOURCE = "https://www.canada.ca/en/services/benefits/education/education-savings/estimating-amounts.html"
RRIF_SOURCE = (
    "https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/"
    "completing-slips-summaries/t4rsp-t4rif-information-returns/payments/"
    "chart-prescribed-factors.html"
)
RRIF_FACTORS = [
    .0528, .0540, .0553, .0567, .0582, .0598, .0617, .0636,
    .0658, .0682, .0708, .0738, .0771, .0808, .0851, .0899,
    .0955, .1021, .1099, .1192, .1306, .1449, .1634, .1879, .20,
]


def number(value, name, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} is outside the numeric range") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    if minimum is not None and result < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    if maximum is not None and result > maximum:
        raise ValueError(f"{name} must be at most {maximum}")
    return result


def integer(value, name, minimum=0, maximum=150):
    number(value, name, minimum, maximum)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    return value


def fields(data, allowed, required=()):
    if not isinstance(data, dict):
        raise ValueError("input must be a JSON object")
    unknown = data.keys() - set(allowed)
    missing = set(required) - data.keys()
    if unknown:
        raise ValueError(f"unsupported input fields: {', '.join(sorted(unknown))}")
    if missing:
        raise ValueError(f"required input fields: {', '.join(sorted(missing))}")


def progressive(income, boundaries, rates):
    total = lower = 0.0
    for upper, rate in zip([*boundaries, math.inf], rates):
        total += max(0, min(income, upper) - lower) * rate
        lower = upper
    return total


def ontario_health_premium(income):
    for threshold, base, rate, cap in (
        (200000, 750, .25, 900), (72000, 600, .25, 750),
        (48000, 450, .25, 600), (36000, 300, .06, 450),
        (20000, 0, .06, 300),
    ):
        if income > threshold:
            return min(cap, base + rate * (income - threshold))
    return 0.0


def tax_estimate(data):
    fields(data, ("province", "tax_year", "ordinary_income", "capital_gains",
                  "rrsp_deduction", "net_income"),
           ("province", "tax_year", "ordinary_income"))
    if data["province"] != "ON" or integer(data["tax_year"], "tax_year", 2026, 2026) != 2026:
        raise ValueError("only Ontario (ON), tax year 2026 is supported; no fallback")
    ordinary = number(data["ordinary_income"], "ordinary_income", 0)
    gains = number(data.get("capital_gains", 0), "capital_gains", 0)
    deduction = number(data.get("rrsp_deduction", 0), "rrsp_deduction", 0)
    taxable = number(max(0, ordinary + gains * .5 - deduction), "taxable_income", 0)
    net = number(data.get("net_income", taxable), "net_income", taxable)
    reduction = min(1, max(0, (net - 181440) / (258482 - 181440)))
    federal_bpa = 16452 - (16452 - 14829) * reduction
    federal = max(0, progressive(
        taxable, [58523, 117045, 181440, 258482], [.14, .205, .26, .29, .33]
    ) - federal_bpa * .14)
    ontario = max(0, progressive(
        taxable, [53891, 107785, 150000, 220000], [.0505, .0915, .1116, .1216, .1316]
    ) - 12989 * .0505)
    surtax = max(0, ontario - 5818) * .2 + max(0, ontario - 7446) * .36
    # Basic Ontario tax reduction only; dependants require a fuller T1 model.
    ontario_reduction = max(0, min(ontario + surtax, 600 - (ontario + surtax)))
    premium = ontario_health_premium(taxable)
    total = federal + ontario + surtax - ontario_reduction + premium
    return {
        "province": "ON", "tax_year": 2026, "taxable_income": taxable,
        "net_income_for_bpa": net, "capital_gains_inclusion": .5,
        "federal_basic_personal_amount": federal_bpa, "federal": federal,
        "ontario_before_surtax": ontario, "ontario_surtax": surtax,
        "ontario_basic_reduction": ontario_reduction, "health_premium": premium,
        "total_income_tax_estimate": total,
        "source": TAX_SOURCE, "checked": CHECKED,
        "limitations": [
            "Planning estimate for ordinary income and non-negative realized capital gains only.",
            "Not payroll take-home or a T1: excludes CPP/EI contributions and credits, "
            "employment/age/pension/spousal/disability credits, dividends, AMT, OAS recovery, "
            "benefits, foreign tax credits, loss carryovers and other deductions.",
            "RRSP deduction is supplied by the user; eligibility and contribution room are not inferred.",
            "Net income defaults to taxable income; supply net_income if they differ.",
        ],
    }


def cpp_timing(data):
    fields(data, ("monthly_at_65", "start_age_months", "end_age", "real_discount_rate",
                  "valuation_age_months"),
           ("monthly_at_65", "start_age_months"))
    baseline = number(data["monthly_at_65"], "monthly_at_65", 0)
    start = integer(data["start_age_months"], "start_age_months", 720, 840)
    end = integer(data.get("end_age", 95), "end_age", 60, 120) * 12
    if end <= start:
        raise ValueError("end_age must be after the CPP start age")
    valuation = integer(data.get("valuation_age_months", 720), "valuation_age_months", 0, start)
    discount = number(data.get("real_discount_rate", 0), "real_discount_rate", -.99, 1)
    months = start - 780
    factor = 1 + months * (.006 if months < 0 else .007)
    monthly = baseline * factor
    present_value = sum(
        monthly / (1 + discount) ** ((month + 1 - valuation) / 12)
        for month in range(start, end)
    )
    return {
        "start_age_months": start, "monthly_real_benefit": monthly,
        "annual_real_benefit": monthly * 12, "age_adjustment": factor,
        "cumulative_real_benefits": monthly * (end - start),
        "present_value": present_value, "valuation_age_months": valuation,
        "real_discount_rate": discount, "end_age": end / 12,
        "source": CPP_SOURCE, "checked": CHECKED,
        "limitations": [
            "User must supply a verified age-65 estimate in today's dollars for the same earnings history.",
            "Age adjustment only: not a statutory entitlement model. Changing retirement/contribution "
            "dates needs new estimates; base/enhanced CPP dropouts and post-retirement benefits differ.",
            "Assumes CPI-indexed payments; excludes tax, mortality and survivor benefits.",
            "Present values use valuation_age_months (default age 60); use the same date for comparisons.",
        ],
    }


def rrif_factor(age):
    age = integer(age, "RRIF factor age on January 1", 0, 120)
    return 1 / (90 - age) if age <= 70 else RRIF_FACTORS[min(age, 95) - 71]


def resp_schedule(data):
    fields(data, ("start_age", "contributions", "initial_balance", "prior_contributions",
                  "prior_cesg", "unused_cesg_room", "eligible_at_16_17", "annual_return",
                  "student_effective_tax_rate", "taxable_capital_gains_rate", "available_budget"),
           ("start_age", "contributions", "prior_contributions", "prior_cesg",
            "unused_cesg_room", "eligible_at_16_17", "available_budget"))
    start = integer(data["start_age"], "start_age", 0, 30)
    schedule = data["contributions"]
    if not isinstance(schedule, list) or not 1 <= len(schedule) <= 31 - start:
        raise ValueError("contributions must be a non-empty annual list ending by age 30")
    contributions = [number(v, "contribution", 0) for v in schedule]
    prior = number(data["prior_contributions"], "prior_contributions", 0, 50000)
    cesg = number(data["prior_cesg"], "prior_cesg", 0, 7200)
    room = number(data["unused_cesg_room"], "unused_cesg_room", 0, 9000)
    if room > min(start, 18) * 500:
        raise ValueError("unused_cesg_room exceeds the maximum accrued before start_age")
    if not isinstance(data["eligible_at_16_17"], bool):
        raise ValueError("eligible_at_16_17 must be a confirmed boolean")
    if prior + sum(contributions) > 50000:
        raise ValueError("aggregate contributions across all RESPs exceed the $50,000 lifetime cap")
    balance = number(data.get("initial_balance", 0), "initial_balance", 0)
    if prior != 0 or cesg != 0 or balance != 0:
        raise ValueError("RESP comparison currently requires a new plan; existing-plan histories "
                         "need contribution, grant, withdrawal and loss allocation reconciliation")
    budget = number(data["available_budget"], "available_budget", sum(contributions))
    rate = number(data.get("annual_return", 0), "annual_return", -.99, 1)
    student_tax = number(data.get("student_effective_tax_rate", 0),
                         "student_effective_tax_rate", 0, 1)
    capital_tax = number(data.get("taxable_capital_gains_rate", 0),
                         "taxable_capital_gains_rate", 0, 1)
    residual = taxable_alternative = budget
    outside_acb = budget
    rows = []
    grant_total = 0.0
    transfer_tax = 0.0
    for index, contribution in enumerate(contributions):
        age = start + index
        if age <= 17:
            room += 500
        history = contributions[:max(0, 16 - start)]
        history_eligible = sum(history) >= 2000 or sum(v >= 100 for v in history) >= 4
        eligible = age <= 15 or (
            age <= 17 and data["eligible_at_16_17"] and history_eligible
        )
        grant = min(contribution * .2, room, 1000, 7200 - cesg) if eligible else 0
        room -= grant
        cesg += grant
        grant_total += grant
        # Same starting household budget: deferred contributions remain invested outside.
        gain_fraction = max(0, (residual - outside_acb) / residual) if residual else 0
        sale = contribution / (1 - gain_fraction * capital_tax)
        if sale > residual + 1e-8:
            raise ValueError(f"outside budget cannot fund contribution and tax at age {age}")
        acb_sold = outside_acb * sale / residual if residual else 0
        outside_acb -= acb_sold
        transfer_tax += sale - contribution
        residual = max(0, residual - sale)
        balance = (balance + contribution + grant) * (1 + rate)
        residual *= 1 + rate
        taxable_alternative *= 1 + rate
        rows.append({"age": age, "contribution": contribution, "basic_cesg": grant,
                     "cesg_lifetime": cesg, "unused_cesg_room": room,
                     "resp_balance": balance, "outside_balance": residual,
                     "outside_acb": outside_acb, "cumulative_transfer_tax": transfer_tax})
    principal = min(sum(contributions), balance)
    eap = max(0, balance - principal)
    outside_net = residual - max(0, residual - outside_acb) * capital_tax
    resp_net = principal + eap * (1 - student_tax)
    taxable_net = taxable_alternative - max(0, taxable_alternative - budget) * capital_tax
    return {
        "schedule": rows, "total_contributions": sum(contributions),
        "total_basic_cesg": grant_total, "contribution_tax_deduction": 0,
        "resp_terminal_balance": balance,
        "education_spendable_estimate": resp_net,
        "household_with_resp_after_tax": resp_net + outside_net,
        "same_budget_taxable_after_tax": taxable_net,
        "household_advantage_estimate": resp_net + outside_net - taxable_net,
        "outside_transfer_tax": transfer_tax,
        "assumptions": dict(data), "source": RESP_SOURCE, "checked": CHECKED,
        "limitations": [
            "One new-plan beneficiary; confirm Canadian eligibility each year and aggregate all subscribers.",
            "Basic CESG only; additional income-tested grants, CLB and provincial grants excluded.",
            "Confirm age-16/17 contribution-history eligibility; not inferred from current balance.",
            "Annual beginning-year contributions/grants, constant nominal return; all budget available now.",
            "Unused budget stays invested; taxable alternative uses identical initial budget and return.",
            "Simplified terminal EAP tax rate, no annual taxable distributions, fees or interim withdrawals.",
            "Losses allocate to principal first for this estimate, not provider payout or grant repayment rules.",
            "Non-education/AIP outcomes, family-plan transfers and RRSP rollovers require separate analysis.",
        ],
    }
