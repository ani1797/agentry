"""Descriptive statistics and deterministic, cash-flow-aware historical replay.

Returns are decimal simple returns, not percentages. Supply chronological,
regularly spaced observations; no prices, data downloads, forecasts, risk-free
rate, or tax rules are inferred. CSV loading defaults to contiguous annual
observations; pass periods_per_year=12, 252, or 365 for other supported cadences.
The 252 convention requires consecutive weekdays, without a holiday calendar.
Price inputs are unadjusted price returns unless the caller independently
confirms that the supplied levels include distributions and corporate actions.
"""

from __future__ import annotations

import calendar
import csv
from datetime import date, timedelta
import math
from numbers import Real
import statistics


MAX_OBSERVATIONS = 100_000
MAX_ROLLING_PERIODS = 1_000_000

CAVEATS = [
    "Historical descriptive results are not forecasts or confidence intervals.",
    "Inputs must be chronological, regularly spaced decimal simple returns; "
    "array inputs have no dates with which to verify cadence.",
    "Use total-return inputs including distributions for an investment replay; "
    "price-only inputs omit distributions unless independently confirmed adjusted.",
    "Survivorship bias, look-ahead bias, selection bias, and missing history "
    "are not corrected.",
    "Taxes, foreign-exchange effects, trading costs, and cash drag are not modeled "
    "unless already reflected in the supplied returns.",
    "Inflation and fees, when supplied, are constant annual effective rates.",
]


