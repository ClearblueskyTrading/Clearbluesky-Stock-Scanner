# ============================================================
# ClearBlueSky - Safe Finviz Wrapper
# ============================================================
# Wraps finviz.get_stock() with timeout protection and retry
# logic to prevent scanners from hanging indefinitely.

import threading
import time
from typing import Optional, Dict

import finviz


def get_stock_safe(ticker: str, timeout: float = 30.0, max_attempts: int = 2) -> Optional[Dict]:
    """
    Fetch finviz stock data with timeout protection and retry.

    Args:
        ticker: Stock ticker symbol
        timeout: Max seconds to wait per attempt (default 30s)
        max_attempts: Number of retry attempts (default 2)

    Returns:
        Dict of stock data, or None if all attempts fail/timeout
    """
    for attempt in range(max_attempts):
        result = [None]
        exc = [None]

        def _fetch():
            try:
                result[0] = finviz.get_stock(ticker)
            except Exception as e:
                exc[0] = e

        t = threading.Thread(target=_fetch, daemon=True)
        t.start()
        t.join(timeout=timeout)

        if t.is_alive():
            # Thread is stuck — abandon it
            if attempt < max_attempts - 1:
                time.sleep(1.0)
                continue
            return None

        if exc[0]:
            err_str = str(exc[0]).lower()
            # Retry on transient errors
            if attempt < max_attempts - 1 and ('429' in err_str or 'timeout' in err_str or 'rate' in err_str or 'connection' in err_str):
                time.sleep(1.5 * (attempt + 1))
                continue
            return None

        if result[0] is not None:
            return result[0]

        # Got None result — retry
        if attempt < max_attempts - 1:
            time.sleep(0.5)

    return None
