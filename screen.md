# Financial statement screen

Ratio red flags, Piotroski score and accrual ratio on five years of synthetic statements. Memos written by: none; every number verified against the evidence pack. A screen, not a valuation, and not advice.

## Company A - PROCEED

PROCEED: 0 flags on FY26 - revenue 1371.3 cr, net margin 10.88%, Piotroski 9/9, accrual ratio -0.05.
Cash conversion 1.21, net debt/EBITDA -0.01, interest coverage 23.88x, ROCE 35.47%.
Ask management first: what sustains 14.82% growth with capex at 1.21x depreciation, and for how long.

*source: template (no API key)*

<details><summary>evidence</summary>

```json
{
  "company": "Company A",
  "currency": "INR crore",
  "years": [
    "FY22",
    "FY23",
    "FY24",
    "FY25",
    "FY26"
  ],
  "latest_year": "FY26",
  "latest": {
    "revenue": 1371.3,
    "net_income": 149.2,
    "cfo": 180.8,
    "revenue_growth_pct": 14.82,
    "gross_margin_pct": 42.06,
    "ebitda_margin_pct": 18.11,
    "net_margin_pct": 10.88,
    "cash_conversion": 1.21,
    "dso_days": 45.01,
    "inventory_days": 60.0,
    "payable_days": 54.99,
    "cash_conversion_cycle_days": 50.02,
    "net_debt_to_ebitda": -0.01,
    "interest_coverage": 23.88,
    "capex_to_depreciation": 1.21,
    "free_cash_flow": 114.5,
    "other_income_pct_pbt": 6.88,
    "roce_pct": 35.47
  },
  "trend": {
    "cash_conversion": [
      1.29,
      1.28,
      1.25,
      1.24,
      1.21
    ],
    "dso_days": [
      48.01,
      47.01,
      45.98,
      44.99,
      45.01
    ],
    "net_debt_to_ebitda": [
      1.57,
      1.09,
      0.68,
      0.31,
      -0.01
    ],
    "interest_coverage": [
      3.56,
      5.22,
      7.76,
      12.52,
      23.88
    ]
  },
  "flags": [],
  "flag_points": 0,
  "piotroski": {
    "score": 9,
    "out_of": 9,
    "passed": [
      "positive_roa",
      "positive_cfo",
      "roa_improved",
      "cfo_exceeds_net_income",
      "leverage_fell",
      "current_ratio_rose",
      "no_new_shares",
      "gross_margin_rose",
      "asset_turnover_rose"
    ]
  },
  "accrual_ratio": -0.05,
  "verdict": "PROCEED"
}
```
</details>

## Company B - PROCEED WITH DILIGENCE

PROCEED WITH DILIGENCE: 4 flags on FY26 - revenue 1118.6 cr, net margin 7.82%, Piotroski 6/9, accrual ratio 0.099.
cash conversion (CFO / net income): 0.24 vs threshold 0.7 (below in 2+ of last 3 years; 3 of last 3 years below 0.7).
DSO rise over 3 years, %: 89.6 vs threshold 40 (above; 58 -> 110 days).
Ask management first: walk me through the receivables ageing and which customers are past 90 days.

*source: template (no API key)*

<details><summary>evidence</summary>

```json
{
  "company": "Company B",
  "currency": "INR crore",
  "years": [
    "FY22",
    "FY23",
    "FY24",
    "FY25",
    "FY26"
  ],
  "latest_year": "FY26",
  "latest": {
    "revenue": 1118.6,
    "net_income": 87.5,
    "cfo": 20.7,
    "revenue_growth_pct": 18.55,
    "gross_margin_pct": 37.69,
    "ebitda_margin_pct": 11.76,
    "net_margin_pct": 7.82,
    "cash_conversion": 0.24,
    "dso_days": 110.0,
    "inventory_days": 50.01,
    "payable_days": 44.98,
    "cash_conversion_cycle_days": 115.02,
    "net_debt_to_ebitda": 1.1,
    "interest_coverage": 3.88,
    "capex_to_depreciation": 1.09,
    "free_cash_flow": -22.1,
    "other_income_pct_pbt": 41.25,
    "roce_pct": 14.08
  },
  "trend": {
    "cash_conversion": [
      1.28,
      0.71,
      0.59,
      0.39,
      0.24
    ],
    "dso_days": [
      45.03,
      58.02,
      71.98,
      90.01,
      110.0
    ],
    "net_debt_to_ebitda": [
      0.91,
      0.83,
      0.86,
      0.95,
      1.1
    ],
    "interest_coverage": [
      4.05,
      4.26,
      3.98,
      3.89,
      3.88
    ]
  },
  "flags": [
    {
      "flag": "cash_conversion_low",
      "label": "cash conversion (CFO / net income)",
      "severity": "high",
      "value": 0.24,
      "threshold": 0.7,
      "direction": "below in 2+ of last 3 years",
      "detail": "3 of last 3 years below 0.7"
    },
    {
      "flag": "dso_rising",
      "label": "DSO rise over 3 years, %",
      "severity": "high",
      "value": 89.6,
      "threshold": 40,
      "direction": "above",
      "detail": "58 -> 110 days"
    },
    {
      "flag": "other_income_dependence",
      "label": "other income as % of PBT",
      "severity": "medium",
      "value": 41.25,
      "threshold": 30,
      "direction": "above",
      "detail": "20% -> 41% over 3 years"
    },
    {
      "flag": "working_capital_squeeze",
      "label": "cash conversion cycle change over 3 years, days",
      "severity": "medium",
      "value": 52.0,
      "threshold": 20,
      "direction": "above",
      "detail": "63 -> 115 days"
    }
  ],
  "flag_points": 6,
  "piotroski": {
    "score": 6,
    "out_of": 9,
    "passed": [
      "positive_roa",
      "positive_cfo",
      "roa_improved",
      "leverage_fell",
      "current_ratio_rose",
      "no_new_shares"
    ]
  },
  "accrual_ratio": 0.099,
  "verdict": "PROCEED WITH DILIGENCE"
}
```
</details>

