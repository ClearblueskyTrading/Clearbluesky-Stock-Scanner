# ============================================================
# ClearBlueSky - Watchlist Scanner v7.85
# ============================================================
# Scans only tickers in the user's watchlist.
# Two modes:
#   "down_pct" — stocks down 0–X% today (X = slider = max of range; emotional dip candidates)
#   "all"      — every watchlist ticker with full TA data
#
# Features:
#   - Real scoring (0–100) based on price action, volume, TA
#   - Sequential fetching with polite delays (rate-limit safe)
#   - Cancel support via threading.Event
#   - Full TA data: RSI, SMA200, ATR, analyst rating, open, etc.
#   - News headlines for enrichment pipeline

import time
import threading
from typing import List, Dict, Optional, Callable

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
    """Get today's change % from Finviz (e.g. '-5.2%' -> -5.2)."""
    val = stock.get("Change", "") or stock.get("change", "")
    if val is None or val == "" or val == "N/A":
        return None
    s = str(val).strip().replace(",", "").replace("%", "").strip()
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _score_watchlist_ticker(stock: dict, change_pct: float) -> int:
    """
    Score a watchlist ticker 0–100 based on multiple factors.
    Higher = more interesting setup.

    Scoring breakdown (100 total):
      - Change magnitude   (20 pts) — bigger dip = more opportunity
      - Relative volume    (20 pts) — institutional interest
      - RSI position       (15 pts) — oversold = bullish for bounce
      - SMA200 position    (15 pts) — above = healthy stock
      - Analyst rating     (15 pts) — buy/strong buy = conviction
      - Upside to target   (15 pts) — analyst price target headroom
    """
    score = 0

    # ── Change magnitude (20 pts) ──
    abs_change = abs(change_pct) if change_pct else 0
    if abs_change >= 5.0:
        score += 20
    elif abs_change >= 3.0:
        score += 15
    elif abs_change >= 2.0:
        score += 10
    elif abs_change >= 1.0:
        score += 5
    # Green stocks get some points too (momentum)
    if change_pct and change_pct > 0:
        if change_pct >= 3.0:
            score += 15
        elif change_pct >= 1.5:
            score += 10
        elif change_pct >= 0.5:
            score += 5

    # ── Relative volume (20 pts) ──
    rel_vol = _parse_num(stock.get("Rel Volume"), 0)
    if rel_vol >= 3.0:
        score += 20
    elif rel_vol >= 2.0:
        score += 15
    elif rel_vol >= 1.5:
        score += 10
    elif rel_vol >= 1.0:
        score += 5

    # ── RSI (15 pts) ──
    rsi = _parse_num(stock.get("RSI (14)"), 50)
    if rsi > 0:
        if rsi <= 30:       # oversold — great for dip
            score += 15
        elif rsi <= 40:
            score += 10
        elif rsi <= 50:
            score += 7
        elif rsi >= 70:     # overbought — caution but still notable
            score += 3

    # ── SMA200 position (15 pts) ──
    sma200_str = str(stock.get("SMA200", "")).replace("%", "").strip()
    try:
        sma200_pct = float(sma200_str)
        if sma200_pct > 10:      # well above
            score += 15
        elif sma200_pct > 0:     # above
            score += 10
        elif sma200_pct > -10:   # slightly below
            score += 5
        # deeply below = 0 pts
    except (ValueError, TypeError):
        pass

    # ── Analyst rating (15 pts) ──
    recom = _parse_num(stock.get("Recom"), 0)
    # Finviz: 1.0 = Strong Buy, 2.0 = Buy, 3.0 = Hold, 4.0 = Sell, 5.0 = Strong Sell
    if 0 < recom <= 1.5:
        score += 15
    elif recom <= 2.0:
        score += 12
    elif recom <= 2.5:
        score += 8
    elif recom <= 3.0:
        score += 4

    # ── Upside to target (15 pts) ──
    price = _parse_num(stock.get("Price"), 0)
    target = _parse_num(stock.get("Target Price"), 0)
    if price > 0 and target > 0:
        upside = ((target - price) / price) * 100
        if upside >= 30:
            score += 15
        elif upside >= 20:
            score += 12
        elif upside >= 10:
            score += 8
        elif upside >= 5:
            score += 5

    return min(100, max(0, score))


