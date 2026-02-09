# ============================================================
# ClearBlueSky - Watchlist Scanner
# ============================================================
# Scans only tickers in the user's watchlist.
# Filters by: today's Change % (down from prior close) 1–25% — big-name dips that often bounce in a few days.

import time
from typing import List, Dict, Optional, Callable

import finviz
from scan_settings import load_config
from finviz_safe import get_stock_safe


def _parse_num(s, default=0.0) -> float:
    if s is None:
        return default
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip().replace(",", "").replace("%", "").strip()
    mult = 1.0
    if s.upper().endswith("K"):
        mult = 1000.0
        s = s[:-1].strip()
    elif s.upper().endswith("M"):
        mult = 1_000_000.0
        s = s[:-1].strip()
    elif s.upper().endswith("B"):
        mult = 1_000_000_000.0
        s = s[:-1].strip()
    try:
        return float(s) * mult
    except (TypeError, ValueError):
        return default


def _get_change_pct(stock: dict) -> Optional[float]:
    """Get today's change % from Finviz (e.g. '-5.2%' -> -5.2). Down from prior close."""
    val = stock.get("Change", "") or stock.get("change", "")
    if val is None or val == "" or val == "N/A":
        return None
    s = str(val).strip().replace(",", "").replace("%", "").strip()
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def run_watchlist_scan(
    progress_callback: Optional[Callable[[str], None]] = None,
    config: Optional[Dict] = None,
) -> List[Dict]:
    """
    Run Watchlist scan: only tickers in the user's watchlist that are
    down today (Change % from prior close) between X% and 25%.
    progress_callback: optional(msg) for UI updates.
    config: optional overrides; otherwise load_config() is used.
    Returns list of dicts with Ticker, Score (100), and fields for report.
    """
    cfg = config or load_config()
    watchlist = cfg.get("watchlist", []) or []
    watchlist = [str(t).strip().upper() for t in watchlist if t]
    if not watchlist:
        if progress_callback:
            progress_callback("Watchlist is empty. Add tickers in Watchlist first.")
        return []

    pct_down_min = float(cfg.get("watchlist_pct_down_from_open", 5.0))
    pct_down_min = max(1.0, min(25.0, pct_down_min))
    pct_down_max = 25.0

    def progress(msg):
        if progress_callback:
            progress_callback(msg)

    progress(f"Scanning {len(watchlist)} watchlist tickers ({pct_down_min}–{pct_down_max}% down today)...")
    results = []
    total = len(watchlist)
    for i, ticker in enumerate(watchlist):
        if progress_callback:
            progress(f"Checking ({i+1}/{total}): {ticker}")
        try:
            stock = get_stock_safe(ticker, timeout=30.0, max_attempts=3)
            if not stock:
                continue
            price = _parse_num(stock.get("Price", 0))
            if not price or price <= 0:
                continue
            # Filter by today's Change % (down from prior close) — 1–25% down
            change_pct = _get_change_pct(stock)
            if change_pct is None or change_pct >= 0:
                continue
            pct_down = abs(change_pct)
            if pct_down < pct_down_min or pct_down > pct_down_max:
                continue
            vol_str = stock.get("Volume", "N/A")
            change_str = stock.get("Change", "N/A")
            results.append({
                "Ticker": ticker,
                "ticker": ticker,
                "Score": 100,
                "score": 100,
                "Company": stock.get("Company", ticker),
                "Price": price,
                "Volume": vol_str,
                "Change": change_str,
                "Open": None,
                "Sector": stock.get("Sector", "N/A"),
                "Industry": stock.get("Industry", "N/A"),
            })
        except Exception:
            continue
        time.sleep(0.15)
    progress(f"Found {len(results)} watchlist tickers {pct_down_min}–{pct_down_max}% down today.")
    return results


def run_watchlist_tickers_scan(
    progress_callback: Optional[Callable[[str], None]] = None,
    config: Optional[Dict] = None,
) -> List[Dict]:
    """
    Scan watchlist tickers only — no filters. Fetches current data for every ticker
    on the watchlist and returns them all for the report.
    progress_callback: optional(msg) for UI updates.
    config: optional overrides; otherwise load_config() is used.
    Returns list of dicts with Ticker, Score (100), and fields for report.
    """
    cfg = config or load_config()
    watchlist = cfg.get("watchlist", []) or []
    watchlist = [str(t).strip().upper() for t in watchlist if t]
    if not watchlist:
        if progress_callback:
            progress_callback("Watchlist is empty. Add tickers in Watchlist first.")
        return []

    def progress(msg):
        if progress_callback:
            progress_callback(msg)

    progress(f"Scanning {len(watchlist)} watchlist tickers (no filters)...")
    results = []
    total = len(watchlist)
    for i, ticker in enumerate(watchlist):
        if progress_callback:
            progress(f"Checking ({i+1}/{total}): {ticker}")
        try:
            stock = get_stock_safe(ticker, timeout=30.0, max_attempts=3)
            if not stock:
                continue
            price = _parse_num(stock.get("Price", 0))
            if not price or price <= 0:
                continue
            vol_str = stock.get("Volume", "N/A")
            change_str = stock.get("Change", "N/A")
            results.append({
                "Ticker": ticker,
                "ticker": ticker,
                "Score": 100,
                "score": 100,
                "Company": stock.get("Company", ticker),
                "Price": price,
                "Volume": vol_str,
                "Change": change_str,
                "Open": None,
                "Sector": stock.get("Sector", "N/A"),
                "Industry": stock.get("Industry", "N/A"),
            })
        except Exception:
            continue
        time.sleep(0.15)
    progress(f"Found {len(results)} watchlist tickers.")
    return results
