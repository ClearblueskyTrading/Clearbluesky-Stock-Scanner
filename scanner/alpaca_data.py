# ============================================================
# ClearBlueSky - Alpaca market data (read-only, rate-limited)
# ============================================================
# Used by scanners and report generator for execution-grade price/volume
# when Alpaca keys are set. Respects 3× safety: 60 req/min, 3 req/sec.
# Data API base: https://data.alpaca.markets (same for paper/live).
# Supports: snapshots (current), historical bars (OHLCV, 6+ years).

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Rate limit: 60/min, 3/sec (3× safety vs Alpaca 200/min, 10/sec)
MAX_PER_MINUTE = 60
MAX_PER_SECOND = 3
# Rolling window tracking
_request_times: List[float] = []


def _rate_limit_ok() -> bool:
    """Return True if we can make a request without exceeding limits."""
    now = time.time()
    # Prune older than 60s
    global _request_times
    _request_times = [t for t in _request_times if now - t < 60.0]
    in_last_min = len(_request_times)
    in_last_sec = sum(1 for t in _request_times if now - t < 1.0)
    return in_last_min < MAX_PER_MINUTE and in_last_sec < MAX_PER_SECOND


def _record_request():
    _request_times.append(time.time())


def _get_config():
    try:
        from scan_settings import load_config
        return load_config()
    except Exception:
        return {}


def _alpaca_headers(config: dict) -> Optional[dict]:
    key = (config.get("alpaca_api_key") or "").strip()
    secret = (config.get("alpaca_secret_key") or "").strip()
    if not key or not secret:
        return None
    return {
        "APCA-API-KEY-ID": key,
        "APCA-API-SECRET-KEY": secret,
    }


