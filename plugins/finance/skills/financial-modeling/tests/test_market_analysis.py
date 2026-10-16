"""Synthetic, analytical tests; no market data, network, or third-party packages."""

import importlib.util
import math
from pathlib import Path
import unittest
from unittest.mock import mock_open, patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "market_analysis.py"
SPEC = importlib.util.spec_from_file_location("finance_market_analysis", MODULE_PATH)
market = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(market)


class AnalyzeTests(unittest.TestCase):
    def test_known_sample_statistics_and_percentiles(self):
        result = market.analyze([-0.1, 0, 0.1], periods_per_year=12)
        self.assertEqual(result["n"], 3)
        self.assertAlmostEqual(result["arithmetic_annualized_return"], 0)
        self.assertAlmostEqual(result["geometric_annualized_return"], 0.99 ** 4 - 1)
        self.assertAlmostEqual(result["sample_volatility"], 0.1)
        self.assertAlmostEqual(result["annualized_volatility"], 0.1 * math.sqrt(12))
        self.assertEqual(result["median"], 0)
        self.assertAlmostEqual(result["percentiles"]["p5"], -0.09)
        self.assertAlmostEqual(result["percentiles"]["p95"], 0.09)
        self.assertEqual(result["worst_period"], -0.1)
        self.assertEqual(result["best_period"], 0.1)
        self.assertTrue(result["caveats"])

    def test_drawdown_includes_initial_wealth_and_recovery(self):
        self.assertAlmostEqual(market.analyze([-0.5, 1])["max_drawdown"], 0.5)
        self.assertAlmostEqual(market.analyze([-0.5, -0.5])["max_drawdown"], 0.75)
        self.assertAlmostEqual(market.analyze([1, -0.25])["max_drawdown"], 0.25)
        self.assertEqual(market.analyze([0.1, 0.2])["max_drawdown"], 0)

    def test_geometric_not_arithmetic_annualization(self):
        result = market.analyze([0.1] * 12, 12)
        self.assertAlmostEqual(result["arithmetic_annualized_return"], 1.2)
        self.assertAlmostEqual(result["geometric_annualized_return"], 1.1 ** 12 - 1)
        self.assertEqual(result["sample_volatility"], 0)

    def test_zero_returns(self):
        result = market.analyze([0, 0])
        for name in ("sample_volatility", "geometric_annualized_return",
                     "arithmetic_annualized_return", "max_drawdown"):
            self.assertEqual(result[name], 0)

    def test_invalid_returns(self):
        for values in ([], [0], [True, 0], ["0", 0], [None, 0],
                       [math.nan, 0], [math.inf, 0], [-math.inf, 0],
                       [-1, 0], [-1.1, 0]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                market.analyze(values)
        with self.assertRaises(ValueError):
            market.analyze("0,0")

    def test_invalid_periods(self):
        for periods in (0, -1, True, 1.0, "12", None):
            with self.subTest(periods=periods), self.assertRaises(ValueError):
                market.analyze([0, 0], periods)

    def test_overflow_rejected_and_large_log_drawdown_supported(self):
        with self.assertRaises(ValueError):
            market.analyze([1e308, 1e308], 12)
        result = market.analyze([1e100] * 10 + [-0.5], 1)
        self.assertAlmostEqual(result["max_drawdown"], 0.5)


class LoadReturnsTests(unittest.TestCase):
    def load(self, text, **kwargs):
        with patch("builtins.open", mock_open(read_data=text)):
            return market.load_returns("synthetic.csv", **kwargs)

    def test_annual_returns(self):
        self.assertEqual(
            self.load("date,return\n2020-12-31,0.1\n2021-12-31,-0.2\n"),
            [0.1, -0.2],
        )

    def test_monthly_prices_have_one_fewer_return(self):
        values = self.load(
            "date,level\n2023-12-31,100\n2024-01-31,110\n2024-02-29,99\n",
            column="level", kind="prices", periods_per_year=12,
        )
        self.assertEqual(len(values), 2)
        self.assertAlmostEqual(values[0], 0.1)
        self.assertAlmostEqual(values[1], -0.1)

    def test_kind_does_not_infer_prices(self):
        text = "date,return\n2020-01-01,100\n2021-01-01,110\n"
        self.assertEqual(self.load(text), [100, 110])
        self.assertAlmostEqual(self.load(text, kind="prices")[0], 0.1)

    def test_duplicate_missing_and_out_of_order_dates(self):
        for second in ("2020-01-01", "2019-01-01", ""):
            with self.subTest(second=second), self.assertRaises(ValueError):
                self.load(f"date,return\n2020-01-01,0\n{second},0\n")

    def test_invalid_dates_values_headers_and_rows(self):
        for text in (
            "", "date,return\n", "return\n0\n", "date,price\n2020-01-01,1\n",
            "date,return,return\n2020-01-01,0,0\n",
            "date,return\nnot-a-date,0\n", "date,return\n2020-02-30,0\n",
            "date,return\n20200101,0\n", "date,return\n2020-01-01,\n",
            "date,return\n2020-01-01,NaN\n",
            "date,return\n2020-01-01,Inf\n",
            "date,return\n2020-01-01,-Inf\n",
            "date,return\n2020-01-01,true\n",
            "date,return\n2020-01-01,-1\n",
            "date,return\n2020-01-01\n",
            "date,return\n2020-01-01,0,unexpected\n",
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.load(text)

    def test_annual_and_monthly_gaps_rejected(self):
        for text, periods in (
            ("date,return\n2020-01-01,0\n2022-01-01,0\n", 1),
            ("date,return\n2020-01-01,0\n2021-02-01,0\n", 1),
            ("date,return\n2020-01-01,0\n2020-02-01,0\n", 1),
            ("date,return\n2020-01-01,0\n2020-03-01,0\n", 12),
            ("date,return\n2020-01-01,0\n2020-01-31,0\n", 12),
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.load(text, periods_per_year=periods)

    def test_leap_anniversary(self):
        self.assertEqual(
            self.load("date,return\n2020-02-29,0\n2021-02-28,0\n"), [0, 0]
        )

    def test_daily_business_gaps_and_weekends(self):
        self.assertEqual(self.load(
            "date,return\n2024-01-05,0\n2024-01-08,0\n",
            periods_per_year=252,
        ), [0, 0])
        for text in (
            "date,return\n2024-01-05,0\n2024-01-09,0\n",
            "date,return\n2024-01-06,0\n",
        ):
            with self.assertRaises(ValueError):
                self.load(text, periods_per_year=252)
        with self.assertRaises(ValueError):
            self.load("date,return\n2024-01-05,0\n2024-01-08,0\n",
                      periods_per_year=365)
        self.assertEqual(self.load(
            "date,return\n2024-02-28,0\n2024-02-29,0\n2024-03-01,0\n",
            periods_per_year=365,
        ), [0, 0, 0])

    def test_invalid_prices_and_options(self):
        for price in ("0", "-1", "NaN", "Inf"):
            with self.subTest(price=price), self.assertRaises(ValueError):
                self.load(
                    f"date,return\n2020-01-01,100\n2021-01-01,{price}\n",
                    kind="prices",
                )
        with self.assertRaises(ValueError):
            self.load("date,return\n2020-01-01,100\n", kind="prices")
        for kwargs in ({"kind": "log"}, {"column": "date"},
                       {"periods_per_year": 4}, {"periods_per_year": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.load("date,return\n2020-01-01,0\n", **kwargs)

    def test_price_ratio_rounding_to_total_loss_rejected(self):
        with self.assertRaises(ValueError):
            self.load("date,return\n2020-01-01,1e308\n2021-01-01,1e-308\n",
                      kind="prices")


class BacktestTests(unittest.TestCase):
    def test_zero_return_contributions_and_end_period_timing(self):
        result = market.backtest([0] * 12, 100, annual_cashflow=120, periods_per_year=12)
        self.assertEqual(result["terminal_balance"], 220)
        self.assertEqual(result["total_period_contributions"], 120)
        self.assertEqual(result["total_contributions"], 220)
        self.assertTrue(result["success"])
        timing = market.backtest([1, 0], 100, annual_cashflow=10)
        self.assertEqual(timing["balances"], [100, 210, 220])
        self.assertEqual(timing["period_results"][0]["actual_cashflow"], 10)

    def test_fee_compounds_multiplicatively_and_inflation(self):
        result = market.backtest([0] * 12, 1000, periods_per_year=12,
                                 annual_fee=0.12, inflation=0.1)
        self.assertAlmostEqual(result["terminal_balance"], 880)
        self.assertAlmostEqual(result["total_fees"], 120)
        self.assertAlmostEqual(result["real_terminal_balance"], 800)
        result = market.backtest([0.1, 0.1], 100, annual_fee=0.1, inflation=0.1)
        self.assertAlmostEqual(result["terminal_balance"], 100 * 0.99 ** 2)
        self.assertAlmostEqual(result["real_terminal_balance"], 81)

    def test_fractional_year_inflation_and_deflation(self):
        result = market.backtest([0] * 6, 100, periods_per_year=12, inflation=0.21)
        self.assertAlmostEqual(result["real_terminal_balance"], 100 / 1.1)
        result = market.backtest([0], 100, inflation=-0.2)
        self.assertAlmostEqual(result["real_terminal_balance"], 125)

    def test_shortfalls_explicit_without_negative_balance(self):
        result = market.backtest([0, 0, 0], 100, annual_cashflow=-60)
        self.assertEqual(result["balances"], [100, 40, 0, 0])
        self.assertEqual(result["total_withdrawals"], 100)
        self.assertEqual(result["total_requested_withdrawals"], 180)
        self.assertEqual(result["total_shortfall"], 80)
        self.assertEqual(result["first_shortfall_period"], 1)
        self.assertFalse(result["success"])
        self.assertTrue(result["depleted"])
        self.assertEqual(result["period_results"][1]["actual_cashflow"], -40)
        self.assertEqual(result["period_results"][1]["shortfall"], 20)

    def test_exact_exhaustion_is_not_unmet_withdrawal(self):
        result = market.backtest([0], 100, annual_cashflow=-100)
        self.assertTrue(result["success"])
        self.assertTrue(result["depleted"])
        self.assertEqual(result["total_shortfall"], 0)
        self.assertEqual(market.backtest([0], 0)["real_terminal_balance"], 0)

    def test_withdrawals_are_not_inflation_indexed(self):
        result = market.backtest([0, 0], 100, annual_cashflow=-10, inflation=0.1)
        self.assertEqual(result["terminal_balance"], 80)
        self.assertAlmostEqual(result["real_terminal_balance"], 80 / 1.1 ** 2)
        self.assertFalse(result["assumptions"]["cashflow_inflation_indexed"])

    def test_inflation_indexed_spending_starts_at_base_amount(self):
        result = market.backtest(
            [0, 0, 0], 100, annual_cashflow=-10, inflation=0.1,
            cashflow_timing="beginning", cashflow_inflation_indexed=True,
        )
        requested = [row["requested_cashflow"] for row in result["period_results"]]
        for actual, expected in zip(requested, [-10, -11, -12.1]):
            self.assertAlmostEqual(actual, expected)
        self.assertEqual(requested[0], -10)
        self.assertAlmostEqual(result["total_withdrawals"], 33.1)
        self.assertAlmostEqual(result["terminal_balance"], 66.9)
        self.assertAlmostEqual(result["real_terminal_balance"], 66.9 / 1.1 ** 3)
        self.assertTrue(result["assumptions"]["cashflow_inflation_indexed"])

    def test_subannual_indexed_contributions_and_end_spending(self):
        for timing in ("beginning", "end"):
            with self.subTest(timing=timing):
                result = market.backtest(
                    [0, 0, 0], 100, annual_cashflow=20, periods_per_year=2,
                    inflation=0.21, cashflow_timing=timing,
                    cashflow_inflation_indexed=True,
                )
                requested = [
                    row["requested_cashflow"] for row in result["period_results"]
                ]
                for actual, expected in zip(requested, [10, 11, 12.1]):
                    self.assertAlmostEqual(actual, expected)
                self.assertAlmostEqual(result["total_period_contributions"], 33.1)
                self.assertAlmostEqual(result["terminal_balance"], 133.1)
        spending = market.backtest(
            [0, 0], 100, annual_cashflow=-10, inflation=0.1,
            cashflow_inflation_indexed=True,
        )
        self.assertAlmostEqual(spending["terminal_balance"], 79)

    def test_first_year_timing_changes_growth_and_fees(self):
        end = market.backtest([0.1], 100, annual_cashflow=-10, annual_fee=0.1)
        beginning = market.backtest(
            [0.1], 100, annual_cashflow=-10, annual_fee=0.1,
            cashflow_timing="beginning",
        )
        self.assertAlmostEqual(end["terminal_balance"], 89)
        self.assertAlmostEqual(beginning["terminal_balance"], 89.1)
        self.assertAlmostEqual(end["total_fees"], 11)
        self.assertAlmostEqual(beginning["total_fees"], 9.9)
        contributed = market.backtest(
            [1], 100, annual_cashflow=10, cashflow_timing="beginning",
        )
        self.assertEqual(contributed["terminal_balance"], 220)
        end_contributed = market.backtest([1], 100, annual_cashflow=10)
        self.assertEqual(end_contributed["terminal_balance"], 210)

    def test_beginning_shortfall_is_not_rescued_by_later_return(self):
        beginning = market.backtest(
            [1], 100, annual_cashflow=-150, cashflow_timing="beginning",
        )
        end = market.backtest([1], 100, annual_cashflow=-150)
        self.assertEqual(beginning["total_shortfall"], 50)
        self.assertEqual(beginning["terminal_balance"], 0)
        self.assertFalse(beginning["success"])
        self.assertEqual(end["total_shortfall"], 0)
        self.assertEqual(end["terminal_balance"], 50)
        self.assertTrue(end["success"])

    def test_rolling_windows_reset_inflation_indexing(self):
        result = market.backtest(
            [0] * 4, 100, annual_cashflow=-10, inflation=0.1, rolling_years=2,
            cashflow_timing="beginning", cashflow_inflation_indexed=True,
        )
        self.assertEqual(result["rolling"]["n_windows"], 3)
        for window in result["rolling"]["windows"]:
            self.assertAlmostEqual(window["total_requested_withdrawals"], 21)
            self.assertAlmostEqual(window["terminal_balance"], 79)
            self.assertAlmostEqual(window["real_terminal_balance"], 79 / 1.1 ** 2)
        self.assertGreater(result["total_requested_withdrawals"], 42)

    def test_indexing_handles_deflation_zero_flow_and_shortfalls(self):
        deflation = market.backtest(
            [0, 0], 100, annual_cashflow=-10, inflation=-0.2,
            cashflow_inflation_indexed=True,
        )
        self.assertAlmostEqual(deflation["total_withdrawals"], 18)
        self.assertAlmostEqual(deflation["terminal_balance"], 82)
        zero = market.backtest(
            [0, 0], 0, inflation=1e308, cashflow_inflation_indexed=True,
        )
        self.assertEqual(zero["total_period_contributions"], 0)
        indexed = market.backtest(
            [0, 0], 20, annual_cashflow=-10, inflation=0.1,
            cashflow_timing="beginning", cashflow_inflation_indexed=True,
        )
        self.assertAlmostEqual(indexed["total_requested_withdrawals"], 21)
        self.assertAlmostEqual(indexed["total_shortfall"], 1)
        self.assertEqual(indexed["first_shortfall_period"], 1)

    def test_cashflow_options_validate_types_and_keyword_only(self):
        for timing in ("start", "END", "", True, False, 0, None, ["end"]):
            with self.subTest(timing=timing), self.assertRaises(ValueError):
                market.backtest([0], 100, cashflow_timing=timing)
        for indexed in ("true", "false", 1, 0, None, [], 1.0):
            with self.subTest(indexed=indexed), self.assertRaises(ValueError):
                market.backtest([0], 100, cashflow_inflation_indexed=indexed)
        with self.assertRaises(TypeError):
            market.backtest([0], 100, 0, 1, 0, 0, None, "beginning")

    def test_no_lookahead_and_input_not_mutated(self):
        values = [0.1, -0.2]
        original = values[:]
        prefix = market.backtest(values, 100, annual_cashflow=-5)
        extended = market.backtest(values + [10], 100, annual_cashflow=-5)
        self.assertEqual(prefix["balances"], extended["balances"][:3])
        self.assertEqual(prefix["period_results"], extended["period_results"][:2])
        self.assertEqual(values, original)

    def test_all_rolling_windows_inclusive_boundaries(self):
        result = market.backtest([0.1, 0.2, -0.5], 100, rolling_years=2)
        rolling = result["rolling"]
        self.assertEqual(rolling["n_windows"], 2)
        self.assertEqual([item["start_index"] for item in rolling["windows"]], [0, 1])
        self.assertEqual(
            [item["end_index_exclusive"] for item in rolling["windows"]], [2, 3]
        )
        self.assertAlmostEqual(rolling["windows"][0]["terminal_balance"], 132)
        self.assertAlmostEqual(rolling["windows"][1]["terminal_balance"], 60)
        self.assertAlmostEqual(rolling["terminal_percentiles"]["p50"], 96)
        one = market.backtest([0.1, 0.2], 100, rolling_years=2)["rolling"]
        self.assertEqual(one["n_windows"], 1)
        self.assertAlmostEqual(one["terminal_percentiles"]["p5"], 132)

    def test_rolling_monthly_windows_success_and_fresh_initial_balance(self):
        result = market.backtest([-0.9, 0, 0, 0], 100, annual_cashflow=-60,
                                 periods_per_year=2, rolling_years=1)
        rolling = result["rolling"]
        self.assertEqual(rolling["window_periods"], 2)
        self.assertEqual(rolling["n_windows"], 3)
        self.assertEqual(rolling["successful_windows"], 2)
        self.assertAlmostEqual(rolling["success_rate"], 2 / 3)
        self.assertEqual(rolling["windows"][1]["terminal_balance"], 40)

    def test_invalid_arguments_and_overflow(self):
        cases = (
            {"returns": []}, {"returns": [-1]}, {"returns": [True]},
            {"initial_balance": -1}, {"initial_balance": math.inf},
            {"initial_balance": True}, {"annual_cashflow": math.nan},
            {"annual_cashflow": False}, {"annual_fee": -0.1},
            {"annual_fee": 1}, {"annual_fee": math.nan},
            {"inflation": -1}, {"inflation": math.inf},
            {"periods_per_year": 0}, {"periods_per_year": True},
            {"rolling_years": 0}, {"rolling_years": True},
            {"rolling_years": 1.5}, {"rolling_years": 3},
            {"returns": [1e308], "initial_balance": 1e308},
        )
        for changes in cases:
            kwargs = {"returns": [0, 0], "initial_balance": 100}
            kwargs.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                market.backtest(**kwargs)

    def test_resource_bounds(self):
        with patch.object(market, "MAX_OBSERVATIONS", 2):
            with self.assertRaises(ValueError):
                market.backtest([0, 0, 0], 100)
        with patch.object(market, "MAX_ROLLING_PERIODS", 3):
            with self.assertRaises(ValueError):
                market.backtest([0, 0, 0], 100, rolling_years=2)


if __name__ == "__main__":
    unittest.main()
