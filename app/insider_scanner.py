# ============================================================
# ClearBlueSky - Insider Trading Scanner
# ============================================================
# Uses Finviz insider data (same source as elite.finviz.com/insidertrading).
# Options: latest, latest buys, latest sales, top week, top week buys, top week sales,
#          top owner trade, top owner buys, top owner sales.

from typing import List, Dict, Optional, Callable

from scan_settings import load_config


# Finvizfinance Insider option values (see https://finvizfinance.readthedocs.io/en/latest/insider.html)
INSIDER_OPTIONS = [
    "latest",
    "latest buys",
    "latest sales",
    "top week",
    "top week buys",
    "top week sales",
    "top owner trade",
    "top owner buys",
    "top owner sales",
]

DEFAULT_OPTION = "latest"


def run_insider_scan(
    progress_callback: Optional[Callable[[str], None]] = None,
    config: Optional[Dict] = None,
) -> List[Dict]:
    """
    Run Insider scan: fetch latest (or configured) insider transactions from Finviz.
    progress_callback: optional(msg) for UI updates.
    config: optional overrides; otherwise load_config() is used.
    Returns list of dicts with Ticker, Score (100), Owner, Relationship, Date, Transaction, Cost, Shares, Value for report.
    """
    cfg = config or load_config()
    option = (cfg.get("insider_option") or DEFAULT_OPTION).strip().lower()
    if option not in INSIDER_OPTIONS:
        option = DEFAULT_OPTION

    def progress(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    progress(f"Fetching insider data ({option})...")
    try:
        from finvizfinance.insider import Insider
    except ImportError:
        progress("Error: finvizfinance is required. Install with: pip install finvizfinance")
        return []

    try:
        finsider = Insider(option=option)
        df = finsider.get_insider()
    except Exception as e:
        progress(f"Insider fetch failed: {e}")
        return []

    if df is None or df.empty:
        progress("No insider transactions returned.")
        return []

    # Normalize column names (DataFrame may have spaces or different casing)
    col_map = {}
    for c in df.columns:
        cnorm = str(c).strip().lower().replace(" ", "_").replace("#", "").replace("$", "").replace("(", "").replace(")", "")
        col_map[c] = cnorm

    results = []
    seen = set()  # dedupe by (Ticker, Owner, Date, Transaction) to avoid same row multiple times
    for _, row in df.iterrows():
        try:
            ticker = None
            for orig, norm in col_map.items():
                if norm in ("ticker", "symbol"):
                    ticker = row.get(orig)
                    break
            if ticker is None and len(df.columns) > 0:
                ticker = row.iloc[0]
            ticker = str(ticker).strip().upper() if ticker is not None else ""
            if not ticker or ticker == "NAN":
                continue

            owner = ""
            for orig, norm in col_map.items():
                if norm == "owner":
                    owner = row.get(orig)
                    break
            owner = str(owner).strip() if owner is not None else ""

            relationship = ""
            for orig, norm in col_map.items():
                if norm == "relationship":
                    relationship = row.get(orig)
                    break
            relationship = str(relationship).strip() if relationship is not None else ""

            trans_date = ""
            for orig, norm in col_map.items():
                if norm == "date":
                    trans_date = row.get(orig)
                    break
            trans_date = str(trans_date).strip() if trans_date is not None else ""

            transaction = ""
            for orig, norm in col_map.items():
                if norm == "transaction":
                    transaction = row.get(orig)
                    break
            transaction = str(transaction).strip() if transaction is not None else ""

            cost = ""
            for orig, norm in col_map.items():
                if norm in ("cost", "price"):
                    cost = row.get(orig)
                    break
            cost = str(cost).strip() if cost is not None else ""

            shares = ""
            for orig, norm in col_map.items():
                if "shares" in norm and "total" not in norm:
                    shares = row.get(orig)
                    break
            shares = str(shares).strip() if shares is not None else ""

            value = ""
            for orig, norm in col_map.items():
                if norm == "value" or "value" in norm:
                    value = row.get(orig)
                    break
            value = str(value).strip() if value is not None else ""

            key = (ticker, owner[:30], trans_date, transaction[:20])
            if key in seen:
                continue
            seen.add(key)

            results.append({
                "Ticker": ticker,
                "ticker": ticker,
                "Score": 100,
                "score": 100,
                "Owner": owner,
                "Relationship": relationship,
                "Date": trans_date,
                "Transaction": transaction,
                "Cost": cost,
                "Shares": shares,
                "Value": value,
            })
        except Exception as e:
            continue

    progress(f"Found {len(results)} insider transaction(s).")
    return results
