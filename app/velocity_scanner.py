#!/usr/bin/env python3
"""
ClearBlueSky — velocity_scanner stub.
Premarket scanner removed; SCAN_UNIVERSE kept for emotional_dip_scanner.
"""
import os
import sys
from typing import List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

SCAN_UNIVERSE = [
    "TQQQ", "SOXL", "SPXL", "NVDL",
    "NVDA", "TSLA", "AMD", "META", "NFLX", "AMZN", "GOOGL", "COIN", "MSTR",
    "AAPL", "MSFT", "JPM", "V",
]

INDEX_UNIVERSE_CAP = 200


def get_universe_for_index(index: Optional[str]) -> List[str]:
    """Return ticker list. For sp500/etfs fetch from breadth; otherwise SCAN_UNIVERSE."""
    if index and index in ("sp500", "etfs", "sp500_etfs"):
        try:
            from breadth import fetch_full_index_for_breadth
            rows = fetch_full_index_for_breadth(index, progress_callback=None)
            tickers = [str(r.get("Ticker") or "").strip().upper() for r in (rows or []) if r.get("Ticker")]
            tickers = [t for t in tickers if t]
            return tickers[:INDEX_UNIVERSE_CAP] if tickers else SCAN_UNIVERSE
        except Exception:
            return SCAN_UNIVERSE
    return SCAN_UNIVERSE
