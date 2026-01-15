from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
import requests
import pandas as pd
import numpy as np

SEC_USER_AGENT = "Andrew Ignatescu (atig@bu.edu)"
SEC_HEADERS = {
    "User-Agent": SEC_USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov",
}

TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json"


def _get_json(url: str, headers: Dict[str, str]) -> Dict[str, Any]:
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()


def ticker_to_cik10(ticker: str) -> str:
    data = _get_json(TICKER_MAP_URL, headers={"User-Agent": SEC_USER_AGENT})
    t = ticker.upper()
    for _, rec in data.items():
        if rec.get("ticker", "").upper() == t:
            return f"{int(rec['cik_str']):010d}"
    raise ValueError(f"Ticker not found in SEC map: {ticker}")


def fetch_companyfacts(cik10: str) -> Dict[str, Any]:
    return _get_json(COMPANY_FACTS_URL.format(cik10=cik10), headers=SEC_HEADERS)


def pick_latest_fy_usd(facts: Dict[str, Any], tag: str) -> Optional[Tuple[int, float]]:
    try:
        items = facts["facts"]["us-gaap"][tag]["units"]["USD"]
    except KeyError:
        return None

    annual = [x for x in items if x.get("fp") == "FY" and isinstance(x.get("val"), (int, float))]
    if not annual:
        return None

    latest = sorted(annual, key=lambda x: (x.get("end", ""), x.get("filed", "")))[-1]
    fy = latest.get("fy")
    if fy is None:
        end = str(latest.get("end", "0000-01-01"))
        fy = int(end[:4]) if end[:4].isdigit() else None
    if fy is None:
        return None
    return int(fy), float(latest["val"])


def get_fy_value(facts: Dict[str, Any], tag: str) -> float:
    out = pick_latest_fy_usd(facts, tag)
    return float(out[1]) if out else 0.0


def get_fy_year(facts: Dict[str, Any], primary_tag: str = "Revenues") -> int:
    out = pick_latest_fy_usd(facts, primary_tag)
    if out:
        return int(out[0])
    out2 = pick_latest_fy_usd(facts, "Assets")
    if out2:
        return int(out2[0])
    raise ValueError("Could not determine latest fiscal year.")


@dataclass
class BaseInputs:
    fiscal_year: int
    revenue: float
    net_income: float
    interest_expense: float
    tax_expense: float
    cash: float
    current_assets: float
    current_liabilities: float
    long_term_debt: float
    short_term_debt: float
    total_debt: float
    operating_cf: float
    capex: float
    ebitda_proxy: float


def build_base_inputs(ticker: str) -> BaseInputs:
    cik10 = ticker_to_cik10(ticker)
    facts = fetch_companyfacts(cik10)

    fy = get_fy_year(facts)

    revenue = get_fy_value(facts, "Revenues")
    net_income = get_fy_value(facts, "NetIncomeLoss")
    interest = get_fy_value(facts, "InterestExpense")
    tax_exp = get_fy_value(facts, "IncomeTaxExpenseBenefit")

    cash = get_fy_value(facts, "CashAndCashEquivalentsAtCarryingValue")
    current_assets = get_fy_value(facts, "AssetsCurrent")
    current_liabilities = get_fy_value(facts, "LiabilitiesCurrent")

    ltd = get_fy_value(facts, "LongTermDebtNoncurrent")
    std = get_fy_value(facts, "DebtCurrent")
    total_debt = get_fy_value(facts, "Debt")
    if total_debt <= 0:
        total_debt = max(0.0, ltd + std)

    ocf = get_fy_value(facts, "NetCashProvidedByUsedInOperatingActivities")
    capex = get_fy_value(facts, "PaymentsToAcquirePropertyPlantAndEquipment")
    if capex > 0:
        capex = -capex

    ebit = get_fy_value(facts, "OperatingIncomeLoss")
    da = get_fy_value(facts, "DepreciationDepletionAndAmortization")
    ebitda = ebit + da if (ebit or da) else max(0.0, net_income + interest + tax_exp)

    return BaseInputs(
        fiscal_year=fy,
        revenue=revenue,
        net_income=net_income,
        interest_expense=interest,
        tax_expense=tax_exp,
        cash=cash,
        current_assets=current_assets,
        current_liabilities=current_liabilities,
        long_term_debt=ltd,
        short_term_debt=std,
        total_debt=total_debt,
        operating_cf=ocf,
        capex=capex,
        ebitda_proxy=ebitda,
    )


