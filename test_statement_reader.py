#!/usr/bin/env python3
"""Run: python test_statement_reader.py"""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

import llm
import statement_reader as sr


def fresh_statements() -> dict[str, dict[str, pd.DataFrame]]:
    sr.RNG = np.random.default_rng(11)  # same seed as the script, same statements
    return {name: sr.make_statements(spec) for name, spec in sr.COMPANIES.items()}


STATEMENTS = fresh_statements()
PACKS = {name: sr.evidence_for(name, f) for name, f in STATEMENTS.items()}


class TestStatements(unittest.TestCase):
    def test_balance_sheets_balance(self):
        for name, f in STATEMENTS.items():
            gap = (f["bs"].total_assets - f["bs"].total_liab_equity).abs().max()
            self.assertLess(gap, 0.05, f"{name}: assets != liabilities + equity")

    def test_cash_flow_reconciles_change_in_cash(self):
        for name, f in STATEMENTS.items():
            c = f["cf"]
            recon = (c.cfo + c.cfi + c.cff) - (c.closing_cash - c.opening_cash)
            self.assertLess(recon.abs().max(), 0.05, f"{name}: cash flow does not reconcile")
            # and closing cash is what sits on the balance sheet
            self.assertTrue(np.allclose(c.closing_cash.values, f["bs"].cash.values))

    def test_income_statement_lines_add_up(self):
        i = STATEMENTS["Company A"]["is"]
        self.assertTrue(np.allclose(i.revenue - i.cogs - i.opex - i.depreciation + i.other_income - i.interest, i.pbt))
        self.assertTrue(np.allclose(i.pbt - i.tax, i.net_income))


class TestEngine(unittest.TestCase):
    def test_dso_hand_computed(self):
        # receivables 100 on revenue 730 -> 100 / 730 * 365 = 50 days, every year
        n = len(sr.YEARS)
        f = {"is": pd.DataFrame({"revenue": [730.0] * n, "cogs": [365.0] * n, "gross_profit": [365.0] * n,
                                 "ebitda": [100.0] * n, "depreciation": [10.0] * n, "ebit": [90.0] * n,
                                 "interest": [10.0] * n, "other_income": [5.0] * n, "pbt": [85.0] * n,
                                 "net_income": [60.0] * n}, index=sr.YEARS),
             "bs": pd.DataFrame({"ar": [100.0] * n, "inv": [73.0] * n, "ap": [36.5] * n, "debt": [50.0] * n,
                                 "cash": [20.0] * n, "equity": [200.0] * n}, index=sr.YEARS),
             "cf": pd.DataFrame({"cfo": [70.0] * n, "capex": [12.0] * n}, index=sr.YEARS)}
        f["is"].attrs["revenue_prior"] = 730.0
        r = sr.ratios(f)
        self.assertTrue(np.allclose(r.dso_days, 50.0))
        self.assertTrue(np.allclose(r.inventory_days, 73.0))      # 73 / 365 * 365
        self.assertTrue(np.allclose(r.payable_days, 36.5))
        self.assertTrue(np.allclose(r.cash_conversion_cycle_days, 50 + 73 - 36.5))
        self.assertTrue(np.allclose(r.interest_coverage, 9.0))

    def test_stories_fire_the_right_flags(self):
        a, b, c = (set(fl["flag"] for fl in PACKS[n]["flags"]) for n in ("Company A", "Company B", "Company C"))
        self.assertEqual(a, set())
        self.assertTrue({"cash_conversion_low", "dso_rising", "other_income_dependence"} <= b)
        self.assertNotIn("interest_coverage_low", b)
        self.assertTrue({"interest_coverage_low", "net_debt_rising", "capex_funded_by_debt"} <= c)
        self.assertEqual([PACKS[n]["verdict"] for n in ("Company A", "Company B", "Company C")],
                         ["PROCEED", "PROCEED WITH DILIGENCE", "PASS"])

    def test_dso_climbs_as_specified_for_company_b(self):
        dso = PACKS["Company B"]["trend"]["dso_days"]
        self.assertAlmostEqual(dso[0], 45, delta=1)
        self.assertAlmostEqual(dso[-1], 110, delta=1)

    def test_verdict_thresholds(self):
        high, med = {"severity": "high"}, {"severity": "medium"}
        self.assertEqual(sr.verdict([])[0], "PROCEED")
        self.assertEqual(sr.verdict([med])[0], "PROCEED")
        self.assertEqual(sr.verdict([high])[0], "PROCEED WITH DILIGENCE")
        self.assertEqual(sr.verdict([high, high, high])[0], "PASS")
        self.assertEqual(sr.verdict([high, high, med, med, med])[0], "PASS")   # 7 points

    def test_piotroski_and_accrual_sanity(self):
        for ev in PACKS.values():
            self.assertTrue(0 <= ev["piotroski"]["score"] <= 9)
            self.assertEqual(len(ev["piotroski"]["passed"]), ev["piotroski"]["score"])
        self.assertGreater(PACKS["Company A"]["piotroski"]["score"], PACKS["Company C"]["piotroski"]["score"])
        self.assertGreater(PACKS["Company B"]["accrual_ratio"], PACKS["Company A"]["accrual_ratio"])


class TestNarrative(unittest.TestCase):
    def test_template_renders_three_to_four_lines(self):
        for ev in PACKS.values():
            memo = sr.template_memo(ev)
            self.assertIn(ev["verdict"], memo)
            self.assertTrue(3 <= len(memo.splitlines()) <= 4)
            self.assertIn("Ask management first:", memo)
            self.assertEqual(llm.unpinned(memo, ev), set())    # the template never invents a number

    def test_unpinned_catches_an_invented_number(self):
        ev = PACKS["Company B"]
        clean = f"Cash conversion is {ev['latest']['cash_conversion']} against a threshold of 0.7."
        self.assertEqual(llm.unpinned(clean, ev), set())
        self.assertEqual(llm.unpinned("Cash conversion is 0.31 against a threshold of 0.7.", ev), {"0.31"})


if __name__ == "__main__":
    unittest.main(verbosity=1)
