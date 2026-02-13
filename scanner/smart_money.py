"""
ClearBlueSky – Smart Money Signals.

Gathers institutional / social confirmation signals per ticker from FREE sources:
  1. WSB / Reddit sentiment  – apewisdom.io (free, no key, real-time mentions & rank)
  2. Institutional holders   – yfinance (13F data: top holders, % change, date reported)
  3. Insider activity        – Finviz data already captured in report; this module adds
                               SEC EDGAR Form 4 filing count as a supplement.

Usage:
  ALL scanners  → get_wsb_sentiment(tickers)    (fast, one API call for top 100)
  TREND scanner → get_smart_money(tickers)      (full package: WSB + institutional + insider filings)
"""

import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ---------------------------------------------------------------------------
# WSB / Reddit sentiment (apewisdom.io — free, no key)
# ---------------------------------------------------------------------------

APEWISDOM_URL = "https://apewisdom.io/api/v1.0/filter/all-stocks/page/{page}"
_wsb_cache = {}  # ticker -> dict, refreshed per call to get_wsb_sentiment
_wsb_cache_time = 0
WSB_CACHE_TTL = 300  # 5 minutes


def _refresh_wsb_cache():
    """Fetch top ~200 mentioned tickers from apewisdom (pages 1-2)."""
    global _wsb_cache, _wsb_cache_time
    if not REQUESTS_AVAILABLE:
        return
    now = time.time()
    if _wsb_cache and (now - _wsb_cache_time) < WSB_CACHE_TTL:
        return  # cache still fresh
    new_cache = {}
    for page in (1, 2):
        try:
            r = requests.get(APEWISDOM_URL.format(page=page), timeout=10)
            if r.status_code != 200:
                continue
            results = r.json().get("results", [])
            for item in results:
                ticker = (item.get("ticker") or "").upper().strip()
                if ticker:
                    new_cache[ticker] = {
                        "wsb_rank": item.get("rank"),
                        "wsb_mentions": item.get("mentions", 0),
                        "wsb_upvotes": item.get("upvotes", 0),
                        "wsb_rank_24h_ago": item.get("rank_24h_ago"),
                        "wsb_mentions_24h_ago": item.get("mentions_24h_ago", 0),
                    }
        except Exception:
            continue
    if new_cache:
        _wsb_cache = new_cache
        _wsb_cache_time = now


def get_wsb_sentiment(tickers: List[str]) -> Dict[str, Dict]:
    """
    Get WSB/Reddit sentiment for a list of tickers.
    Returns {ticker: {wsb_rank, wsb_mentions, wsb_upvotes, ...}} for those found.
    Tickers not in the top ~200 return an empty dict entry.
    """
    _refresh_wsb_cache()
    result = {}
    for t in tickers:
        t_upper = t.upper().strip()
        result[t_upper] = _wsb_cache.get(t_upper, {})
    return result


# ---------------------------------------------------------------------------
# Institutional holders (yfinance — 13F data)
# ---------------------------------------------------------------------------

# Well-known fund names to highlight
NOTABLE_FUNDS = {
    "berkshire hathaway", "bridgewater", "citadel", "renaissance",
    "two sigma", "d.e. shaw", "millennium", "point72", "tiger global",
    "soros", "druckenmiller", "appaloosa", "third point", "pershing square",
    "elliott", "baupost", "greenlight", "lone pine", "coatue",
    "viking global", "maverick", "jana partners",
}


def _get_institutional_holders(ticker: str) -> Dict[str, Any]:
    """Get top institutional holders from yfinance (13F filings)."""
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        ih = t.institutional_holders
        if ih is None or ih.empty:
            return {}
        holders = []
        notable = []
        for _, row in ih.head(10).iterrows():
            name = str(row.get("Holder", "")).strip()
            pct_change = row.get("pctChange")
            pct_held = row.get("pctHeld")
            date_rep = row.get("Date Reported")
            holder_info = {
                "name": name,
                "pct_held": round(float(pct_held) * 100, 2) if pct_held else None,
                "pct_change": round(float(pct_change) * 100, 2) if pct_change else None,
                "date_reported": str(date_rep.date()) if hasattr(date_rep, "date") else str(date_rep) if date_rep else None,
            }
            holders.append(holder_info)
            # Check if this is a notable hedge fund
            name_lower = name.lower()
            for fund in NOTABLE_FUNDS:
                if fund in name_lower:
                    notable.append(holder_info)
                    break

        # Identify recent large increases (>10% position change)
        increasing = [h for h in holders if h.get("pct_change") and h["pct_change"] > 10]

        return {
            "top_holders": holders[:5],  # Top 5 for JSON
            "notable_funds": notable,
            "increasing_positions": increasing,
            "holder_count": len(holders),
        }
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# SEC EDGAR insider filing count (Form 4 — supplements Finviz insider data)
# ---------------------------------------------------------------------------

EDGAR_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
EDGAR_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
EDGAR_HEADERS = {"User-Agent": "ClearBlueSky/1.0 contact@clearbluesky.com"}

_cik_cache = {}  # ticker -> CIK string


