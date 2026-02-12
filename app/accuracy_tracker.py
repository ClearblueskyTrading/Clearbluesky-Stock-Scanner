# ============================================================
# ClearBlueSky - Accuracy Tracker
# ============================================================
# Compares past scan picks against current prices to calculate
# hits, misses, and accuracy rating.  Runs on startup and
# after each scan to keep the main GUI updated.
#
# HIT  = stock price went UP from flagged price (any amount)
# MISS = stock price went DOWN from flagged price
# Accuracy % = hits / (hits + misses) * 100
#
# Only evaluates picks that are 1-5 trading days old (the app's
# swing hold window).  Skips same-day picks (no time to move).
#
# Rolling history: uses ~20 trading days (~30 calendar days).

import json

LOOKBACK_TRADING_DAYS = 20
LOOKBACK_CALENDAR_DAYS = 30  # ~20 trading days (20 * 365/252)

import os
from collections import defaultdict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _get_current_prices(tickers: List[str]) -> Dict[str, float]:
    """Fetch latest price for a batch of tickers. Failover: yfinance > finviz > alpaca."""
    prices = {}
    if not tickers:
        return prices
    try:
        from data_failover import get_price_volume_batch
        pv = get_price_volume_batch(tickers)
        for t in tickers:
            if t in pv and pv[t].get("price") and pv[t]["price"] > 0:
                prices[t] = round(float(pv[t]["price"]), 2)
    except Exception:
        pass
    return prices


def calculate_accuracy(reports_dir: str = None, lookback_days: int = LOOKBACK_CALENDAR_DAYS) -> Dict:
    """
    Calculate accuracy by comparing past scan picks to current prices.
    
    Returns dict with:
      - hits: int (price went up)
      - misses: int (price went down or flat)
      - accuracy_pct: float (0-100)
      - total_evaluated: int
      - by_scan_type: {scan_type: {hits, misses, accuracy_pct}}
      - details: list of {ticker, scan_type, flagged_price, current_price, change_pct, result}
      - last_updated: timestamp
    """
    if reports_dir is None:
        reports_dir = os.path.join(BASE_DIR, "reports")
    
    history_path = os.path.join(reports_dir, "scan_history.json")
    if not os.path.exists(history_path):
        return {"hits": 0, "misses": 0, "accuracy_pct": 0, "total_evaluated": 0,
                "by_scan_type": {}, "details": [], "last_updated": "", "status": "no_history"}
    
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
        if not isinstance(history, list):
            history = [history]
    except Exception:
        return {"hits": 0, "misses": 0, "accuracy_pct": 0, "total_evaluated": 0,
                "by_scan_type": {}, "details": [], "last_updated": "", "status": "load_error"}
    
    # Collect picks from 1-N days ago (skip today — no time to move)
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    cutoff = now - timedelta(days=lookback_days)
    
    picks = []  # list of {ticker, flagged_price, scan_type, scan_date}
    seen = set()  # dedupe same ticker/date combos
    
    for entry in history:
        timestamp = entry.get("timestamp", "")
        scan_type = entry.get("scan_type", "Unknown")
        try:
            scan_date = datetime.strptime(timestamp[:10], "%Y-%m-%d")
        except Exception:
            continue
        
        date_str = scan_date.strftime("%Y-%m-%d")
        
        # Skip today's scans and scans older than lookback
        if date_str == today_str:
            continue
        if scan_date < cutoff:
            continue
        
        for s in entry.get("stocks", []):
            ticker = s.get("ticker", "")
            price = s.get("price")
            if not ticker or price in (None, "N/A", "", 0):
                continue
            try:
                flagged_price = float(price)
            except (ValueError, TypeError):
                continue
            
            key = f"{ticker}_{date_str}"
            if key in seen:
                continue
            seen.add(key)
            
            picks.append({
                "ticker": ticker,
                "flagged_price": flagged_price,
                "scan_type": scan_type,
                "scan_date": date_str,
                "score": s.get("score", 0),
            })
    
    if not picks:
        return {"hits": 0, "misses": 0, "accuracy_pct": 0, "total_evaluated": 0,
                "by_scan_type": {}, "details": [], "last_updated": now.strftime("%Y-%m-%d %H:%M"),
                "status": "no_past_picks"}
    
    # Get current prices for all unique tickers
    unique_tickers = list(set(p["ticker"] for p in picks))
    current_prices = _get_current_prices(unique_tickers)
    
    # Calculate hits and misses
    hits = 0
    misses = 0
    details = []
    by_type = defaultdict(lambda: {"hits": 0, "misses": 0})
    
    for pick in picks:
        ticker = pick["ticker"]
        current = current_prices.get(ticker)
        if current is None:
            continue  # Skip if we can't get current price
        
        flagged = pick["flagged_price"]
        if not flagged or flagged == 0:
            continue
        change_pct = round(((current - flagged) / flagged) * 100, 2)
        
        if current > flagged:
            result = "HIT"
            hits += 1
            by_type[pick["scan_type"]]["hits"] += 1
        else:
            result = "MISS"
            misses += 1
            by_type[pick["scan_type"]]["misses"] += 1
        
        details.append({
            "ticker": ticker,
            "scan_type": pick["scan_type"],
            "scan_date": pick["scan_date"],
            "score": pick["score"],
            "flagged_price": flagged,
            "current_price": current,
            "change_pct": change_pct,
            "result": result,
        })
    
    total = hits + misses
    accuracy = round((hits / total) * 100, 1) if total > 0 else 0
    
    # Per scan type accuracy
    by_type_out = {}
    for st, counts in by_type.items():
        st_total = counts["hits"] + counts["misses"]
        by_type_out[st] = {
            "hits": counts["hits"],
            "misses": counts["misses"],
            "accuracy_pct": round((counts["hits"] / st_total) * 100, 1) if st_total > 0 else 0,
        }
    
    # Sort details: hits first, then by change_pct descending
    details.sort(key=lambda x: x["change_pct"], reverse=True)
    
    return {
        "hits": hits,
        "misses": misses,
        "accuracy_pct": accuracy,
        "total_evaluated": total,
        "lookback_days": lookback_days,
        "lookback_trading_days": LOOKBACK_TRADING_DAYS,
        "by_scan_type": by_type_out,
        "details": details,
        "last_updated": now.strftime("%Y-%m-%d %H:%M"),
        "status": "ok",
    }


