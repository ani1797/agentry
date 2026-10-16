import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from canada import cpp_timing, ontario_health_premium, resp_schedule, rrif_factor, tax_estimate


class TaxTests(unittest.TestCase):
    def tax(self, income, **extra):
        return tax_estimate({
            "province": "ON", "tax_year": 2026, "ordinary_income": income, **extra,
        })

    def test_zero_and_basic_credits(self):
        self.assertEqual(self.tax(0)["total_income_tax_estimate"], 0)
        self.assertEqual(self.tax(15000)["total_income_tax_estimate"], 0)
        self.assertAlmostEqual(self.tax(50000)["total_income_tax_estimate"], 7165.7755)

    def test_federal_bracket_and_bpa_boundaries(self):
        self.assertAlmostEqual(self.tax(58523)["federal"], (58523 - 16452) * .14)
        self.assertAlmostEqual(self.tax(58524)["federal"] - self.tax(58523)["federal"], .205)
        self.assertEqual(self.tax(181440)["federal_basic_personal_amount"], 16452)
        self.assertEqual(self.tax(258482)["federal_basic_personal_amount"], 14829)
        self.assertAlmostEqual(
            self.tax((181440 + 258482) / 2)["federal_basic_personal_amount"],
            (16452 + 14829) / 2,
        )

    def test_ontario_basic_reduction_and_surtax(self):
        result = self.tax(20000)
        basic = (20000 - 12989) * .0505
        self.assertAlmostEqual(result["ontario_basic_reduction"], 600 - basic)
        result = self.tax(200000)
        basic = result["ontario_before_surtax"]
        self.assertAlmostEqual(
            result["ontario_surtax"], .2 * (basic - 5818) + .36 * (basic - 7446)
        )

    def test_premium_boundaries(self):
        cases = {0: 0, 20000: 0, 25000: 300, 36000: 300, 38500: 450,
                 48000: 450, 48600: 600, 72000: 600, 72600: 750,
                 200000: 750, 200600: 900, 1000000: 900}
        for income, expected in cases.items():
            with self.subTest(income=income):
                self.assertAlmostEqual(ontario_health_premium(income), expected)

    def test_capital_gains_and_rrsp(self):
        self.assertEqual(self.tax(50000, capital_gains=20000)["taxable_income"], 60000)
        self.assertEqual(self.tax(50000, rrsp_deduction=10000)["taxable_income"], 40000)
        self.assertEqual(self.tax(50000, rrsp_deduction=60000)["taxable_income"], 0)
        self.assertEqual(
            self.tax(100000, net_income=300000)["federal_basic_personal_amount"], 14829
        )

    def test_reject_unsupported_and_invalid_inputs(self):
        for extra in ({"province": "BC"}, {"tax_year": 2025}, {"tax_year": 2026.0},
                      {"eligible_dividends": 1000}, {"ordinary_income": -1},
                      {"capital_gains": float("nan")}, {"ordinary_income": True},
                      {"net_income": 1}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                self.tax(50000, **extra)


class PensionTests(unittest.TestCase):
    def test_cpp_monthly_adjustments(self):
        for months, factor in ((720, .64), (779, .994), (780, 1), (781, 1.007), (840, 1.42)):
            result = cpp_timing({"monthly_at_65": 1000, "start_age_months": months})
            self.assertAlmostEqual(result["monthly_real_benefit"], 1000 * factor)

    def test_cpp_shared_valuation_and_cumulative_payments(self):
        result = cpp_timing({
            "monthly_at_65": 1000, "start_age_months": 780, "end_age": 66,
            "real_discount_rate": 0, "valuation_age_months": 720,
        })
        self.assertEqual(result["present_value"], 12000)
        self.assertEqual(result["cumulative_real_benefits"], 12000)
        result2 = cpp_timing({
            "monthly_at_65": 1000, "start_age_months": 780, "end_age": 66,
            "real_discount_rate": .05,
        })
        self.assertLess(result2["present_value"], 12000)

    def test_cpp_invalid_start_and_past_valuation(self):
        for extra in ({"start_age_months": 719}, {"start_age_months": 841},
                      {"valuation_age_months": 800}, {"start_age_months": True},
                      {"end_age": 60}, {"contribution_years": 20}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                cpp_timing({"monthly_at_65": 1000, "start_age_months": 780, **extra})

    def test_modern_rrif_factor_boundaries(self):
        for age, factor in ((60, 1 / 30), (70, .05), (71, .0528),
                            (72, .054), (94, .1879), (95, .2), (110, .2)):
            self.assertAlmostEqual(rrif_factor(age), factor)
        with self.assertRaises(ValueError):
            rrif_factor(True)


class RespTests(unittest.TestCase):
    def data(self, contributions=None, **extra):
        return {
            "start_age": 0, "contributions": contributions or [2500] * 18,
            "prior_contributions": 0, "prior_cesg": 0, "unused_cesg_room": 0,
            "eligible_at_16_17": True, "available_budget": 50000,
            "annual_return": 0, "student_effective_tax_rate": 0,
            "taxable_capital_gains_rate": 0, **extra,
        }

    def test_lifetime_grant_and_no_deduction(self):
        result = resp_schedule(self.data())
        self.assertEqual(result["total_basic_cesg"], 7200)
        self.assertEqual(result["contribution_tax_deduction"], 0)
        self.assertEqual(result["household_with_resp_after_tax"], 57200)
        self.assertEqual(result["same_budget_taxable_after_tax"], 50000)

    def test_lump_sum_only_gets_available_grant(self):
        result = resp_schedule(self.data([50000] + [0] * 17))
        self.assertEqual(result["total_basic_cesg"], 500)

    def test_carryforward_annual_limit(self):
        result = resp_schedule(self.data([5000], start_age=5, unused_cesg_room=2500))
        self.assertEqual(result["total_basic_cesg"], 1000)
        self.assertEqual(result["schedule"][0]["unused_cesg_room"], 2000)

    def test_age_16_cannot_invent_contribution_history(self):
        result = resp_schedule(self.data([5000, 5000], start_age=16, unused_cesg_room=8000))
        self.assertEqual(result["total_basic_cesg"], 0)
        result = resp_schedule(self.data([100] * 4 + [0] * 12 + [5000, 5000]))
        self.assertEqual(result["schedule"][16]["basic_cesg"], 1000)
        result = resp_schedule(self.data([100] * 4 + [0] * 12 + [5000, 5000],
                                        eligible_at_16_17=False))
        self.assertEqual(result["schedule"][16]["basic_cesg"], 0)

    def test_same_starting_capital_and_conservation(self):
        for schedule in ([50000] + [0] * 17, [2500] * 18):
            with self.subTest(schedule=schedule):
                result = resp_schedule(self.data(schedule))
                self.assertEqual(result["household_with_resp_after_tax"],
                                 50000 + result["total_basic_cesg"])

    def test_outside_acb_and_transfer_tax_are_tracked(self):
        result = resp_schedule(self.data([0, 2500], annual_return=.1,
                                        taxable_capital_gains_rate=.2))
        row = result["schedule"][1]
        fraction = 5000 / 55000
        sale = 2500 / (1 - fraction * .2)
        self.assertAlmostEqual(result["outside_transfer_tax"], sale - 2500)
        self.assertAlmostEqual(row["outside_acb"], 50000 * (1 - sale / 55000))
        self.assertGreater(result["household_with_resp_after_tax"],
                           result["education_spendable_estimate"])

    def test_invalid_and_overfunded_schedules(self):
        cases = (self.data([50001]), self.data([1], prior_contributions=1),
                 self.data([1], unused_cesg_room=500), self.data([1], eligible_at_16_17=1),
                 self.data([0, 50000], annual_return=-.5), self.data([1], annual_return=float("inf")))
        for data in cases:
            with self.subTest(data=data), self.assertRaises(ValueError):
                resp_schedule(copy.deepcopy(data))


if __name__ == "__main__":
    unittest.main()
