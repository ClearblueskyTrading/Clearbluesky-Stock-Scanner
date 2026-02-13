# ============================================================
# Sector Rotation - Rank sectors by momentum, map to leveraged ETFs
# ============================================================
# Used by PTM (rotation mode) and scanner reports.

from typing import List, Optional, Tuple

SECTOR_ETFS = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
SECTOR_NAMES = {
    "XLK": "Technology", "XLF": "Financial", "XLE": "Energy", "XLV": "Healthcare",
    "XLI": "Industrials", "XLY": "Consumer Cyclical", "XLP": "Consumer Defensive",
    "XLU": "Utilities", "XLB": "Materials", "XLRE": "Real Estate", "XLC": "Communication",
}
SECTOR_TO_LEVERAGED = {
    "XLK": "TQQQ", "XLF": "FAS", "XLE": "ERX", "XLV": "CURE",
    "XLI": "DUSL", "XLY": "RETL", "XLP": None, "XLU": None, "XLB": None,
    "XLRE": "DRN", "XLC": None,
}
# Inverse/bear leveraged (when sector momentum is negative)
SECTOR_TO_BEAR = {
    "XLK": "SQQQ", "XLF": "FAZ", "XLE": "ERY", "XLV": "LABD",
    "XLI": None, "XLY": None, "XLP": None, "XLU": None, "XLB": None,
    "XLRE": None, "XLC": None,
}
# Fallback when sector has no bear ETF - use market inverse
BEAR_FALLBACK = "SPXU"


def get_sector_rankings(lookback_days: int = 5) -> List[Tuple[str, str, float]]:
    """
    Rank sectors by N-day return. Returns [(sector_etf, sector_name, return_pct), ...] best first.
    """
    try:
        import yfinance as yf
        import pandas as pd
    except ImportError:
        return []

    results = []
    for etf in SECTOR_ETFS:
        try:
            t = yf.Ticker(etf)
            hist = t.history(period="1mo")
            if hist is None or len(hist) < lookback_days + 2:
                continue
            close = hist["Close"]
            start = float(close.iloc[-lookback_days - 1])
            end = float(close.iloc[-1])
            if start <= 0:
                continue
            ret = (end - start) / start * 100
            name = SECTOR_NAMES.get(etf, etf)
            results.append((etf, name, ret))
        except Exception:
            continue
    results.sort(key=lambda x: -x[2])
    return results


def get_top_rotation_ticker(lookback_days: int = 5, use_leveraged: bool = True,
                           use_bear_when_negative: bool = False) -> Optional[Tuple[str, str, float]]:
    """
    Get top sector and ticker to deploy. Returns (ticker, sector_name, return_pct) or None.
    If use_bear_when_negative and top sector return < 0, returns bear/inverse ETF instead.
    """
    rankings = get_sector_rankings(lookback_days)
    if not rankings:
        return None
    top_etf, name, ret = rankings[0]
    if use_bear_when_negative and ret < 0:
        ticker = SECTOR_TO_BEAR.get(top_etf) or BEAR_FALLBACK
    else:
        ticker = SECTOR_TO_LEVERAGED.get(top_etf) if use_leveraged else top_etf
        if ticker is None:
            ticker = top_etf
    return (ticker, name, ret)


def get_top_n_rotation_tickers(lookback_days: int = 5, n: int = 2,
                              use_leveraged: bool = True, use_bear_when_negative: bool = False
                              ) -> List[Tuple[str, str, float, float]]:
    """
    Get top N sectors and tickers. Returns [(ticker, sector_name, return_pct, weight_pct), ...].
    Weights: first gets 60%, second 40% (for n=2).
    """
    rankings = get_sector_rankings(lookback_days)
    if not rankings:
        return []
    weights = [0.6, 0.4][:n] if n == 2 else [1.0 / n] * n
    out = []
    for i, (etf, name, ret) in enumerate(rankings[:n]):
        if use_bear_when_negative and ret < 0:
            ticker = SECTOR_TO_BEAR.get(etf) or BEAR_FALLBACK
        else:
            ticker = SECTOR_TO_LEVERAGED.get(etf) if use_leveraged else etf
            if ticker is None:
                ticker = etf
        out.append((ticker, name, ret, weights[i] * 100 if i < len(weights) else 100 / n))
    return out


def get_rotation_signal_for_report(lookback_days: int = 5, config: Optional[dict] = None) -> dict:
    """Return dict for report frontmatter/display. Uses ptm_rotation_positions, ptm_rotation_bear from config."""
    try:
        from scan_settings import load_config
        cfg = config or load_config() or {}
    except Exception:
        cfg = config or {}
    n_pos = int(cfg.get("ptm_rotation_positions", 2)) or 2
    use_bear = cfg.get("ptm_rotation_bear", True)
    rankings = get_sector_rankings(lookback_days)

    if n_pos == 2:
        tops = get_top_n_rotation_tickers(lookback_days, n=2, use_leveraged=True, use_bear_when_negative=use_bear)
        top = tops[0] if tops else None
        top_2 = [(t[0], t[1], round(t[2], 2), t[3]) for t in tops] if tops else []
        return {
            "top_sector": top[1] if top else None,
            "top_ticker": top[0] if top else None,
            "top_return_5d": round(top[2], 2) if top else None,
            "top_2_tickers": top_2,
            "n_positions": 2,
            "use_bear": use_bear,
            "rankings": [(r[0], r[1], round(r[2], 2)) for r in rankings[:5]],
        }
    top = get_top_rotation_ticker(lookback_days, use_leveraged=True, use_bear_when_negative=use_bear)
    return {
        "top_sector": top[1] if top else None,
        "top_ticker": top[0] if top else None,
        "top_return_5d": round(top[2], 2) if top else None,
        "top_2_tickers": None,
        "n_positions": 1,
        "use_bear": use_bear,
        "rankings": [(r[0], r[1], round(r[2], 2)) for r in rankings[:5]],
    }
