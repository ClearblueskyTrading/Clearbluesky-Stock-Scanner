# ClearBlueSky - Institutional fundamentals helper
# Optional quality gates: use when Finviz/Elite returns data; skip gate if missing.

from typing import Dict, List, Optional, Tuple

# Finviz quote keys (vary by source; Elite may expose more)
# Common keys: ROE, Debt/Eq, Profit Margin, PEG, Beta, Inst Own
KEY_ROE = "ROE"
KEY_DEBT_EQ = "Debt/Eq"
KEY_PROFIT_MARGIN = "Profit Margin"
KEY_PEG = "PEG"
KEY_BETA = "Beta"
KEY_INST_OWN = "Inst Own"
KEY_SECTOR = "Sector"
KEY_SMA200 = "SMA200"
KEY_PRICE = "Price"
KEY_MARKET_CAP = "Market Cap"


def _parse_num(val, default=None):
    """Parse number from string (e.g. '15.2%' -> 15.2, '0.8' -> 0.8)."""
    if val is None or val == "" or val == "-" or (isinstance(val, float) and (val != val)):  # NaN
        return default
    try:
        s = str(val).strip().replace("%", "").replace(",", "")
        if not s:
            return default
        return float(s)
    except (TypeError, ValueError):
        return default


def _parse_inst_own(val) -> Optional[float]:
    """Parse institutional ownership (e.g. '45.2%' -> 45.2)."""
    return _parse_num(val)


def _parse_market_cap_millions(val) -> Optional[float]:
    """Parse market cap to millions. e.g. '1.2B' -> 1200, '500M' -> 500."""
    if val is None or val == "" or val == "-":
        return None
    try:
        s = str(val).strip().upper().replace(",", "")
        if "B" in s:
            return float(s.replace("B", "").strip()) * 1000
        if "M" in s:
            return float(s.replace("M", "").strip())
        return float(s) / 1e6  # assume raw number
    except (TypeError, ValueError):
        return None


def _get(quote: Dict, *keys):
    """First key that exists in quote (for dict or DataFrame row)."""
    for k in keys:
        try:
            v = quote.get(k)
            if v is not None and (not isinstance(v, str) or v.strip()):
                return v
        except (KeyError, AttributeError):
            continue
    return None


def get_fundamentals_from_quote(quote: Dict) -> Dict[str, Optional[float]]:
    """
    Extract optional fundamental metrics from a Finviz quote dict or DataFrame row.
    Returns dict with keys: roe, profit_margin, debt_equity, peg, beta, inst_own.
    Missing/unparseable values are None (caller skips that gate). Elite API may expose more.
    """
    out = {
        "roe": None,
        "profit_margin": None,
        "debt_equity": None,
        "peg": None,
        "beta": None,
        "inst_own": None,
        "sector": None,
        "sma200_pct": None,
        "price": None,
        "market_cap_millions": None,
    }
    if not quote:
        return out

    sector_val = _get(quote, KEY_SECTOR, "Sector")
    out["sector"] = (str(sector_val).strip() or None) if sector_val is not None else None

    # Try common key variants (finviz vs finvizfinance / Elite / DataFrame columns)
    roe = _get(quote, KEY_ROE, "ROE")
    out["roe"] = _parse_num(roe)

    pm = _get(quote, KEY_PROFIT_MARGIN, "Profit Margin", "Net Margin")
    out["profit_margin"] = _parse_num(pm)

    de = _get(quote, KEY_DEBT_EQ, "Debt/Eq", "LT Debt/Equity")
    out["debt_equity"] = _parse_num(de)

    peg = _get(quote, KEY_PEG, "PEG")
    out["peg"] = _parse_num(peg)

    beta = _get(quote, KEY_BETA, "Beta")
    out["beta"] = _parse_num(beta)

    io = _get(quote, KEY_INST_OWN, "Inst Own", "Institutional Ownership")
    out["inst_own"] = _parse_inst_own(io)

    sma200 = _get(quote, KEY_SMA200, "SMA200")
    out["sma200_pct"] = _parse_num(sma200)

    pr = _get(quote, KEY_PRICE, "Price")
    out["price"] = _parse_num(pr)

    mc = _get(quote, KEY_MARKET_CAP, "Market Cap")
    out["market_cap_millions"] = _parse_market_cap_millions(mc)

    return out