def _extract_ticker_data(ticker: str, stock: dict, change_pct: float, score: int) -> Dict:
    """Build a full data row from Finviz stock dict."""
    price = _parse_num(stock.get("Price"), 0)
    return {
        "ticker": ticker,
        "score": score,
        "Company": stock.get("Company", ticker),
        "Price": price,
        "price": price,
        "Open": _parse_num(stock.get("Open"), None),
        "Volume": stock.get("Volume", "N/A"),
        "Change": stock.get("Change", "N/A"),
        "change": stock.get("Change", "N/A"),
        "Sector": stock.get("Sector", "N/A"),
        "sector": stock.get("Sector", "N/A"),
        "Industry": stock.get("Industry", "N/A"),
        "industry": stock.get("Industry", "N/A"),
        "Market Cap": stock.get("Market Cap", "N/A"),
        "P/E": stock.get("P/E", "N/A"),
        "pe": stock.get("P/E", "N/A"),
        "Target Price": stock.get("Target Price", "N/A"),
        "target": stock.get("Target Price", "N/A"),
        "RSI (14)": stock.get("RSI (14)", "N/A"),
        "rsi": stock.get("RSI (14)", "N/A"),
        "SMA200": stock.get("SMA200", "N/A"),
        "sma200": stock.get("SMA200", "N/A"),
        "SMA50": stock.get("SMA50", "N/A"),
        "sma50": stock.get("SMA50", "N/A"),
        "SMA20": stock.get("SMA20", "N/A"),
        "Rel Volume": stock.get("Rel Volume", "N/A"),
        "rel_volume": stock.get("Rel Volume", "N/A"),
        "Recom": stock.get("Recom", "N/A"),
        "recom": stock.get("Recom", "N/A"),
        "Perf Week": stock.get("Perf Week", "N/A"),
        "perf_week": stock.get("Perf Week", "N/A"),
        "Perf Month": stock.get("Perf Month", "N/A"),
        "perf_month": stock.get("Perf Month", "N/A"),
        "Perf Quarter": stock.get("Perf Quarter", "N/A"),
        "perf_quarter": stock.get("Perf Quarter", "N/A"),
        "ATR": stock.get("ATR", "N/A"),
        "Volatility": stock.get("Volatility", "N/A"),
        "52W High": stock.get("52W High", "N/A"),
        "52W Low": stock.get("52W Low", "N/A"),
        "Avg Volume": stock.get("Avg Volume", "N/A"),
        "change_pct": change_pct,
    }


def _scan_watchlist_sequential(
    watchlist: List[str],
    progress: Callable,
    cancel_event: Optional[threading.Event],
    filter_fn: Optional[Callable] = None,
) -> List[Dict]:
    """
    Fetch watchlist tickers one at a time with a polite delay between each.
    No parallel workers — avoids Finviz rate-limit bans.

    filter_fn: optional callable(stock, change_pct) -> bool.  If provided,
               only tickers where filter_fn returns True are kept.
    """
    DELAY = 0.5   # seconds between each request — safe for Finviz
    MAX_CONSECUTIVE_FAIL = 20

    results = []
    total = len(watchlist)
    consecutive_failures = 0

    for i, ticker in enumerate(watchlist):
        if cancel_event and cancel_event.is_set():
            progress("Scan cancelled.")
            break

        progress(f"Checking ({i + 1}/{total}): {ticker}")

        try:
            stock = get_stock_safe(ticker, timeout=30.0, max_attempts=2)
        except Exception:
            stock = None

        if stock is None:
            consecutive_failures += 1
            if consecutive_failures >= MAX_CONSECUTIVE_FAIL:
                progress(f"Too many failures ({consecutive_failures}) — aborting (Finviz may be rate-limiting).")
                break
            time.sleep(DELAY)
            continue

        price = _parse_num(stock.get("Price", 0))
        if not price or price <= 0:
            time.sleep(DELAY)
            continue

        consecutive_failures = 0
        change_pct = _get_change_pct(stock) or 0.0

        # Apply optional filter
        if filter_fn and not filter_fn(stock, change_pct):
            time.sleep(DELAY)
            continue

        score = _score_watchlist_ticker(stock, change_pct)
        row = _extract_ticker_data(ticker, stock, change_pct, score)
        results.append(row)

        time.sleep(DELAY)

    return results


def run_watchlist_scan(
    progress_callback: Optional[Callable[[str], None]] = None,
    config: Optional[Dict] = None,
    cancel_event: Optional[threading.Event] = None,
) -> List[Dict]:
    """
    Watchlist scan — "Down X% today" mode.
    Only returns tickers down within the range 0% to X% from prior close.
    Sequential fetching (rate-limit safe), real scoring, full TA data.
    """
    cfg = config or load_config()
    watchlist = cfg.get("watchlist", []) or []
    watchlist = [str(t).strip().upper() for t in watchlist if t]
    if not watchlist:
        if progress_callback:
            progress_callback("Watchlist is empty. Add tickers in Watchlist first.")
        return []

    # Slider = max % down. Range is 0% to X% (down within that range, not exact X).
    pct_down_max = float(cfg.get("watchlist_pct_down_from_open", 5.0))
    pct_down_max = max(0.0, min(25.0, pct_down_max))
    pct_down_min = 0.01  # Include any down ticker; max is slider

    def progress(msg):
        if progress_callback:
            progress_callback(msg)

    progress(f"Scanning {len(watchlist)} watchlist tickers (down 0-{pct_down_max}% today)...")

    def _down_filter(stock, change_pct):
        """Only keep tickers that are down within the range 0% to X% (X = slider)."""
        if change_pct is None or change_pct >= 0:
            return False
        pct_down = abs(change_pct)
        return pct_down_min <= pct_down <= pct_down_max

    results = _scan_watchlist_sequential(watchlist, progress, cancel_event, filter_fn=_down_filter)
    results.sort(key=lambda x: -x["score"])
    progress(f"Found {len(results)} watchlist tickers down 0-{pct_down_max}% today.")
    return results


def run_watchlist_tickers_scan(
    progress_callback: Optional[Callable[[str], None]] = None,
    config: Optional[Dict] = None,
    cancel_event: Optional[threading.Event] = None,
) -> List[Dict]:
    """
    Watchlist scan — "All tickers" mode.
    Returns every watchlist ticker with full data and scoring.
    Sequential fetching (rate-limit safe), real scoring, full TA data.
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

    progress(f"Scanning {len(watchlist)} watchlist tickers (all, no filters)...")

    results = _scan_watchlist_sequential(watchlist, progress, cancel_event, filter_fn=None)
    results.sort(key=lambda x: -x["score"])
    progress(f"Loaded {len(results)} watchlist tickers.")
    return results
