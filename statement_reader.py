#!/usr/bin/env python3
"""Statement Reader - three statements in, ratio red flags and a short screening memo out.

1. Synthesize five fiscal years of income statement, balance sheet and cash-flow
   statement (INR crore) for three fictional mid-size Indian companies. Each embodies a
   known story: a healthy compounder, "profit without cash", and leverage creep. The
   statements are built so the balance sheet balances and the cash flow reconciles.
2. Compute the ratios an acquirer reads first: growth, margins, cash conversion,
   working-capital days, leverage, interest coverage, capex intensity, free cash flow,
   other-income dependence, ROCE - plus a Piotroski-style score and an accrual ratio.
3. Run the red-flag rules (threshold + direction each) and assemble an *evidence pack*
   per company: latest ratios, five-year trends, fired flags with value vs threshold,
   and a verdict in {PROCEED, PROCEED WITH DILIGENCE, PASS}.
4. Write a three-to-four line memo per company. With GEMINI_API_KEY or ANTHROPIC_API_KEY
   set, an LLM writes it - and every number it uses is checked against the evidence pack.
   If it invents one, the deterministic template is used. Without a key you get the
   template. This is a screen, not a valuation, and not advice.

Run:  python statement_reader.py
Out:  screen.md, ratios.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import llm  # noqa: E402

RNG = np.random.default_rng(11)
YEARS = ["FY22", "FY23", "FY24", "FY25", "FY26"]
TAX_RATE = 0.25

# Per-year drivers. Margins are shares of revenue; days are on revenue (DSO) or COGS (DIO, DPO).
COMPANIES = {
    "Company A": dict(  # healthy compounder
        rev0=700, growth=[.14] * 5, gm=[.42] * 5, opex=[.24] * 5, dep=[.04] * 5, other=[.01] * 5,
        debt0=360, debt=[300, 240, 180, 120, 60], rate=.09, dso=[48, 47, 46, 45, 45],
        dio=[60] * 5, dpo=[55] * 5, capex_x=[1.2] * 5, payout=.30, cash0=120, ppe0=260),
    "Company B": dict(  # profit without cash
        rev0=508, growth=[.18] * 5, gm=[.38] * 5, opex=[.26] * 5, dep=[.035] * 5,
        other=[.008, .017, .026, .036, .043], debt0=140, debt=[150, 170, 200, 240, 290],
        rate=.09, dso=[45, 58, 72, 90, 110], dio=[50] * 5, dpo=[45] * 5, capex_x=[1.1] * 5,
        payout=.20, cash0=60, ppe0=150),
    "Company C": dict(  # leverage creep
        rev0=895, growth=[.005, .015, -.01, .015, -.01], gm=[.35, .34, .33, .32, .31],
        opex=[.195] * 5, dep=[.05] * 5, other=[.003] * 5, debt0=330,
        debt=[360, 405, 460, 525, 600], rate=.095, dso=[60, 63, 67, 71, 75],
        dio=[70, 73, 77, 81, 85], dpo=[50, 46, 42, 38, 35], capex_x=[1.8, 1.9, 2.0, 2.0, 2.0],
        payout=.50, cash0=70, ppe0=420),
}


def r1(x: float) -> float:
    return float(round(x, 1))


def make_statements(c: dict) -> dict[str, pd.DataFrame]:
    """Income statement, balance sheet, cash flow. Primitives are rounded to INR 0.1 cr;
    every derived line is computed from rounded primitives, so the identities hold exactly."""
    rev_prev = c["rev0"]
    cogs0 = rev_prev * (1 - c["gm"][0])
    bs_prev = dict(cash=c["cash0"], ar=r1(rev_prev * c["dso"][0] / 365),
                   inv=r1(cogs0 * c["dio"][0] / 365), ppe=c["ppe0"],
                   ap=r1(cogs0 * c["dpo"][0] / 365), debt=c["debt0"])
    bs_prev["equity"] = r1(sum(bs_prev[k] for k in ("cash", "ar", "inv", "ppe")) - bs_prev["ap"] - bs_prev["debt"])
    inc, bal, cf = [], [], []
    for i, y in enumerate(YEARS):
        n = RNG.normal(size=4) * 0.01
        rev = r1(rev_prev * (1 + c["growth"][i] + n[0]))
        cogs = r1(rev * (1 - c["gm"][i] + 0.3 * n[1]))
        opex = r1(rev * (c["opex"][i] + 0.3 * n[2]))
        dep = r1(rev * c["dep"][i])
        other = r1(rev * c["other"][i])
        interest = r1(c["rate"] * (bs_prev["debt"] + c["debt"][i]) / 2)
        ebitda = r1(rev - cogs - opex)
        ebit = r1(ebitda - dep)
        pbt = r1(ebit + other - interest)
        tax = r1(max(pbt, 0) * TAX_RATE)
        ni = r1(pbt - tax)
        ar, invt = r1(rev * c["dso"][i] / 365), r1(cogs * c["dio"][i] / 365)
        ap = r1(cogs * c["dpo"][i] / 365)
        capex = r1(dep * c["capex_x"][i] * (1 + n[3]))
        div = r1(max(ni, 0) * c["payout"])
        cfo = r1(ni + dep - (ar - bs_prev["ar"]) - (invt - bs_prev["inv"]) + (ap - bs_prev["ap"]))
        cfi, cff = r1(-capex), r1(c["debt"][i] - bs_prev["debt"] - div)
        bs = dict(cash=r1(bs_prev["cash"] + cfo + cfi + cff), ar=ar, inv=invt,
                  ppe=r1(bs_prev["ppe"] + capex - dep), ap=ap, debt=c["debt"][i],
                  equity=r1(bs_prev["equity"] + ni - div))
        bs["total_assets"] = r1(bs["cash"] + ar + invt + bs["ppe"])
        bs["total_liab_equity"] = r1(ap + bs["debt"] + bs["equity"])
        inc.append(dict(year=y, revenue=rev, cogs=cogs, gross_profit=r1(rev - cogs), opex=opex,
                        ebitda=ebitda, depreciation=dep, ebit=ebit, other_income=other,
                        interest=interest, pbt=pbt, tax=tax, net_income=ni))
        bal.append(dict(year=y, **bs))
        cf.append(dict(year=y, cfo=cfo, capex=capex, cfi=cfi, debt_change=r1(c["debt"][i] - bs_prev["debt"]),
                       dividends=div, cff=cff, net_change_in_cash=r1(cfo + cfi + cff),
                       opening_cash=bs_prev["cash"], closing_cash=bs["cash"]))
        rev_prev, bs_prev = rev, bs
    frames = {k: pd.DataFrame(v).set_index("year") for k, v in (("is", inc), ("bs", bal), ("cf", cf))}
    frames["is"].attrs["revenue_prior"] = c["rev0"]
    return frames


def ratios(f: dict[str, pd.DataFrame]) -> pd.DataFrame:
    i, b, c = f["is"], f["bs"], f["cf"]
    rev_prev = pd.concat([pd.Series([i.attrs["revenue_prior"]]), i.revenue.iloc[:-1].reset_index(drop=True)]).values
    r = pd.DataFrame(index=i.index)
    r["revenue_growth_pct"] = (i.revenue.values / rev_prev - 1) * 100
    r["gross_margin_pct"] = i.gross_profit / i.revenue * 100
    r["ebitda_margin_pct"] = i.ebitda / i.revenue * 100
    r["net_margin_pct"] = i.net_income / i.revenue * 100
    r["cash_conversion"] = c.cfo / i.net_income
    r["dso_days"] = b.ar / i.revenue * 365
    r["inventory_days"] = b.inv / i.cogs * 365
    r["payable_days"] = b.ap / i.cogs * 365
    r["cash_conversion_cycle_days"] = r.dso_days + r.inventory_days - r.payable_days
    r["net_debt_to_ebitda"] = (b.debt - b.cash) / i.ebitda
    r["interest_coverage"] = i.ebit / i.interest
    r["capex_to_depreciation"] = c.capex / i.depreciation
    r["free_cash_flow"] = c.cfo - c.capex
    r["other_income_pct_pbt"] = i.other_income / i.pbt * 100
    r["roce_pct"] = i.ebit / (b.equity + b.debt) * 100
    return r.round(2)


def accrual_ratio(f: dict[str, pd.DataFrame]) -> float:
    """Sloan-style accruals: (net income - CFO) / average total assets, latest year."""
    i, b, c = f["is"], f["bs"], f["cf"]
    avg_assets = (b.total_assets.iloc[-1] + b.total_assets.iloc[-2]) / 2
    return round(float((i.net_income.iloc[-1] - c.cfo.iloc[-1]) / avg_assets), 3)


def piotroski(f: dict[str, pd.DataFrame]) -> dict:
    """Nine binary tests, latest year vs prior. Equity is retained earnings only here, so
    'no new shares' is granted (test 7) - say so rather than pretend it was tested."""
    i, b, c = f["is"], f["bs"], f["cf"]
    ta, cur = b.total_assets, b.cash + b.ar + b.inv
    roa = i.net_income / ta
    tests = {
        "positive_roa": roa.iloc[-1] > 0,
        "positive_cfo": c.cfo.iloc[-1] > 0,
        "roa_improved": roa.iloc[-1] > roa.iloc[-2],
        "cfo_exceeds_net_income": c.cfo.iloc[-1] > i.net_income.iloc[-1],
        "leverage_fell": (b.debt / ta).iloc[-1] < (b.debt / ta).iloc[-2],
        "current_ratio_rose": (cur / b.ap).iloc[-1] > (cur / b.ap).iloc[-2],
        "no_new_shares": True,
        "gross_margin_rose": (i.gross_profit / i.revenue).iloc[-1] > (i.gross_profit / i.revenue).iloc[-2],
        "asset_turnover_rose": (i.revenue / ta).iloc[-1] > (i.revenue / ta).iloc[-2],
    }
    return {"score": int(sum(tests.values())), "out_of": 9, "passed": [k for k, v in tests.items() if v]}


# Red-flag rules: (label, severity, threshold, direction, test(ratios) -> (fired, value, detail))
def _pct_change(s: pd.Series, back: int) -> float:
    return float((s.iloc[-1] / s.iloc[-1 - back] - 1) * 100)


def _cagr(growth_pct: pd.Series, years: int = 4) -> float:
    return float((1 + growth_pct.iloc[-years:] / 100).prod() ** (1 / years) * 100 - 100)


RULES = {
    "cash_conversion_low": ("cash conversion (CFO / net income)", "high", 0.7, "below in 2+ of last 3 years",
        lambda r: ((r.cash_conversion.iloc[-3:] < 0.7).sum() >= 2, r.cash_conversion.iloc[-1],
                   f"{int((r.cash_conversion.iloc[-3:] < 0.7).sum())} of last 3 years below 0.7")),
    "dso_rising": ("DSO rise over 3 years, %", "high", 40, "above",
        lambda r: (_pct_change(r.dso_days, 3) > 40, round(_pct_change(r.dso_days, 3), 1),
                   f"{r.dso_days.iloc[-4]:.0f} -> {r.dso_days.iloc[-1]:.0f} days")),
    "interest_coverage_low": ("interest coverage (EBIT / interest), x", "high", 2.0, "below",
        lambda r: (r.interest_coverage.iloc[-1] < 2, r.interest_coverage.iloc[-1],
                   f"{r.interest_coverage.iloc[-4]:.1f}x -> {r.interest_coverage.iloc[-1]:.1f}x over 3 years")),
    "net_debt_rising": ("net debt / EBITDA, x", "high", 3.0, "above and rising",
        lambda r: (r.net_debt_to_ebitda.iloc[-1] > 3 and r.net_debt_to_ebitda.iloc[-1] > r.net_debt_to_ebitda.iloc[-2],
                   r.net_debt_to_ebitda.iloc[-1], f"{r.net_debt_to_ebitda.iloc[-2]:.1f}x -> {r.net_debt_to_ebitda.iloc[-1]:.1f}x")),
    "capex_funded_by_debt": ("free cash flow, cr, with capex above 1.5x depreciation and debt rising", "high", 0,
        "below in 2+ of last 3 years",
        lambda r: ((r.free_cash_flow.iloc[-3:] < 0).sum() >= 2 and r.capex_to_depreciation.iloc[-1] > 1.5
                   and r.net_debt_to_ebitda.iloc[-1] > r.net_debt_to_ebitda.iloc[-3],
                   r.free_cash_flow.iloc[-1], f"capex/dep {r.capex_to_depreciation.iloc[-1]:.1f}x")),
    "other_income_dependence": ("other income as % of PBT", "medium", 30, "above",
        lambda r: (r.other_income_pct_pbt.iloc[-1] > 30, r.other_income_pct_pbt.iloc[-1],
                   f"{r.other_income_pct_pbt.iloc[-4]:.0f}% -> {r.other_income_pct_pbt.iloc[-1]:.0f}% over 3 years")),
    "revenue_flat": ("revenue 4-year CAGR, %", "medium", 3, "below",
        lambda r: (_cagr(r.revenue_growth_pct) < 3, round(_cagr(r.revenue_growth_pct), 1),
                   f"{r.revenue_growth_pct.iloc[-1]:g}% in the latest year")),
    "gross_margin_eroding": ("gross margin change over 3 years, bps", "medium", -300, "below",
        lambda r: ((r.gross_margin_pct.iloc[-1] - r.gross_margin_pct.iloc[-4]) * 100 < -300,
                   round((r.gross_margin_pct.iloc[-1] - r.gross_margin_pct.iloc[-4]) * 100),
                   f"{r.gross_margin_pct.iloc[-4]:.1f}% -> {r.gross_margin_pct.iloc[-1]:.1f}%")),
    "working_capital_squeeze": ("cash conversion cycle change over 3 years, days", "medium", 20, "above",
        lambda r: (r.cash_conversion_cycle_days.iloc[-1] - r.cash_conversion_cycle_days.iloc[-4] > 20,
                   round(r.cash_conversion_cycle_days.iloc[-1] - r.cash_conversion_cycle_days.iloc[-4], 1),
                   f"{r.cash_conversion_cycle_days.iloc[-4]:.0f} -> {r.cash_conversion_cycle_days.iloc[-1]:.0f} days")),
}
POINTS = {"high": 2, "medium": 1}


def run_rules(r: pd.DataFrame) -> list[dict]:
    out = []
    for fid, (label, sev, thr, direction, test) in RULES.items():
        fired, value, detail = test(r)
        if fired:
            out.append({"flag": fid, "label": label, "severity": sev, "value": float(value),
                        "threshold": thr, "direction": direction, "detail": detail})
    return sorted(out, key=lambda x: (x["severity"] != "high", list(RULES).index(x["flag"])))


def verdict(flags: list[dict]) -> tuple[str, int]:
    pts = sum(POINTS[f["severity"]] for f in flags)
    highs = sum(f["severity"] == "high" for f in flags)
    if highs >= 3 or pts >= 7:
        return "PASS", pts
    return ("PROCEED WITH DILIGENCE" if pts >= 2 else "PROCEED"), pts


TREND = ["cash_conversion", "dso_days", "net_debt_to_ebitda", "interest_coverage"]


def evidence_for(name: str, f: dict[str, pd.DataFrame]) -> dict:
    r = ratios(f)
    flags = run_rules(r)
    v, pts = verdict(flags)
    return {"company": name, "currency": "INR crore", "years": YEARS, "latest_year": YEARS[-1],
            "latest": {"revenue": float(f["is"].revenue.iloc[-1]), "net_income": float(f["is"].net_income.iloc[-1]),
                       "cfo": float(f["cf"].cfo.iloc[-1]), **r.iloc[-1].to_dict()},
            "trend": {k: [float(x) for x in r[k]] for k in TREND},
            "flags": flags, "flag_points": pts, "piotroski": piotroski(f),
            "accrual_ratio": accrual_ratio(f), "verdict": v}


ASK_FIRST = {
    "cash_conversion_low": "walk me through the receivables ageing and which customers are past 90 days",
    "dso_rising": "which customers' terms changed, and how much of the latest year's revenue is still uncollected",
    "interest_coverage_low": "what is the covenant headroom, and which lender is the first to call",
    "other_income_dependence": "what exactly is in other income, and how much of it is recurring cash",
    "net_debt_rising": "what is the plan to bring leverage down without cutting capex",
    "capex_funded_by_debt": "what did the borrowed capex buy, and when does it start earning",
    "revenue_flat": "what has changed in the market that lets you grow again",
    "gross_margin_eroding": "is it input cost or pricing power, and who is taking your share",
    "working_capital_squeeze": "why are suppliers being paid faster while customers pay slower",
}


def fmt_flag(fl: dict) -> str:
    return (f"{fl['label']}: {fl['value']:g} vs threshold {fl['threshold']:g} ({fl['direction']}; "
            f"{fl['detail']}).")


def template_memo(ev: dict) -> str:
    la, pi = ev["latest"], ev["piotroski"]
    lines = [f"{ev['verdict']}: {len(ev['flags'])} flags on {ev['latest_year']} - revenue {la['revenue']:g} cr, "
             f"net margin {la['net_margin_pct']:g}%, Piotroski {pi['score']}/{pi['out_of']}, "
             f"accrual ratio {ev['accrual_ratio']:g}."]
    if ev["flags"]:
        lines += [fmt_flag(fl) for fl in ev["flags"][:2]]
        ask = ASK_FIRST[ev["flags"][0]["flag"]]
    else:
        lines.append(f"Cash conversion {la['cash_conversion']:g}, net debt/EBITDA {la['net_debt_to_ebitda']:g}, "
                     f"interest coverage {la['interest_coverage']:g}x, ROCE {la['roce_pct']:g}%.")
        ask = (f"what sustains {la['revenue_growth_pct']:g}% growth with capex at "
               f"{la['capex_to_depreciation']:g}x depreciation, and for how long")
    lines.append(f"Ask management first: {ask}.")
    return "\n".join(lines)


SYSTEM = """You write a three-to-four line screening memo on a company's financial statements for an acquirer.
Line 1: the verdict and the overall picture in one sentence.
Lines 2-3: the two flags that matter most, each with its actual value and the threshold it crossed.
Last line: starts with "Ask management first:" and gives ONE question.
Use ONLY numbers present in the evidence. Never compute, re-round, or add numbers. Plain English, no jargon.
This is a screen, not a valuation - do not give a price or a recommendation to buy."""


def narrate(ev: dict) -> tuple[str, str]:
    text = llm.complete(SYSTEM, json.dumps(ev, indent=2), max_tokens=320)
    if text is None:
        return template_memo(ev), "template (no API key)"
    bad = llm.unpinned(text, ev)
    if bad:
        return template_memo(ev), f"template (LLM invented numbers: {sorted(bad)})"
    return text, f"llm ({llm.provider()})"


def plot(packs: list[dict]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker
    panels = [("cash_conversion", "Cash conversion (CFO / net income)", 0.7, 2.6),
              ("dso_days", "Receivable days (DSO)", None, None),
              ("net_debt_to_ebitda", "Net debt / EBITDA", 3.0, None),
              ("interest_coverage", "Interest coverage (EBIT / interest), log scale", 2.0, None)]
    colours, markers = ["#4A6FA5", "#B8740F", "#8E5BB0"], ["o", "s", "^"]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for ax, (key, title, thr, cap) in zip(axes.flat, panels):
        for ev, col, mk in zip(packs, colours, markers):
            ys = ev["trend"][key]
            ax.plot(YEARS, ys, color=col, lw=2, marker=mk, ms=5, label=ev["company"])
            end = min(ys[-1], cap) if cap else ys[-1]
            tag = ev["company"][-1] + (f" off scale ({ys[-1]:g})" if cap and ys[-1] > cap else "")
            ax.annotate(tag, (YEARS[-1], end), xytext=(6, 0), textcoords="offset points",
                        va="center", fontsize=8, color="#444", annotation_clip=False)
        if cap:
            ax.set_ylim(0, cap)
        if key == "interest_coverage":
            ax.set_yscale("log")
            ax.set_yticks([1, 2, 5, 10, 25])
            ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        if thr is not None:
            ax.axhline(thr, color="#d9534f", ls="--", lw=1.2)
            ax.text(0.15, thr, f"flag {thr:g}", color="#d9534f", fontsize=8, va="bottom", ha="center",
                    transform=ax.get_yaxis_transform())
        ax.set_title(title, fontsize=10)
        ax.grid(alpha=0.2)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0, 0].legend(fontsize=8, frameon=False)
    fig.suptitle("Five-year ratio trends - dashed = red-flag threshold", fontsize=11)
    plt.tight_layout()
    fig.subplots_adjust(right=0.93)
    plt.savefig("ratios.png", dpi=130)


def main() -> None:
    packs = [evidence_for(name, make_statements(spec)) for name, spec in COMPANIES.items()]
    print(f"{len(packs)} companies x {len(YEARS)} fiscal years (INR crore) · {len(RULES)} red-flag rules · "
          f"LLM provider: {llm.provider()}\n")
    out = ["# Financial statement screen", "",
           "Ratio red flags, Piotroski score and accrual ratio on five years of synthetic statements. "
           f"Memos written by: {llm.provider()}; every number verified against the evidence pack. "
           "A screen, not a valuation, and not advice.", ""]
    for ev in packs:
        memo, src = narrate(ev)
        print(f"── {ev['company']}  [{src}]")
        print(memo, "\n")
        out += [f"## {ev['company']} - {ev['verdict']}", "", memo, "", f"*source: {src}*", "",
                "<details><summary>evidence</summary>", "", "```json",
                json.dumps(ev, indent=2), "```", "</details>", ""]
    Path("screen.md").write_text("\n".join(out), encoding="utf-8")
    plot(packs)
    print("wrote screen.md and ratios.png")


if __name__ == "__main__":
    main()