def get_price_volume(ticker: str, config: Optional[dict] = None) -> Optional[Dict]:
    """
    Fetch latest price and volume for one ticker from Alpaca (when keys set).
    Respects rate limit (60/min, 3/sec). Returns None if no keys, limit hit, or error.

    Returns:
        {"price": float, "volume": int, "change_pct": float|None, "source": "alpaca"}
        or None.
    """
    if not REQUESTS_AVAILABLE:
        return None
    config = config or _get_config()
    headers = _alpaca_headers(config)
    if not headers:
        return None
    if not _rate_limit_ok():
        return None

    ticker = (ticker or "").strip().upper()
    if not ticker:
        return None

    url = "https://data.alpaca.markets/v2/stocks/snapshots"
    params = {"symbols": ticker}
    try:
        _record_request()
        r = requests.get(url, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None

    snap = data.get("snapshots", {}).get(ticker) if isinstance(data, dict) else None
    if not snap:
        return None

    # Prefer latest trade price; fallback to daily bar close
    price = None
    daily = (snap.get("dailyBar") or snap.get("daily_bar")) or {}
    prev_daily = (snap.get("previousDailyBar") or snap.get("previous_daily_bar")) or {}
    latest_trade = (snap.get("latestTrade") or snap.get("latest_trade")) or {}

    if latest_trade and latest_trade.get("p") is not None:
        try:
            price = float(latest_trade["p"])
        except (TypeError, ValueError):
            pass
    if price is None and daily.get("c") is not None:
        try:
            price = float(daily["c"])
        except (TypeError, ValueError):
            pass
    if price is None or price <= 0:
        return None

    volume = 0
    if daily.get("v") is not None:
        try:
            volume = int(float(daily["v"]))
        except (TypeError, ValueError):
            pass

    change_pct = None
    try:
        prev_c = prev_daily.get("c")
        if prev_c is not None and float(prev_c) > 0:
            change_pct = round((price - float(prev_c)) / float(prev_c) * 100, 2)
    except (TypeError, ValueError):
        pass

    return {
        "price": round(price, 2),
        "volume": volume,
        "change_pct": change_pct,
        "source": "alpaca",
    }


def get_price_volume_batch(tickers: List[str], config: Optional[dict] = None) -> Dict[str, Dict]:
    """
    Fetch price/volume for multiple tickers in one Alpaca call (saves rate limit).
    Returns dict keyed by ticker with same shape as get_price_volume(), only for tickers that succeeded.
    """
    if not REQUESTS_AVAILABLE or not tickers:
        return {}
    config = config or _get_config()
    headers = _alpaca_headers(config)
    if not headers:
        return {}
    if not _rate_limit_ok():
        return {}

    symbols = [str(t).strip().upper() for t in tickers if str(t).strip()]
    symbols = list(dict.fromkeys(symbols))[:50]  # cap batch size
    if not symbols:
        return {}

    url = "https://data.alpaca.markets/v2/stocks/snapshots"
    params = {"symbols": ",".join(symbols)}
    try:
        _record_request()
        r = requests.get(url, params=params, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return {}

    out = {}
    snapshots = data.get("snapshots", {}) if isinstance(data, dict) else {}
    for sym in symbols:
        snap = snapshots.get(sym)
        if not snap:
            continue
        daily = (snap.get("dailyBar") or snap.get("daily_bar")) or {}
        prev_daily = (snap.get("previousDailyBar") or snap.get("previous_daily_bar")) or {}
        latest_trade = (snap.get("latestTrade") or snap.get("latest_trade")) or {}
        price = None
        if latest_trade and latest_trade.get("p") is not None:
            try:
                price = float(latest_trade["p"])
            except (TypeError, ValueError):
                pass
        if price is None and daily.get("c") is not None:
            try:
                price = float(daily["c"])
            except (TypeError, ValueError):
                pass
        if price is None or price <= 0:
            continue
        volume = 0
        if daily.get("v") is not None:
            try:
                volume = int(float(daily["v"]))
            except (TypeError, ValueError):
                pass
        change_pct = None
        try:
            prev_c = prev_daily.get("c")
            if prev_c is not None and float(prev_c) > 0:
                change_pct = round((price - float(prev_c)) / float(prev_c) * 100, 2)
        except (TypeError, ValueError):
            pass
        out[sym] = {"price": round(price, 2), "volume": volume, "change_pct": change_pct, "source": "alpaca"}
    return out


def get_bars(
    symbol: str,
    days: int = 30,
    timeframe: str = "1Day",
    limit: int = 1000,
    config: Optional[dict] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch historical OHLCV bars for one symbol from Alpaca.
    When keys set, returns list of dicts: {"date": "YYYY-MM-DD", "open", "high", "low", "close", "volume"}.
    Returns None if no keys, rate limit hit, or error.

    timeframe: "1Min", "5Min", "15Min", "1Hour", "1Day", "1Week", "1Month"
    start_date, end_date: optional "YYYY-MM-DD" for explicit range (overrides days).
    """
    if not REQUESTS_AVAILABLE:
        return None
    config = config or _get_config()
    headers = _alpaca_headers(config)
    if not headers:
        return None
    if not _rate_limit_ok():
        return None

    symbol = (symbol or "").strip().upper()
    if not symbol:
        return None

    if start_date and end_date:
        start_str = f"{start_date[:10]}T00:00:00Z"
        end_str = f"{end_date[:10]}T23:59:59Z"
    else:
        end = datetime.now()
        start = end - timedelta(days=min(days, 365 * 7))  # cap 7 years
        start_str = start.strftime("%Y-%m-%dT00:00:00Z")
        end_str = end.strftime("%Y-%m-%dT23:59:59Z")

    url = "https://data.alpaca.markets/v2/stocks/bars"
    params = {
        "symbols": symbol,
        "timeframe": timeframe,
        "start": start_str,
        "end": end_str,
        "limit": min(limit, 10000),
    }
    try:
        _record_request()
        r = requests.get(url, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None

    bars_raw = (data.get("bars") or {}).get(symbol)
    if not bars_raw:
        return None

    out = []
    for b in bars_raw:
        t = b.get("t") or b.get("timestamp")
        if not t:
            continue
        try:
            if isinstance(t, str) and "T" in t:
                dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
            else:
                dt = datetime.fromtimestamp(t) if isinstance(t, (int, float)) else None
            date_str = dt.strftime("%Y-%m-%d") if dt else None
        except Exception:
            date_str = str(t)[:10]
        o = float(b.get("o", 0) or 0)
        h = float(b.get("h", 0) or 0)
        l_ = float(b.get("l", 0) or 0)
        c = float(b.get("c", 0) or 0)
        v = int(float(b.get("v", 0) or 0))
        if date_str and c > 0:
            out.append({
                "date": date_str,
                "open": round(o, 2),
                "high": round(h, 2),
                "low": round(l_, 2),
                "close": round(c, 2),
                "volume": v,
            })
    return out if out else None


def get_bars_batch(
    symbols: List[str],
    days: int = 30,
    timeframe: str = "1Day",
    limit_per_symbol: int = 500,
    config: Optional[dict] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetch historical bars for multiple symbols. One Alpaca request per symbol (batched would need pagination).
    Returns dict keyed by symbol with list of bar dicts. Skips symbols that fail.
    """
    if not REQUESTS_AVAILABLE or not symbols:
        return {}
    config = config or _get_config()
    if not _alpaca_headers(config):
        return {}

    symbols = [str(s).strip().upper() for s in symbols if str(s).strip()]
    symbols = list(dict.fromkeys(symbols))[:20]  # cap to avoid rate limit
    out = {}
    for sym in symbols:
        if not _rate_limit_ok():
            break
        bars = get_bars(sym, days=days, timeframe=timeframe, limit=limit_per_symbol, config=config)
        if bars:
            out[sym] = bars
        time.sleep(0.1)  # small stagger between symbols
    return out


def bars_to_dataframe(bars: List[Dict[str, Any]]):
    """Convert bars list to pandas DataFrame with columns Open, High, Low, Close, Volume (yfinance-compatible)."""
    if not bars:
        return None
    try:
        import pandas as pd
        df = pd.DataFrame(bars)
        if df.empty:
            return None
        df = df.rename(columns={"date": "Date", "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")
        df = df.sort_index()
        return df[["Open", "High", "Low", "Close", "Volume"]]
    except Exception:
        return None


def has_alpaca_keys(config: Optional[dict] = None) -> bool:
    """Return True if config has non-empty Alpaca API key and secret."""
    config = config or _get_config()
    return _alpaca_headers(config) is not None
