#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Reusable offline financial models. All inputs/outputs are local JSON or CSV."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from canada import cpp_timing, resp_schedule, tax_estimate
from market_analysis import analyze, backtest, load_returns
from scenarios import project, simulate, summarize, withdrawals


def read_json(path):
    def reject_constant(value):
        raise ValueError(f"non-finite JSON value: {value}")

    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(
        Path(path).read_text(encoding="utf-8"),
        parse_constant=reject_constant, object_pairs_hook=unique_pairs,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    functions = {
        "tax": tax_estimate, "cpp": cpp_timing, "resp": resp_schedule,
        "project": project, "simulate": simulate, "withdrawals": withdrawals,
        "summarize": summarize,
    }
    for name in functions:
        command = sub.add_parser(name)
        command.add_argument("input", help="Local JSON input; see references/models.md")
    for name in ("analyze", "backtest"):
        command = sub.add_parser(name)
        command.add_argument("input", help="Chronological CSV with date and numeric column")
        command.add_argument("--column", default="return")
        command.add_argument("--kind", choices=("returns", "prices"), default="returns")
        command.add_argument("--periods-per-year", type=int, choices=(1, 12, 252, 365), default=1)
        if name == "backtest":
            command.add_argument("--initial-balance", type=float, required=True)
            command.add_argument("--annual-cashflow", type=float, default=0)
            command.add_argument("--annual-fee", type=float, default=0)
            command.add_argument("--inflation", type=float, default=0)
            command.add_argument("--rolling-years", type=int)
            command.add_argument("--cashflow-timing", choices=("beginning", "end"), default="end")
            command.add_argument("--index-cashflow", action="store_true",
                                 help="Index each period's cash flow to the supplied inflation rate")
    args = parser.parse_args()
    try:
        if args.command in functions:
            result = functions[args.command](read_json(args.input))
        else:
            returns = load_returns(
                args.input, column=args.column, kind=args.kind,
                periods_per_year=args.periods_per_year,
            )
            if args.command == "analyze":
                result = analyze(returns, args.periods_per_year)
            else:
                result = backtest(
                    returns, args.initial_balance, args.annual_cashflow,
                    args.periods_per_year, args.annual_fee, args.inflation, args.rolling_years,
                    cashflow_timing=args.cashflow_timing,
                    cashflow_inflation_indexed=args.index_cashflow,
                )
        result["provenance"] = {
            "tool_version": "0.1.0",
            "input_sha256": hashlib.sha256(Path(args.input).read_bytes()).hexdigest(),
            "command": args.command,
        }
        print(json.dumps(result, indent=2, allow_nan=False))
    except (OSError, ValueError, OverflowError) as exc:
        parser.exit(2, f"finance_model: {exc}\n")


if __name__ == "__main__":
    main()
