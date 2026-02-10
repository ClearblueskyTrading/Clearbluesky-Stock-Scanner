# ============================================================
# ClearBlueSky - Ticker Enrichment
# ============================================================
# Adds earnings dates, news sentiment flags, price-at-report-time,
# insider data, and leveraged ticker suggestions to scan results.

import json
import os
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

try:
    import finviz
    FINVIZ_AVAILABLE = True
except ImportError:
    FINVIZ_AVAILABLE = False

# ── News sentiment keywords ──────────────────────────────────

RED_FLAG_KEYWORDS = [
    'fda rejection', 'lawsuit', 'sued', 'sec investigation', 'sec probe',
    'recall', 'bankruptcy', 'bankrupt', 'delisted', 'fraud', 'indictment',
    'ceo resign', 'cfo resign', 'accounting', 'restatement', 'default',
    'downgrade', 'cut to sell', 'price target cut', 'guidance lower',
    'missed estimates', 'miss earnings', 'revenue miss', 'profit warning',
    'layoff', 'data breach', 'hack', 'subpoena', 'class action',
    'dividend cut', 'dividend suspend', 'going concern',
]

GREEN_FLAG_KEYWORDS = [
    'upgrade', 'price target raise', 'raised guidance', 'beat estimates',
    'beat earnings', 'revenue beat', 'profit beat', 'fda approval',
    'fda cleared', 'new contract', 'buyback', 'share repurchase',
    'dividend increase', 'dividend raise', 'raised dividend',
    'analyst upgrade', 'buy rating', 'outperform', 'strong buy',
    'record revenue', 'record profit', 'all-time high', 'new high',
    'partnership', 'acquisition', 'merger approved',
]

# ── Leveraged ticker mapping ─────────────────────────────────

_LEVERAGED_MAP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leveraged_tickers.json")


def _load_leveraged_map() -> Dict[str, str]:
    """Load sector/underlying -> leveraged ETF mapping."""
    if not os.path.exists(_LEVERAGED_MAP_PATH):
        return {}
    try:
        with open(_LEVERAGED_MAP_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {str(k).strip().upper(): str(v).strip().upper() for k, v in data.items() if not str(k).startswith("_") and v}
    except Exception:
        return {}


# ── Earnings date ─────────────────────────────────────────────

def _get_earnings_date(ticker: str) -> Optional[Dict]:
    """Get next earnings date for a ticker. Returns dict with date and days_away."""
    if not YF_AVAILABLE:
        return None
    try:
        t = yf.Ticker(ticker)
        cal = t.calendar
        if cal is None:
            return None
        # yfinance calendar can be a dict or DataFrame
        earnings_date = None
        if isinstance(cal, dict):
            ed = cal.get("Earnings Date")
            if ed:
                if isinstance(ed, list) and len(ed) > 0:
                    earnings_date = ed[0]
                elif hasattr(ed, 'date'):
                    earnings_date = ed
        elif hasattr(cal, 'columns'):
            # DataFrame format
            if "Earnings Date" in cal.columns:
                vals = cal["Earnings Date"].dropna()
                if len(vals) > 0:
                    earnings_date = vals.iloc[0]
            elif 0 in cal.columns:
                try:
                    earnings_date = cal.loc["Earnings Date", 0]
                except Exception:
                    pass

        if earnings_date is None:
            return None

        # Convert to date
        if hasattr(earnings_date, 'date'):
            ed = earnings_date.date()
        elif isinstance(earnings_date, str):
            ed = datetime.strptime(earnings_date[:10], "%Y-%m-%d").date()
        else:
            ed = earnings_date

        today = date.today()
        days_away = (ed - today).days

        warning = None
        if days_away <= 0:
            warning = "EARNINGS TODAY"
        elif days_away == 1:
            warning = "EARNINGS TOMORROW - DO NOT HOLD OVERNIGHT"
        elif days_away <= 3:
            warning = f"EARNINGS IN {days_away} DAYS - HIGH RISK"
        elif days_away <= 7:
            warning = f"EARNINGS IN {days_away} DAYS - CAUTION"

        return {
            "earnings_date": str(ed),
            "days_away": days_away,
            "warning": warning,
        }
    except Exception:
        return None


# ── News sentiment ────────────────────────────────────────────

def _score_news_sentiment(headlines: List[str]) -> Dict:
    """Score news headlines for red/green flags. Returns sentiment dict."""
    red_flags = []
    green_flags = []

    for headline in headlines:
        hl = headline.lower()
        for kw in RED_FLAG_KEYWORDS:
            if kw in hl:
                red_flags.append(headline)
                break
        for kw in GREEN_FLAG_KEYWORDS:
            if kw in hl:
                green_flags.append(headline)
                break

    if len(red_flags) >= 2:
        sentiment = "DANGER"
    elif len(red_flags) >= 1:
        sentiment = "NEGATIVE"
    elif len(green_flags) >= 2:
        sentiment = "POSITIVE"
    elif len(green_flags) >= 1:
        sentiment = "POSITIVE"
    else:
        sentiment = "NEUTRAL"

    return {
        "sentiment": sentiment,
        "red_flags": red_flags[:3],
        "green_flags": green_flags[:3],
    }


# ── Price at report time ─────────────────────────────────────

def _get_current_price(ticker: str) -> Optional[Dict]:
    """Get current price for report stamping. Failover: yfinance > finviz > alpaca."""
    try:
        from data_failover import get_price_volume
        pv = get_price_volume(ticker)
        if pv and pv.get("price") and pv["price"] > 0:
            return {
                "price_at_report": pv["price"],
                "report_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S ET"),
            }
    except Exception:
        pass
    return None