def _number(value: Real, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite real number, not a bool")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{name} is outside the supported numeric range") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _finite(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("Calculation exceeds the supported finite numeric range")
    return value


def _periods(periods_per_year: int) -> int:
    if (isinstance(periods_per_year, bool)
            or not isinstance(periods_per_year, int) or periods_per_year <= 0):
        raise ValueError("periods_per_year must be a positive integer")
    return periods_per_year


def _returns(values: list[float], minimum: int = 1) -> list[float]:
    if not isinstance(values, (list, tuple)):
        raise ValueError("returns must be a list or tuple")
    if not minimum <= len(values) <= MAX_OBSERVATIONS:
        raise ValueError(
            f"returns require {minimum} to {MAX_OBSERVATIONS} observations"
        )
    result = [_number(value, f"return[{i}]") for i, value in enumerate(values)]
    if any(value <= -1 for value in result):
        raise ValueError("each simple return must be greater than -1")
    return result


def _exp(value: float) -> float:
    try:
        return _finite(math.exp(value))
    except OverflowError as exc:
        raise ValueError("Calculation exceeds the supported numeric range") from exc


def _percentiles(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    result = {}
    for percentile in (5, 25, 50, 75, 95):
        position = (len(ordered) - 1) * percentile / 100
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        weight = position - lower
        result[f"p{percentile}"] = _finite(
            ordered[lower] * (1 - weight) + ordered[upper] * weight
        )
    return result


def analyze(values: list[float], periods_per_year: int = 1) -> dict:
    """Describe at least two returns; drawdown includes initial wealth of one.

    Volatility is sample standard deviation (n-1), annualized by sqrt(periods).
    Percentiles use linear interpolation and describe individual period returns,
    not annual returns or confidence intervals. Annualization assumes regular
    periods; sqrt-time volatility scaling is a convention, not an IID guarantee.
    """
    periods = _periods(periods_per_year)
    returns = _returns(values, minimum=2)
    try:
        arithmetic = _finite(statistics.fmean(returns) * periods)
        volatility = _finite(statistics.stdev(returns))
        geometric = _finite(math.expm1(
            statistics.fmean([math.log1p(value) for value in returns]) * periods
        ))
        annualized_volatility = _finite(volatility * math.sqrt(periods))
    except (OverflowError, statistics.StatisticsError) as exc:
        raise ValueError("Statistics exceed the supported numeric range") from exc
    log_wealth = peak = max_drawdown = 0.0
    for value in returns:
        log_wealth = _finite(log_wealth + math.log1p(value))
        peak = max(peak, log_wealth)
        max_drawdown = max(max_drawdown, -math.expm1(log_wealth - peak))
    return {
        "n": len(returns),
        "periods_per_year": periods,
        "years": len(returns) / periods,
        "arithmetic_annualized_return": arithmetic,
        "geometric_annualized_return": geometric,
        "sample_volatility": volatility,
        "annualized_volatility": annualized_volatility,
        "median": statistics.median(returns),
        "percentiles": _percentiles(returns),
        "worst_period": min(returns),
        "best_period": max(returns),
        "max_drawdown": max_drawdown,
        "percentile_method": "linear interpolation at (n - 1) * percentile",
        "caveats": CAVEATS + [
            "Annualized volatility uses square-root-of-time scaling; serial "
            "correlation can invalidate this convention."
        ],
    }


def _check_cadence(dates: list[date], periods: int) -> None:
    if periods == 252 and any(day.weekday() >= 5 for day in dates):
        raise ValueError("252-period cadence requires weekday dates")
    for previous, current in zip(dates, dates[1:]):
        if periods == 1:
            anchor = dates[0]
            day = min(anchor.day, calendar.monthrange(current.year, anchor.month)[1])
            valid = (
                current.year == previous.year + 1
                and current.month == anchor.month and current.day == day
            )
        elif periods == 12:
            valid = (
                current.year * 12 + current.month
                == previous.year * 12 + previous.month + 1
            )
        else:
            expected = previous + timedelta(days=1)
            if periods == 252:
                while expected.weekday() >= 5:
                    expected += timedelta(days=1)
            valid = current == expected
        if not valid:
            raise ValueError(
                f"Date gap or inconsistent cadence between {previous} and {current}"
            )


def load_returns(
    path: str, column: str = "return", kind: str = "returns",
    *, periods_per_year: int = 1,
) -> list[float]:
    """Load a CSV with a ``date`` and selected numeric column.

    Dates must be unique, strictly ascending canonical ISO YYYY-MM-DD. Supported
    cadences: 1 (same annual anniversary), 12 (consecutive calendar months),
    252 (consecutive weekdays, no holiday exceptions), 365 (calendar days).
    Monthly spacing is by year/month, not identical day-of-month. Leap days
    remain observations under the 365 annualization convention. Cadence cannot
    be checked for a one-row return file. Price files need at least two rows;
    the first price is a base level, not an invented return observation.
    """
    periods = _periods(periods_per_year)
    if periods not in (1, 12, 252, 365):
        raise ValueError("CSV cadence supports periods_per_year of 1, 12, 252, or 365")
    if kind not in ("returns", "prices"):
        raise ValueError("kind must be 'returns' or 'prices'")
    if not isinstance(column, str) or not column or column == "date":
        raise ValueError("column must name a numeric column other than 'date'")
    dates = []
    values = []
    with open(path, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        if (not fields or len(fields) != len(set(fields))
                or "date" not in fields or column not in fields):
            raise ValueError("CSV requires unique headers including date and column")
        for row_number, row in enumerate(reader, start=2):
            if len(values) >= MAX_OBSERVATIONS:
                raise ValueError(f"CSV exceeds {MAX_OBSERVATIONS} observations")
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Malformed CSV row {row_number}")
            try:
                day = date.fromisoformat(row["date"])
                if day.isoformat() != row["date"]:
                    raise ValueError("Use canonical YYYY-MM-DD dates")
                value = float(row[column])
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError(f"Invalid date or number on CSV row {row_number}") from exc
            value = _number(value, f"CSV row {row_number}")
            if dates and day <= dates[-1]:
                raise ValueError("CSV dates must be strictly ascending and unique")
            if (kind == "prices" and value <= 0) or (kind == "returns" and value <= -1):
                raise ValueError("Prices must be positive; returns must be greater than -1")
            dates.append(day)
            values.append(value)
    if not values or (kind == "prices" and len(values) < 2):
        raise ValueError("CSV needs returns, or at least two price observations")
    _check_cadence(dates, periods)
    if kind == "prices":
        return _returns([
            _finite(current / previous - 1)
            for previous, current in zip(values, values[1:])
        ])
    return values


def _apply_return_and_fee(
    balance: float, period_return: float, fee_factor: float,
) -> tuple[float, float]:
    gross = _finite(balance * (1 + period_return))
    closing = _finite(gross * fee_factor)
    return closing, _finite(gross - closing)


def _replay(
    returns: list[float], initial: float, cashflow: float,
    fee_factor: float, inflation: float, periods: int, *, history: bool,
    cashflow_timing: str, cashflow_inflation_indexed: bool,
) -> dict:
    balance = initial
    contributions = withdrawals = requested_withdrawals = shortfalls = fees = 0.0
    first_shortfall = None
    balances = [initial] if history else None
    period_results = [] if history else None
    for index, period_return in enumerate(returns):
        opening = balance
        period_cashflow = cashflow
        if cashflow_inflation_indexed and index and cashflow:
            period_cashflow = _finite(
                cashflow * _exp(math.log1p(inflation) * (index / periods))
            )
        if cashflow_timing == "end":
            balance, fee = _apply_return_and_fee(balance, period_return, fee_factor)
        shortfall = 0.0
        if period_cashflow >= 0:
            actual_cashflow = period_cashflow
            contributions = _finite(contributions + period_cashflow)
            balance = _finite(balance + period_cashflow)
        else:
            requested = -period_cashflow
            paid = min(balance, requested)
            actual_cashflow = -paid
            shortfall = requested - paid
            withdrawals = _finite(withdrawals + paid)
            requested_withdrawals = _finite(requested_withdrawals + requested)
            shortfalls = _finite(shortfalls + shortfall)
            balance -= paid
            if shortfall > 0 and first_shortfall is None:
                first_shortfall = index
        if cashflow_timing == "beginning":
            balance, fee = _apply_return_and_fee(balance, period_return, fee_factor)
        fees = _finite(fees + fee)
        if history:
            balances.append(balance)
            period_results.append({
                "period_index": index,
                "opening_balance": opening,
                "return": period_return,
                "fee": fee,
                "requested_cashflow": period_cashflow,
                "actual_cashflow": actual_cashflow,
                "shortfall": shortfall,
                "closing_balance": balance,
            })
    # Log-space discounting avoids an overflowing inflation deflator.
    real_balance = (
        _exp(math.log(balance) - math.log1p(inflation) * (len(returns) / periods))
        if balance > 0 else 0.0
    )
    result = {
        "n": len(returns),
        "years": len(returns) / periods,
        "terminal_balance": balance,
        "real_terminal_balance": real_balance,
        "initial_balance": initial,
        "total_period_contributions": contributions,
        "total_contributions": _finite(initial + contributions),
        "total_withdrawals": withdrawals,
        "total_requested_withdrawals": requested_withdrawals,
        "total_shortfall": shortfalls,
        "total_fees": fees,
        "success": first_shortfall is None,
        "first_shortfall_period": first_shortfall,
        "depleted": balance == 0,
    }
    if history:
        result.update({"balances": balances, "period_results": period_results})
    return result


def backtest(
    returns: list[float], initial_balance: float, annual_cashflow: float = 0,
    periods_per_year: int = 1, annual_fee: float = 0, inflation: float = 0,
    rolling_years: int | None = None,
    *, cashflow_timing: str = "end", cashflow_inflation_indexed: bool = False,
) -> dict:
    """Replay returns in supplied order, without optimization or look-ahead.

    Each period applies the return and then a multiplicative fee. Cash flow
    occurs before both with timing="beginning", or after both with timing="end".
    Positive cash flow contributes; negative cash flow requests a withdrawal.
    Withdrawals use available assets only: unpaid amounts are explicit shortfalls,
    not borrowing or clipped returns. Success means no withdrawal shortfall, not
    a guaranteed sustainable plan. Annual cash flow is split equally across
    periods and defaults to constant nominal amounts. When inflation-indexed,
    period i requests (annual_cashflow / periods_per_year) times
    (1 + inflation) ** (i / periods_per_year), starting with i=0 for either
    timing convention. No terminal liquidation tax is applied. Rolling windows
    reset all assumptions, including inflation indexing, and include every
    complete window.
    """
    periods = _periods(periods_per_year)
    values = _returns(returns)
    initial = _number(initial_balance, "initial_balance")
    annual_flow = _number(annual_cashflow, "annual_cashflow")
    fee = _number(annual_fee, "annual_fee")
    inflation = _number(inflation, "inflation")
    if initial < 0:
        raise ValueError("initial_balance must be nonnegative")
    if not 0 <= fee < 1:
        raise ValueError("annual_fee must be in [0, 1)")
    if inflation <= -1:
        raise ValueError("inflation must be greater than -1")
    if not isinstance(cashflow_timing, str) or cashflow_timing not in ("beginning", "end"):
        raise ValueError("cashflow_timing must be 'beginning' or 'end'")
    if not isinstance(cashflow_inflation_indexed, bool):
        raise ValueError("cashflow_inflation_indexed must be a bool")
    window = None
    if rolling_years is not None:
        if (isinstance(rolling_years, bool) or not isinstance(rolling_years, int)
                or rolling_years <= 0):
            raise ValueError("rolling_years must be a positive integer")
        window = rolling_years * periods
        if window > len(values):
            raise ValueError("rolling window exceeds supplied history")
        if window * (len(values) - window + 1) > MAX_ROLLING_PERIODS:
            raise ValueError(f"Rolling replay exceeds {MAX_ROLLING_PERIODS} period steps")
    factor = _exp(math.log1p(-fee) / periods)
    cashflow = annual_flow / periods
    result = _replay(
        values, initial, cashflow, factor, inflation, periods, history=True,
        cashflow_timing=cashflow_timing,
        cashflow_inflation_indexed=cashflow_inflation_indexed,
    )
    result.update({
        "periods_per_year": periods,
        "assumptions": {
            "cashflow_timing": (
                "end of period, after return and fee" if cashflow_timing == "end"
                else "beginning of period, before return and fee"
            ),
            "annual_cashflow": annual_flow,
            "period_cashflow": cashflow,
            "cashflow_inflation_indexed": cashflow_inflation_indexed,
            "cashflow_indexing": (
                "base period cashflow * (1 + annual_inflation) ** "
                "(zero-based period_index / periods_per_year)"
                if cashflow_inflation_indexed else "constant nominal cashflow"
            ),
            "annual_fee": fee,
            "period_fee_factor": factor,
            "annual_inflation": inflation,
            "shortfall_policy": "pay available assets; record unmet withdrawals; no debt",
            "success_definition": "no unmet requested withdrawals",
        },
        "caveats": CAVEATS + [
            "Overlapping rolling windows are dependent observations, not independent "
            "trials or estimates of future success probability."
        ],
    })
    if window is not None:
        windows = []
        for start in range(len(values) - window + 1):
            replay = _replay(
                values[start:start + window], initial, cashflow, factor,
                inflation, periods, history=False,
                cashflow_timing=cashflow_timing,
                cashflow_inflation_indexed=cashflow_inflation_indexed,
            )
            replay.update({
                "start_index": start,
                "end_index_exclusive": start + window,
            })
            windows.append(replay)
        successful = sum(item["success"] for item in windows)
        result["rolling"] = {
            "rolling_years": rolling_years,
            "window_periods": window,
            "n_windows": len(windows),
            "successful_windows": successful,
            "success_rate": successful / len(windows),
            "terminal_percentiles": _percentiles([
                item["terminal_balance"] for item in windows
            ]),
            "real_terminal_percentiles": _percentiles([
                item["real_terminal_balance"] for item in windows
            ]),
            "windows": windows,
        }
    return result