def prompt_str(label: str, default: str) -> str:
    raw = input(f"{label} (default {default}): ").strip()
    return raw if raw else default


def prompt_float(label: str, default: float) -> float:
    raw = input(f"{label} (default {default}): ").strip()
    return float(raw) if raw else float(default)


def safe_div(a: float, b: float) -> float:
    return a / b if b and abs(b) > 1e-12 else float("nan")


def run_stress(base: BaseInputs, rev_shock: float, margin_shock: float, rate_shock: float, wc_shock: float, capex_shock: float, cash_draw: float) -> Dict[str, float]:
    rev1 = base.revenue * (1 - rev_shock)
    margin0 = safe_div(base.ebitda_proxy, base.revenue)
    ebitda1 = max(0.0, rev1 * (margin0 - margin_shock))

    base_rate = safe_div(base.interest_expense, base.total_debt)
    interest1 = base.total_debt * max(0.0, base_rate + rate_shock)

    wc_hit = wc_shock * base.revenue
    ocf1 = (base.operating_cf or base.net_income) - wc_hit

    capex1 = (base.capex or -0.03 * base.revenue) * (1 + capex_shock)
    fcf1 = ocf1 + capex1

    cash1 = base.cash - cash_draw + fcf1
    ca1 = base.current_assets - wc_hit
    cl1 = base.current_liabilities + wc_hit

    net_debt = max(0.0, base.total_debt - cash1)

    return {
        "Revenue": rev1,
        "EBITDA": ebitda1,
        "Interest": interest1,
        "FCF": fcf1,
        "Cash End": cash1,
        "Current Ratio": safe_div(ca1, cl1),
        "Net Debt / EBITDA": safe_div(net_debt, ebitda1),
        "EBITDA / Interest": safe_div(ebitda1, interest1),
    }


def covenant_checks(row, max_lev, min_cov, min_cr, min_cash):
    lev = row["Net Debt / EBITDA"]
    cov = row["EBITDA / Interest"]
    cr = row["Current Ratio"]
    cash = row["Cash End"]

    def ok(x):
        return pd.notna(x) and np.isfinite(x)

    return {
        "Leverage Pass": ok(lev) and lev <= max_lev,
        "Coverage Pass": ok(cov) and cov >= min_cov,
        "Current Ratio Pass": ok(cr) and cr >= min_cr,
        "Cash Pass": ok(cash) and cash >= min_cash,
        "Overall Pass": ok(lev) and ok(cov) and ok(cr) and ok(cash)
        and lev <= max_lev and cov >= min_cov and cr >= min_cr and cash >= min_cash
    }


if __name__ == "__main__":
    print("\n=== Liquidity & Covenant Stress Test ===\n")
    ticker = prompt_str("Ticker", "JPM")

    base = build_base_inputs(ticker)

    max_lev = prompt_float("Max Net Debt / EBITDA", 4.0)
    min_cov = prompt_float("Min EBITDA / Interest", 3.0)
    min_cr = prompt_float("Min Current Ratio", 1.1)
    min_cash = prompt_float("Minimum Cash", 0.0)
    cash_draw = prompt_float("Immediate Cash Draw", 0.0)

    scenarios = {
        "Base": (0.0, 0.0, 0.0, 0.0, 0.0),
        "Mild": (0.05, 0.02, 0.01, 0.01, 0.05),
        "Severe": (0.15, 0.05, 0.02, 0.03, 0.10),
    }

    rows = []
    for name, s in scenarios.items():
        out = run_stress(base, *s, cash_draw)
        out["Scenario"] = name
        rows.append(out)

    df = pd.DataFrame(rows).set_index("Scenario")
    checks = df.apply(lambda r: covenant_checks(r, max_lev, min_cov, min_cr, min_cash), axis=1)
    out = pd.concat([df, pd.DataFrame(list(checks), index=df.index)], axis=1)

    print("\n", out.to_string(float_format=lambda x: f"{x:,.3f}"))