# ── Leveraged suggestion ─────────────────────────────────────

def _get_leveraged_suggestion(ticker: str, sector: str, leveraged_map: Dict) -> Optional[Dict]:
    """Suggest a leveraged ETF play for a given ticker/sector."""
    # Direct ticker match
    if ticker in leveraged_map:
        return {"leveraged_ticker": leveraged_map[ticker], "match_type": "direct"}

    # Sector match
    sector_lower = (sector or "").lower()
    sector_map = {
        "technology": "TECL",
        "semiconductor": "SOXL",
        "semiconductors": "SOXL",
        "consumer cyclical": "WANT",
        "consumer discretionary": "WANT",
        "financial": "FAS",
        "financials": "FAS",
        "healthcare": "LABU",
        "health care": "LABU",
        "energy": "ERX",
        "industrial": "DUSL",
        "industrials": "DUSL",
    }
    for key, etf in sector_map.items():
        if key in sector_lower:
            return {"leveraged_ticker": etf, "match_type": "sector"}

    # Broad market fallback
    return {"leveraged_ticker": "SPXL", "match_type": "broad_market"}


# ── Main enrichment function ─────────────────────────────────

def enrich_scan_results(results: List[Dict], include_earnings: bool = True,
                        include_news_flags: bool = True, include_price_stamp: bool = True,
                        include_leveraged: bool = False, progress_callback=None) -> List[Dict]:
    """
    Enrich scan results with earnings dates, news flags, price stamps, and leveraged suggestions.

    Args:
        results: List of scan result dicts (must have 'ticker' key)
        include_earnings: Add earnings date warnings
        include_news_flags: Score news headlines for red/green flags
        include_price_stamp: Add current price at report time
        include_leveraged: Add leveraged ETF suggestions
        progress_callback: Optional progress function

    Returns:
        Same results list with enrichment fields added to each dict
    """
    if not results:
        return results

    leveraged_map = _load_leveraged_map() if include_leveraged else {}

    def _enrich_one(r):
        ticker = (r.get("ticker") or r.get("Ticker") or "").strip().upper()
        if not ticker:
            return r

        enrichment = {}

        # Earnings date
        if include_earnings:
            ed = _get_earnings_date(ticker)
            if ed:
                enrichment["earnings"] = ed

        # News sentiment flags
        if include_news_flags:
            headlines = []
            news = r.get("news") or r.get("News") or []
            for item in news:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    headlines.append(str(item[1]))
                elif isinstance(item, dict):
                    headlines.append(str(item.get("title") or item.get("headline", "")))
                elif isinstance(item, str):
                    headlines.append(item)
            if headlines:
                enrichment["news_sentiment"] = _score_news_sentiment(headlines)

        # Price at report time
        if include_price_stamp:
            price_data = _get_current_price(ticker)
            if price_data:
                enrichment.update(price_data)

        # Leveraged suggestion
        if include_leveraged and leveraged_map:
            sector = r.get("sector") or r.get("Sector") or ""
            lev = _get_leveraged_suggestion(ticker, sector, leveraged_map)
            if lev:
                enrichment["leveraged_play"] = lev

        r.update(enrichment)
        return r

    # Sequential enrichment — one at a time to respect Finviz + yfinance rate limits
    total = len(results)
    for i, r in enumerate(results):
        try:
            results[i] = _enrich_one(r)
        except Exception:
            pass
        if progress_callback and (i + 1) % 5 == 0:
            progress_callback(f"Enriching tickers ({i + 1}/{total})...")
        time.sleep(0.5)  # polite delay between enrichment calls

    return results