def _load_cik_cache():
    """Load ticker -> CIK mapping from SEC."""
    global _cik_cache
    if _cik_cache:
        return
    try:
        r = requests.get(EDGAR_TICKERS_URL, headers=EDGAR_HEADERS, timeout=15)
        if r.status_code == 200:
            data = r.json()
            for entry in data.values():
                ticker = (entry.get("ticker") or "").upper().strip()
                cik = str(entry.get("cik_str", "")).strip()
                if ticker and cik:
                    _cik_cache[ticker] = cik.zfill(10)  # Pad to 10 digits
    except Exception:
        pass


def _get_insider_filing_count(ticker: str, days: int = 90) -> Dict[str, Any]:
    """Count recent SEC Form 4 (insider) filings from EDGAR."""
    if not REQUESTS_AVAILABLE:
        return {}
    _load_cik_cache()
    cik = _cik_cache.get(ticker.upper().strip())
    if not cik:
        return {}
    try:
        r = requests.get(EDGAR_SUBMISSIONS_URL.format(cik=cik), headers=EDGAR_HEADERS, timeout=15)
        if r.status_code != 200:
            return {}
        data = r.json()
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        form4_recent = [(f, d) for f, d in zip(forms, dates) if f == "4" and d >= cutoff]
        return {
            "form4_count_90d": len(form4_recent),
            "form4_latest_date": form4_recent[0][1] if form4_recent else None,
        }
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_smart_money_for_ticker(ticker: str) -> Dict[str, Any]:
    """
    Full smart money package for one ticker (TREND scanner).
    Returns dict with wsb, institutional, and insider filing data.
    """
    result = {"ticker": ticker.upper()}

    # WSB (from cache — should already be populated)
    _refresh_wsb_cache()
    wsb = _wsb_cache.get(ticker.upper(), {})
    result.update(wsb)

    # Institutional holders (yfinance 13F)
    inst = _get_institutional_holders(ticker)
    if inst:
        result["institutional"] = inst

    # SEC EDGAR Form 4 count
    edgar = _get_insider_filing_count(ticker)
    if edgar:
        result.update(edgar)

    return result


def get_smart_money_batch(tickers: List[str], full: bool = False,
                          progress_callback=None) -> Dict[str, Dict]:
    """
    Batch smart money lookup.

    Args:
        tickers: List of ticker symbols.
        full: If True, get full package (institutional + EDGAR + WSB) — for trend scanner.
              If False, get WSB only — for all other scanners.
        progress_callback: Optional status callback.

    Returns:
        {ticker: {smart_money_data}} dict.
    """
    if progress_callback:
        mode = "full smart money" if full else "WSB sentiment"
        progress_callback(f"Gathering {mode} for {len(tickers)} tickers...")

    # Always refresh WSB cache first
    _refresh_wsb_cache()

    if not full:
        # WSB only — instant from cache
        return get_wsb_sentiment(tickers)

    # Full smart money — sequential to respect SEC EDGAR + yfinance rate limits
    results = {}
    for i, t in enumerate(tickers):
        try:
            results[t.upper()] = get_smart_money_for_ticker(t)
        except Exception:
            results[t.upper()] = {}
        # Polite delay — SEC EDGAR recommends max 10 req/sec, yfinance similar
        time.sleep(0.5)

    if progress_callback:
        wsb_hits = sum(1 for v in results.values() if v.get("wsb_rank"))
        inst_hits = sum(1 for v in results.values() if v.get("institutional"))
        progress_callback(f"Smart money: {wsb_hits} WSB mentions, {inst_hits} with institutional data")

    return results


def format_smart_money_for_prompt(ticker: str, data: Dict) -> str:
    """Format one ticker's smart money data as a text line for the AI prompt."""
    if not data:
        return ""

    parts = []

    # WSB
    if data.get("wsb_rank"):
        mentions = data.get("wsb_mentions", 0)
        rank = data.get("wsb_rank")
        upvotes = data.get("wsb_upvotes", 0)
        trend = ""
        prev = data.get("wsb_mentions_24h_ago", 0)
        if prev and mentions:
            if mentions > prev * 1.5:
                trend = " TRENDING UP"
            elif mentions < prev * 0.5:
                trend = " cooling off"
        parts.append(f"WSB rank #{rank} ({mentions} mentions, {upvotes} upvotes{trend})")

    # Institutional
    inst = data.get("institutional", {})
    if inst:
        notable = inst.get("notable_funds", [])
        increasing = inst.get("increasing_positions", [])
        if notable:
            names = ", ".join(n["name"] for n in notable[:3])
            parts.append(f"Notable holders: {names}")
        if increasing:
            names = ", ".join(f"{h['name']} (+{h['pct_change']:.0f}%)" for h in increasing[:3])
            parts.append(f"Increasing positions: {names}")

    # EDGAR Form 4
    f4 = data.get("form4_count_90d")
    if f4 is not None:
        latest = data.get("form4_latest_date", "")
        parts.append(f"Insider filings (90d): {f4}" + (f", latest {latest}" if latest else ""))

    if not parts:
        return ""
    return f"  Smart Money [{ticker}]: " + " | ".join(parts)
