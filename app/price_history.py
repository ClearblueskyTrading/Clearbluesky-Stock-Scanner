# ============================================================
# ClearBlueSky - 30-Day Price History
# ============================================================
# Fetches 30 days of OHLCV price history for scan tickers
# plus core leveraged ETFs. Fresh download every scan run.
# Used as a sanity check in reports and AI prompt.

import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

import yfinance as yf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Core leveraged / market ETFs always included alongside scan tickers
CORE_TICKERS = [
    # Leveraged bull ETFs
    "TQQQ", "SOXL", "SPXL", "NVDL",
    # Leveraged single-stock
    "TSLL", "NVDU", "AAPU", "AMZU", "MSFU", "GGLL", "METU", "CONL", "NFXL",
    # Market benchmarks
    "SPY", "QQQ", "DIA", "IWM",
]


def _fetch_one(ticker: str, period: str = "1mo") -> Optional[Dict]:
    """Fetch 30-day daily OHLCV for a single ticker. Returns dict or None."""
    try:
        df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True, timeout=30)
        if df is None or df.empty:
            return None
        # Handle MultiIndex columns from yfinance
        if hasattr(df.columns, 'levels'):
            df.columns = df.columns.get_level_values(0)
        rows = []
        for dt, row in df.iterrows():
            rows.append({
                "date": dt.strftime("%Y-%m-%d"),
                "open": round(float(row.get("Open", 0)), 2),
                "high": round(float(row.get("High", 0)), 2),
                "low": round(float(row.get("Low", 0)), 2),
                "close": round(float(row.get("Close", 0)), 2),
                "volume": int(row.get("Volume", 0)),
            })
        if not rows:
            return None
        # Summary stats
        closes = [r["close"] for r in rows]
        first_close = closes[0] if closes else 0
        last_close = closes[-1] if closes else 0
        high_30d = max(r["high"] for r in rows)
        low_30d = min(r["low"] for r in rows)
        pct_change = round(((last_close - first_close) / first_close) * 100, 2) if first_close else 0
        return {
            "ticker": ticker,
            "period": "30d",
            "last_close": last_close,
            "high_30d": high_30d,
            "low_30d": low_30d,
            "pct_change_30d": pct_change,
            "days": len(rows),
            "daily": rows,
        }
    except Exception:
        return None


def fetch_price_history(scan_tickers: List[str] = None, progress_callback=None) -> Dict:
    """
    Fetch 30-day price history for scan tickers + core leveraged/market ETFs.
    Returns dict keyed by ticker with OHLCV data and summary stats.
    """
    # Combine scan tickers with core tickers (deduplicate, preserve order)
    all_tickers = list(dict.fromkeys(
        [t.upper() for t in (scan_tickers or [])] + CORE_TICKERS
    ))

    if progress_callback:
        progress_callback(f"Fetching 30-day price history ({len(all_tickers)} tickers)...")

    results = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(_fetch_one, t): t for t in all_tickers}
        done = 0
        for future in as_completed(futures):
            ticker = futures[future]
            done += 1
            try:
                data = future.result(timeout=60)
                if data:
                    results[ticker] = data
            except Exception:
                pass

    if progress_callback:
        progress_callback(f"Price history: {len(results)}/{len(all_tickers)} tickers loaded.")

    return results


def format_price_history_for_prompt(history: Dict) -> str:
    """Format price history into a compact text block for the AI prompt."""
    if not history:
        return ""
    lines = [
        "",
        "═══════════════════════════════════════════════════",
        "30-DAY PRICE HISTORY (sanity check)",
        "═══════════════════════════════════════════════════",
        f"{'Ticker':<8} {'Last':>8} {'30d Chg':>8} {'30d High':>9} {'30d Low':>9} {'Days':>5}",
        "─" * 50,
    ]
    # Sort: scan tickers first (non-core), then core
    core_set = set(CORE_TICKERS)
    scan_first = sorted([t for t in history if t not in core_set], key=lambda x: x)
    core_sorted = sorted([t for t in history if t in core_set], key=lambda x: x)

    for ticker in scan_first + core_sorted:
        d = history[ticker]
        chg = d.get("pct_change_30d", 0)
        sign = "+" if chg >= 0 else ""
        lines.append(
            f"{ticker:<8} {d['last_close']:>8.2f} {sign}{chg:>6.1f}% {d['high_30d']:>9.2f} {d['low_30d']:>9.2f} {d['days']:>5}"
        )

    lines.append("")
    return "\n".join(lines)


def price_history_for_json(history: Dict) -> Dict:
    """Return a JSON-safe version (summary only, no daily rows to keep size down)."""
    if not history:
        return {}
    out = {}
    for ticker, d in history.items():
        out[ticker] = {
            "last_close": d["last_close"],
            "high_30d": d["high_30d"],
            "low_30d": d["low_30d"],
            "pct_change_30d": d["pct_change_30d"],
            "days": d["days"],
        }
    return out