## Company C - PASS

PASS: 6 flags on FY26 - revenue 921.6 cr, net margin 1.02%, Piotroski 5/9, accrual ratio -0.023.
interest coverage (EBIT / interest), x: 1.18 vs threshold 2 (below; 2.6x -> 1.2x over 3 years).
net debt / EBITDA, x: 4.57 vs threshold 3 (above and rising; 3.9x -> 4.6x).
Ask management first: what is the covenant headroom, and which lender is the first to call.

*source: template (no API key)*

<details><summary>evidence</summary>

```json
{
  "company": "Company C",
  "currency": "INR crore",
  "years": [
    "FY22",
    "FY23",
    "FY24",
    "FY25",
    "FY26"
  ],
  "latest_year": "FY26",
  "latest": {
    "revenue": 921.6,
    "net_income": 9.4,
    "cfo": 33.0,
    "revenue_growth_pct": -0.39,
    "gross_margin_pct": 30.82,
    "ebitda_margin_pct": 11.85,
    "net_margin_pct": 1.02,
    "cash_conversion": 3.51,
    "dso_days": 75.01,
    "inventory_days": 85.01,
    "payable_days": 34.98,
    "cash_conversion_cycle_days": 125.04,
    "net_debt_to_ebitda": 4.57,
    "interest_coverage": 1.18,
    "capex_to_depreciation": 2.01,
    "free_cash_flow": -59.5,
    "other_income_pct_pbt": 22.4,
    "roce_pct": 6.24
  },
  "trend": {
    "cash_conversion": [
      1.95,
      1.55,
      1.81,
      2.01,
      3.51
    ],
    "dso_days": [
      60.01,
      63.0,
      67.0,
      71.01,
      75.01
    ],
    "net_debt_to_ebitda": [
      2.01,
      2.25,
      3.05,
      3.89,
      4.57
    ],
    "interest_coverage": [
      2.78,
      2.58,
      1.83,
      1.4,
      1.18
    ]
  },
  "flags": [
    {
      "flag": "interest_coverage_low",
      "label": "interest coverage (EBIT / interest), x",
      "severity": "high",
      "value": 1.18,
      "threshold": 2.0,
      "direction": "below",
      "detail": "2.6x -> 1.2x over 3 years"
    },
    {
      "flag": "net_debt_rising",
      "label": "net debt / EBITDA, x",
      "severity": "high",
      "value": 4.57,
      "threshold": 3.0,
      "direction": "above and rising",
      "detail": "3.9x -> 4.6x"
    },
    {
      "flag": "capex_funded_by_debt",
      "label": "free cash flow, cr, with capex above 1.5x depreciation and debt rising",
      "severity": "high",
      "value": -59.5,
      "threshold": 0,
      "direction": "below in 2+ of last 3 years",
      "detail": "capex/dep 2.0x"
    },
    {
      "flag": "revenue_flat",
      "label": "revenue 4-year CAGR, %",
      "severity": "medium",
      "value": 0.5,
      "threshold": 3,
      "direction": "below",
      "detail": "-0.39% in the latest year"
    },
    {
      "flag": "gross_margin_eroding",
      "label": "gross margin change over 3 years, bps",
      "severity": "medium",
      "value": -344.0,
      "threshold": -300,
      "direction": "below",
      "detail": "34.3% -> 30.8%"
    },
    {
      "flag": "working_capital_squeeze",
      "label": "cash conversion cycle change over 3 years, days",
      "severity": "medium",
      "value": 35.0,
      "threshold": 20,
      "direction": "above",
      "detail": "90 -> 125 days"
    }
  ],
  "flag_points": 9,
  "piotroski": {
    "score": 5,
    "out_of": 9,
    "passed": [
      "positive_roa",
      "positive_cfo",
      "cfo_exceeds_net_income",
      "current_ratio_rose",
      "no_new_shares"
    ]
  },
  "accrual_ratio": -0.023,
  "verdict": "PASS"
}
```
</details>