def check_trend_quality_gates(
    quote_or_row,
    config: Dict,
    is_dataframe_row: bool = False,
) -> Tuple[bool, List[str]]:
    """
    Apply institutional quality gates for Trend scan.
    quote_or_row: dict from finviz.get_stock or DataFrame row (has .get or column access).
    Returns (pass: bool, reasons: list of fail reasons).
    """
    if is_dataframe_row:
        # DataFrame row: may have different column names (e.g. Sector, ROE from screener)
        q = dict(quote_or_row) if hasattr(quote_or_row, "keys") else {}
    else:
        q = quote_or_row or {}
    fund = get_fundamentals_from_quote(q)
    reasons = []

    min_roe = config.get("trend_min_roe")
    if min_roe is not None and fund.get("roe") is not None and fund["roe"] < float(min_roe):
        reasons.append(f"ROE {fund['roe']} < {min_roe}")

    min_margin = config.get("trend_min_profit_margin")
    if min_margin is not None and fund.get("profit_margin") is not None and fund["profit_margin"] < float(min_margin):
        reasons.append(f"profit margin {fund['profit_margin']}% < {min_margin}%")

    max_de = config.get("trend_max_debt_equity")
    if max_de is not None and fund.get("debt_equity") is not None and fund["debt_equity"] > float(max_de):
        reasons.append(f"Debt/Equity {fund['debt_equity']} > {max_de}")

    max_peg = config.get("trend_max_peg_ratio")
    if max_peg is not None and fund.get("peg") is not None and fund["peg"] > float(max_peg):
        reasons.append(f"PEG {fund['peg']} > {max_peg}")

    max_beta = config.get("trend_max_beta")
    if max_beta is not None and fund.get("beta") is not None and fund["beta"] > float(max_beta):
        reasons.append(f"Beta {fund['beta']} > {max_beta}")

    min_inst = config.get("min_inst_ownership")
    if min_inst is not None and fund.get("inst_own") is not None and fund["inst_own"] < float(min_inst):
        reasons.append(f"Inst Own {fund['inst_own']}% < {min_inst}%")

    # Extension: price vs SMA200 (if both present)
    max_ext = config.get("trend_max_extension_sma200")
    if max_ext is not None and fund.get("sma200_pct") is not None and fund.get("price") is not None:
        # SMA200 is often given as a percentage or price; Finviz may give "% above SMA200" or we need to compute
        # If quote has "SMA200" as a percentage (e.g. "15.2" meaning 15.2% above), use that
        try:
            ext = float(fund["sma200_pct"])
            if ext > float(max_ext):
                reasons.append(f"Extension above SMA200 {ext}% > {max_ext}%")
        except (TypeError, ValueError):
            pass

    return len(reasons) == 0, reasons


def check_swing_quality_gates(quote: Dict, config: Dict) -> Tuple[bool, List[str]]:
    """Safety net for Swing: min profit margin, max debt/equity, min inst ownership."""
    fund = get_fundamentals_from_quote(quote)
    reasons = []

    min_margin = config.get("swing_min_profit_margin")
    if min_margin is not None and fund.get("profit_margin") is not None and fund["profit_margin"] < float(min_margin):
        reasons.append(f"profit margin {fund['profit_margin']}% < {min_margin}%")

    max_de = config.get("swing_max_debt_equity")
    if max_de is not None and fund.get("debt_equity") is not None and fund["debt_equity"] > float(max_de):
        reasons.append(f"Debt/Equity {fund['debt_equity']} > {max_de}")

    min_inst = config.get("min_inst_ownership")
    if min_inst is not None and fund.get("inst_own") is not None and fund["inst_own"] < float(min_inst):
        reasons.append(f"Inst Own {fund['inst_own']}% < {min_inst}%")

    return len(reasons) == 0, reasons


def check_emotional_liquidity_gates(quote: Dict, config: Dict) -> Tuple[bool, List[str]]:
    """Emotional: min market cap, min inst ownership only."""
    fund = get_fundamentals_from_quote(quote)
    reasons = []

    min_cap_m = config.get("emotional_min_market_cap_millions")
    if min_cap_m is not None and fund.get("market_cap_millions") is not None:
        if fund["market_cap_millions"] < float(min_cap_m):
            reasons.append(f"Market cap {fund['market_cap_millions']}M < {min_cap_m}M")

    min_inst = config.get("min_inst_ownership")
    if min_inst is not None and fund.get("inst_own") is not None and fund["inst_own"] < float(min_inst):
        reasons.append(f"Inst Own {fund['inst_own']}% < {min_inst}%")

    return len(reasons) == 0, reasons
