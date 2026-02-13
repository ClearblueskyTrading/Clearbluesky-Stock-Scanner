# ============================================================
# ClearBlueSky - Safe Finviz Wrapper (Elite + Rate Limiting)
# ============================================================
# Wraps finviz.get_stock() with:
# - Finviz Elite support (elite.finviz.com + api_key)
# - Rate limiter: 20 calls/min (3x safety vs typical 60/min)
# - Timeout protection and retry logic

import threading
import time
from typing import Optional, Dict

import finviz

# --- Rate limiter (3x safety: 20/min if limit is 60/min) ---
_FINVIZ_RATE_LIMIT = 20  # max calls per minute
_FINVIZ_MIN_INTERVAL = 60.0 / _FINVIZ_RATE_LIMIT  # 3.0 seconds between calls
_finviz_last_call: float = 0
_finviz_lock = threading.Lock()


def _rate_limit_wait():
    """Enforce min interval between Finviz calls."""
    global _finviz_last_call
    with _finviz_lock:
        now = time.monotonic()
        elapsed = now - _finviz_last_call
        if elapsed < _FINVIZ_MIN_INTERVAL and _finviz_last_call > 0:
            time.sleep(_FINVIZ_MIN_INTERVAL - elapsed)
        _finviz_last_call = time.monotonic()


def _load_finviz_api_key(config: Optional[dict] = None) -> str:
    """Load finviz_api_key from config (or user_config.json if config is None)."""
    if config is not None:
        key = (config.get("finviz_api_key") or "").strip()
        if key:
            return key
    try:
        import json
        import os
        cfg_path = os.path.join(os.path.dirname(__file__), "user_config.json")
        if os.path.isfile(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return (data.get("finviz_api_key") or "").strip()
    except Exception:
        pass
    return ""


_elite_patch_lock = threading.Lock()


def _elite_get_stock(ticker: str, api_key: str) -> Optional[Dict]:
    """
    Fetch stock from elite.finviz.com with API key (Cookie + X-API-Key).
    Uses same HTML structure as finviz.com; returns None on auth/data failure.
    """
    try:
        import requests
        from lxml import html
        from finviz.config import USER_AGENT
    except ImportError:
        return None

    url = "https://elite.finviz.com/quote.ashx"
    headers = {
        "User-Agent": USER_AGENT,
        "Cookie": f"elite_key={api_key}",
        "X-API-Key": api_key,
    }

    try:
        resp = requests.get(url, params={"t": ticker}, headers=headers, timeout=15, verify=False)
        resp.raise_for_status()
        if resp.text and "Too many requests" in resp.text:
            return None
        txt = resp.text or ""
        if ("Log in" in txt or "Login" in txt) and "quote" not in txt.lower()[:500]:
            return None
        page_parsed = html.fromstring(resp.text)
        import finviz.main_func as mf
        with _elite_patch_lock:
            old_get_page = mf.get_page
            old_sp = dict(mf.STOCK_PAGE)
            mf.STOCK_PAGE[ticker] = page_parsed

            def _noop_get_page(t, force_refresh=False):
                if t == ticker and not force_refresh:
                    return
                old_get_page(t, force_refresh)

            mf.get_page = _noop_get_page
            try:
                data = mf.get_stock(ticker)
            finally:
                mf.get_page = old_get_page
                mf.STOCK_PAGE.clear()
                mf.STOCK_PAGE.update(old_sp)
        return data if data and data.get("Price") else None
    except Exception:
        return None


def get_stock_safe(
    ticker: str,
    timeout: float = 30.0,
    max_attempts: int = 2,
    config: Optional[dict] = None,
) -> Optional[Dict]:
    """
    Fetch finviz stock data with timeout protection, retry, Elite support, and rate limiting.

    Args:
        ticker: Stock ticker symbol
        timeout: Max seconds to wait per attempt (default 30s)
        max_attempts: Number of retry attempts (default 2)
        config: Optional config dict with finviz_api_key. If None, loads from user_config.json.

    Returns:
        Dict of stock data, or None if all attempts fail/timeout
    """
    api_key = _load_finviz_api_key(config)
    use_elite = bool(api_key)

    for attempt in range(max_attempts):
        _rate_limit_wait()
        result = [None]
        exc = [None]

        def _fetch():
            try:
                if use_elite:
                    result[0] = _elite_get_stock(ticker, api_key)
                if result[0] is None:
                    result[0] = finviz.get_stock(ticker)
            except Exception as e:
                exc[0] = e

        t = threading.Thread(target=_fetch, daemon=True)
        t.start()
        t.join(timeout=timeout)

        if t.is_alive():
            if attempt < max_attempts - 1:
                time.sleep(3.0)
                continue
            return None

        if exc[0]:
            err_str = str(exc[0]).lower()
            if attempt < max_attempts - 1 and (
                "429" in err_str
                or "timeout" in err_str
                or "rate" in err_str
                or "connection" in err_str
            ):
                wait = 3.0 * (attempt + 1)
                time.sleep(wait)
                continue
            return None

        if result[0] is not None:
            return result[0]

        if attempt < max_attempts - 1:
            time.sleep(2.0)

    return None
