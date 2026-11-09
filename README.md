# Statement Reader

Every acquisition screen I have sat in opened the valuation model first. Hour one went to WACC debates and terminal growth, and the target's receivables — which had quietly doubled relative to sales over three years — came up on day four, from a junior who had been asked to tidy the data room. That is the wrong order. The first hour with a target's financials belongs to five ratios and the direction they are moving in. The model can wait; it is only as good as the cash flows you have not yet questioned.

This project does that first hour in a second. Three statements in, five years each; ratio red flags, a Piotroski-style score and an accrual ratio out; a verdict and the question to walk into the room with. It is a screen, not a valuation, and not advice — its job is to tell you which pages of the annual report to read before anyone opens a spreadsheet.

```
── Company B  [template (no API key)]
PROCEED WITH DILIGENCE: 4 flags on FY26 - revenue 1118.6 cr, net margin 7.82%, Piotroski 6/9, accrual ratio 0.099.
cash conversion (CFO / net income): 0.24 vs threshold 0.7 (below in 2+ of last 3 years; 3 of last 3 years below 0.7).
DSO rise over 3 years, %: 89.6 vs threshold 40 (above; 58 -> 110 days).
Ask management first: walk me through the receivables ageing and which customers are past 90 days.
```

That is the deterministic template. With an API key the same evidence pack goes to an LLM, which writes the memo in plainer English — and is then checked.

## How it works

1. **Statements.** Five fiscal years of income statement, balance sheet and cash-flow statement for three fictional Indian mid-size companies (₹ crore), each built around a story I have met in real data rooms: a healthy compounder; "profit without cash", where reported profit grows while operating cash flow lags, receivable days climb from 45 to 110 and other income props up PBT; and leverage creep, where revenue is flat, debt funds capex, interest coverage slides below 2x and suppliers get paid faster while customers pay slower. The statements are internally consistent — the balance sheet balances and the cash flow reconciles the change in cash — because the test file checks that they do.
2. **Engine.** Per year: growth, gross/EBITDA/net margin, cash conversion (CFO / net income), DSO, inventory and payable days, cash conversion cycle, net debt / EBITDA, interest coverage, capex / depreciation, free cash flow, other income as a share of PBT, ROCE. Nine red-flag rules, each with a threshold *and a direction* — cash conversion below 0.7 in two of the last three years, DSO up more than 40% over three years, coverage below 2x, net debt / EBITDA above 3 and rising, and so on. A Sloan-style accrual ratio and a nine-test Piotroski score sit alongside as single-number sanity checks. Flags are weighted and summed into PROCEED, PROCEED WITH DILIGENCE or PASS.
3. **Write.** The evidence pack — latest ratios, five-year trends of the four most telling ones, every fired flag with its actual value against its threshold, the score, the verdict — goes to an LLM with a strict brief: three to four lines, the two flags that matter most with their numbers, one question for management, **use only the numbers provided**.
4. **Verify.** Every number in the reply is parsed and checked against the evidence pack. If the model rounded 0.24 to "a quarter of profit" that is fine; if it wrote 0.3, or quoted a DSO it was not given, the memo is discarded and the template is used instead, and the output says so. In a screening memo a wrong number does not look wrong — it looks like diligence. That is exactly why the writer is not allowed to produce any.

## Run it

```bash
pip install -r requirements.txt
python statement_reader.py
```

Works with no API key — you get the template memos. For LLM-written memos set one of:

```bash
export GEMINI_API_KEY=...        # preferred; uses gemini-2.5-flash via REST
export ANTHROPIC_API_KEY=...     # uses the official anthropic SDK, claude-opus-5-5
```

Outputs: `screen.md` (memos + collapsible evidence packs per company) and `ratios.png` (cash conversion, DSO, net debt / EBITDA and interest coverage over five years, thresholds dashed). Tests: `python test_statement_reader.py`.

## What I'd change for production

- Replace the synthetic statements with a parser for the real thing — XBRL filings or the standardised tables a data vendor sells — and spend most of the effort on mapping "other income" and "trade receivables" correctly, because that is where the flags live and where every company's chart of accounts differs.
- Make the thresholds sector-relative. A 110-day DSO is a red flag for a consumer company and normal for an infrastructure EPC contractor; the rules should read against a peer distribution, not a constant.
- Log every fired flag against what diligence later found. After thirty screens you know which rules earn their place and which only generate questions — that is the feedback loop a rules engine never gets on its own.

Companion reading: [Understanding Financial Statements](https://nikunjkaushik.com/blog/financial_statements.html) and [How to Vet a Company for Acquisition](https://nikunjkaushik.com/blog/company_acquisition.html). Part of the [Building with AI](https://nikunjkaushik.com/projects.html) set on my site.