def format_accuracy_for_gui(acc: Dict) -> str:
    """One-line summary for the main GUI status area."""
    status = acc.get("status", "")
    if status == "no_history":
        return "Accuracy: No scan history yet"
    if status == "no_past_picks":
        return "Accuracy: No past picks to evaluate (need 1+ day)"
    if status != "ok" or acc.get("total_evaluated", 0) == 0:
        return "Accuracy: --"
    
    hits = acc["hits"]
    misses = acc["misses"]
    pct = acc["accuracy_pct"]
    total = acc["total_evaluated"]
    
    td = acc.get('lookback_trading_days', LOOKBACK_TRADING_DAYS)
    return f"Accuracy: {pct}% ({hits} hits / {misses} misses, {total} picks, rolling {td} trading days)"


def format_accuracy_for_report(acc: Dict) -> str:
    """Detailed accuracy block for the history report."""
    if acc.get("status") != "ok" or acc.get("total_evaluated", 0) == 0:
        return ""
    
    lines = [
        "─" * 65,
        "  ACCURACY RATING (past picks vs current price)",
        "─" * 65,
        f"  Lookback: rolling {acc.get('lookback_trading_days', LOOKBACK_TRADING_DAYS)} trading days  |  Updated: {acc.get('last_updated', '')}",
        "",
        f"  OVERALL:  {acc['accuracy_pct']}%  ({acc['hits']} hits / {acc['misses']} misses / {acc['total_evaluated']} total)",
        "",
    ]
    
    # Per scan type
    if acc.get("by_scan_type"):
        lines.append("  By scan type:")
        for st, data in acc["by_scan_type"].items():
            lines.append(f"    {st:<30} {data['accuracy_pct']:>5.1f}%  ({data['hits']}H / {data['misses']}M)")
        lines.append("")
    
    # Top hits and worst misses
    details = acc.get("details", [])
    top_hits = [d for d in details if d["result"] == "HIT"][:5]
    top_misses = [d for d in reversed(details) if d["result"] == "MISS"][:5]
    
    if top_hits:
        lines.append("  Best hits:")
        for d in top_hits:
            lines.append(f"    {d['ticker']:<8} +{d['change_pct']:>5.1f}%  (${d['flagged_price']:.2f} -> ${d['current_price']:.2f})  Score {d['score']}  {d['scan_date']}")
    
    if top_misses:
        lines.append("  Worst misses:")
        for d in top_misses:
            lines.append(f"    {d['ticker']:<8} {d['change_pct']:>6.1f}%  (${d['flagged_price']:.2f} -> ${d['current_price']:.2f})  Score {d['score']}  {d['scan_date']}")
    
    lines.append("")
    return "\n".join(lines)
