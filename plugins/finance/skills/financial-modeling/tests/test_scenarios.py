from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from market_analysis import backtest
from scenarios import project, simulate, summarize, withdrawals


class ScenarioTests(unittest.TestCase):
    def data(self, **extra):
        return {
            "current_age": 40, "retirement_age": 42, "end_age": 45,
            "initial_balance": 100000, "annual_savings": 10000,
            "annual_retirement_spending": 20000, "annual_return": 0,
            "inflation": 0, **extra,
        }

    def test_analytical_cashflow_timing(self):
        result = project(self.data())
        self.assertEqual(result["terminal_real_balance"], 60000)
        self.assertEqual([row["real_savings"] for row in result["schedule"]],
                         [10000, 10000, 0, 0, 0])
        result = project(self.data(end_age=41, retirement_age=40, annual_return=.1))
        self.assertAlmostEqual(result["terminal_real_balance"], 88000)

    def test_real_and_nominal_consistency(self):
        result = project(self.data(annual_return=.1, inflation=.1))
        self.assertAlmostEqual(result["terminal_real_balance"], 60000)

    def test_events_and_exclusive_horizon(self):
        result = project(self.data(
            income_events=[{"name": "income", "start_age": 43, "end_age": 44, "annual_amount": 5000}],
            expense_events=[{"name": "lump sum", "start_age": 41, "end_age": 41, "annual_amount": 10000}],
        ))
        self.assertEqual(result["terminal_real_balance"], 60000)
        self.assertEqual(len(result["schedule"]), 5)

    def test_shortfalls_are_not_erased_by_future_recovery(self):
        result = project(self.data(
            retirement_age=40, initial_balance=0,
            income_events=[{"name": "later", "start_age": 44, "end_age": 44, "annual_amount": 100000}],
        ))
        self.assertFalse(result["success"])
        self.assertEqual(result["first_shortfall_age"], 40)
        self.assertEqual(result["total_real_shortfall"], 80000)
        self.assertEqual(result["terminal_real_balance"], 80000)

    def test_fee_and_path(self):
        result = project(self.data(return_path=[.1] * 5, annual_fee=.01))
        balance = 100000
        for age in range(40, 45):
            balance = (balance + (10000 if age < 42 else -20000)) * 1.1 * .99
        self.assertAlmostEqual(result["terminal_real_balance"], balance)

    def test_parameter_validation(self):
        invalid = (
            {"annual_spendng": 1}, {"annual_return": True}, {"end_age": 40},
            {"return_path": [0]}, {"annual_fee": 1}, {"inflation": -1},
            {"expense_events": [{"name": "bad", "start_age": 41, "end_age": 50, "annual_amount": 1}]},
        )
        for extra in invalid:
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                project(self.data(**extra))

    def test_seeded_repeatability_and_common_paths(self):
        data = self.data(annual_return=.05, annual_volatility=.15, trials=100,
                         seed=42, retirement_ages=[40, 42])
        self.assertEqual(simulate(data), simulate(data))
        both = simulate(data)
        single = simulate({**data, "retirement_ages": [42]})
        self.assertEqual(both["scenarios"][1], single["scenarios"][0])

    def test_zero_volatility_equals_project(self):
        data = self.data(annual_return=.05, trials=20)
        expected = project(data)["terminal_real_balance"]
        result = simulate(data)["scenarios"][0]
        self.assertAlmostEqual(result["terminal_real_balance_percentiles"]["p50"], expected)
        self.assertEqual(result["successful_paths"], 20)

    def test_lognormal_arithmetic_parameters(self):
        data = self.data(
            current_age=40, retirement_age=40, end_age=41, initial_balance=1,
            annual_savings=0, annual_retirement_spending=0,
            annual_return=.07, annual_volatility=.2, trials=10000, seed=7,
        )
        result = simulate(data)["scenarios"][0]
        median = result["terminal_real_balance_percentiles"]["p50"]
        self.assertAlmostEqual(median, 1.07 / (1 + (.2 / 1.07) ** 2) ** .5, delta=.01)
        self.assertAlmostEqual(result["terminal_real_balance_mean"], 1.07, delta=.01)
        self.assertIn("all paths", result["percentile_population"])

    def test_bootstrap_and_sampling_bounds(self):
        result = simulate(self.data(method="bootstrap", historical_returns=[0, 0],
                                    bootstrap_block_years=2, trials=5))
        scenario = result["scenarios"][0]
        self.assertEqual(scenario["terminal_real_balance_percentiles"]["p50"], 60000)
        low, high = scenario["simulation_sampling_interval_95"]
        self.assertLess(low, 1)
        self.assertEqual(high, 1)
        for extra in ({"method": "unknown"}, {"method": "bootstrap"},
                      {"historical_returns": [0, 0]}, {"trials": 0},
                      {"retirement_ages": [42, 42]}, {"return_path": [0] * 5}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                simulate(self.data(**extra))

    def test_historical_replay_matches_real_fire_timing(self):
        returns = [.05, -.1, .1, .03, .07]
        scenario = self.data(retirement_age=40, annual_savings=0, inflation=.02,
                             return_path=returns)
        deterministic = project(scenario)
        historical = backtest(
            returns, 100000, -20000, inflation=.02,
            cashflow_timing="beginning", cashflow_inflation_indexed=True,
        )
        self.assertAlmostEqual(
            deterministic["terminal_real_balance"], historical["real_terminal_balance"]
        )

    def test_arbitrary_scenario_outcome_statistics(self):
        result = summarize({"values": [1, 2, 3]})
        self.assertEqual(result["mean"], 2)
        self.assertEqual(result["sample_standard_deviation"], 1)
        self.assertEqual(result["percentiles"]["p50"], 2)
        for values in ([True, 1], [1], [float("nan"), 2]):
            with self.assertRaises(ValueError):
                summarize({"values": values})


class WithdrawalTests(unittest.TestCase):
    def data(self, **extra):
        return {
            "province": "ON", "tax_year": 2026, "start_age": 70, "end_age": 75,
            "balances": {"taxable": 100000, "tfsa": 100000, "rrsp": 300000, "rrif": 0},
            "taxable_acb": 70000, "annual_real_spending": 40000,
            "annual_real_income": 12000, "return_path": [0] * 5, "inflation": 0,
            "strategy": ["taxable", "rrsp", "rrif", "tfsa"], **extra,
        }

    def test_surplus_reinvested_and_wealth_conserved(self):
        result = withdrawals(self.data(
            start_age=72, end_age=73, annual_real_spending=0,
            annual_real_income=0, return_path=[0],
            balances={"taxable": 0, "tfsa": 0, "rrsp": 0, "rrif": 100000},
            taxable_acb=0,
        ))
        row = result["schedule"][0]
        self.assertEqual(row["gross_real_withdrawals"]["rrif"], 5400)
        self.assertEqual(row["real_surplus_reinvested"], 5400)
        self.assertEqual(sum(row["closing_real_balances"].values()), 100000)
        self.assertEqual(row["real_taxable_acb"], 5400)

    def test_rrsp_conversion_and_first_minimum(self):
        result = withdrawals(self.data(
            start_age=71, end_age=73, annual_real_spending=0,
            annual_real_income=0, return_path=[0, 0],
        ))
        self.assertEqual(result["schedule"][0]["gross_real_withdrawals"]["rrif"], 0)
        self.assertEqual(result["schedule"][1]["gross_real_withdrawals"]["rrif"], 16200)
        self.assertEqual(result["terminal_real_balances"]["rrsp"], 0)

    def test_each_year_conserves_household_money_after_tax(self):
        result = withdrawals(self.data())
        for row in result["schedule"]:
            before = sum(row["opening_real_balances"].values())
            expected = before + 12000 - 40000 - row["real_income_tax"] + row["real_shortfall"]
            self.assertAlmostEqual(sum(row["closing_real_balances"].values()), expected, places=5)
        self.assertLessEqual(result["terminal_real_after_tax_estate_estimate"],
                             result["terminal_real_balance_before_estate_tax"])

    def test_tax_grossup_funds_spending(self):
        result = withdrawals(self.data(
            start_age=60, end_age=61, annual_real_spending=50000, annual_real_income=0,
            return_path=[0], balances={"taxable": 0, "tfsa": 0, "rrsp": 200000, "rrif": 0},
            taxable_acb=0,
        ))
        row = result["schedule"][0]
        gross = row["gross_real_withdrawals"]["rrsp"]
        self.assertAlmostEqual(gross - row["real_income_tax"], 50000)
        self.assertTrue(result["success"])

    def test_acb_deflates_not_market_value_reset(self):
        result = withdrawals(self.data(
            start_age=60, end_age=61, annual_real_spending=0, annual_real_income=0,
            return_path=[.1], inflation=.1, taxable_acb=50000,
            balances={"taxable": 100000, "tfsa": 0, "rrsp": 0, "rrif": 0},
        ))
        self.assertAlmostEqual(result["terminal_real_balances"]["taxable"], 100000)
        self.assertAlmostEqual(result["terminal_real_taxable_acb"], 50000 / 1.1)

    def test_time_varying_pension_and_spending(self):
        result = withdrawals(self.data(
            annual_real_income=[0, 0, 12000, 12000, 12000],
            annual_real_spending=[30000, 35000, 40000, 45000, 50000],
        ))
        self.assertEqual([row["real_spending"] for row in result["schedule"]],
                         [30000, 35000, 40000, 45000, 50000])

    def test_shortfall_and_invalid_models(self):
        result = withdrawals(self.data(
            balances={"taxable": 0, "tfsa": 0, "rrsp": 0, "rrif": 0}, taxable_acb=0,
        ))
        self.assertFalse(result["success"])
        self.assertGreater(result["schedule"][0]["real_shortfall"], 0)
        for extra in ({"province": "QC"}, {"strategy": ["tfsa"]},
                      {"return_path": [0]}, {"annual_real_income": [1]},
                      {"lif_maximum": 5000}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                withdrawals(self.data(**extra))


if __name__ == "__main__":
    unittest.main()
