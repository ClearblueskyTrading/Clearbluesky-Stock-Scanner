# ============================================================
# 3 Stock Rotation - Live ranking for PTM
# ============================================================
# Used by PTM to get current week's Top 3 picks. Blended: 60% rotation + 15% GDX + 15% FCX + 10% cash.
# Ranks by prior 5-day return, returns leveraged ETF to trade.

from typing import Optional, Tuple, List

# Same universe as backtest
UNIVERSE: List[Tuple[str, str, str]] = [
    ("NVDA", "NVDA", "NVDU"), ("MU", "MU", "MUU"), ("AMD", "AMD", "AMUU"),
    ("TSM", "TSM", "TSMX"), ("AVGO", "AVGO", "AVL"), ("MSFT", "MSFT", "MSFU"),
    ("AAPL", "AAPL", "AAPU"), ("AMZN", "AMZN", "AMZU"), ("GOOGL", "GOOGL", "GGLL"),
    ("META", "META", "METU"), ("TSLA", "TSLA", "TSLL"), ("NFLX", "NFLX", "NFXL"),
    ("PLTR", "PLTR", "PLTU"), ("PANW", "PANW", "PALU"), ("QCOM", "QCOM", "QCMU"),
    ("SHOP", "SHOP", "SHPU"), ("ASML", "ASML", "ASMU"), ("MRVL", "MRVL", "MRVU"),
    ("CSCO", "CSCO", "CSCL"), ("INTC", "INTC", "LINT"), ("ORCL", "ORCL", "ORCU"),
    ("COIN", "COIN", "CONX"), ("Tech", "XLK", "TECL"), ("Energy", "XLE", "ERX"),
    ("XOM", "XOM", "XOMX"), ("CRCL", "CRCL", "CRCA"), ("LRCX", "LRCX", "LRCU"),
    ("WDC", "WDC", "WDCX"),
]

# All leveraged tickers we might hold
ROTATION_TICKERS = frozenset([u[2] for u in UNIVERSE])

# Top N weights: (40, 35, 25) for top 3
TOP_N_WEIGHTS: dict = {1: (100,), 2: (60, 40), 3: (40, 35, 25)}


def get_top_single_stock_rotation_pick(lookback_days: int = 5) -> Optional[Tuple[str, str, float]]:
    """
    Rank by prior N-day return. Returns (leveraged_ticker, name, return_pct) or None.
    """
    try:
        import yfinance as yf
        import pandas as pd
    except ImportError:
        return None

    best_ret = None
    best_lev = None
    best_name = None

    for name, sig, lev in UNIVERSE:
        try:
            t = yf.Ticker(sig)
            hist = t.history(period="1mo")
            if hist is None or len(hist) < lookback_days + 2:
                continue
            close = hist["Close"]
            start_p = float(close.iloc[-lookback_days - 1])
            end_p = float(close.iloc[-1])
            if start_p <= 0:
                continue
            ret = (end_p - start_p) / start_p * 100
            # Check leveraged ETF has data
            t_lev = yf.Ticker(lev)
            h_lev = t_lev.history(period="5d")
            if h_lev is None or len(h_lev) < 2:
                continue
            if best_ret is None or ret > best_ret:
                best_ret = ret
                best_lev = lev
                best_name = name
        except Exception:
            continue

    if best_lev:
        return (best_lev, best_name, best_ret)
    return None


def get_top_n_single_stock_rotation_picks(lookback_days: int = 5, top_n: int = 3) -> List[Tuple[str, str, float, float]]:
    """
    Top N picks with weights. Returns [(leveraged_ticker, name, return_pct, weight_pct), ...].
    Weights: 1=100%, 2=60/40, 3=40/35/25.
    """
    rankings = get_single_stock_rotation_rankings(lookback_days, top_n=top_n)
    weights = TOP_N_WEIGHTS.get(top_n, TOP_N_WEIGHTS[3])[:top_n]
    return [(lev, name, ret, float(w)) for (lev, name, ret), w in zip(rankings, weights)]


def get_single_stock_rotation_signal_for_report(lookback_days: int = 5, config: Optional[dict] = None) -> dict:
    """Return dict for report frontmatter/display (matches sector_rotation format)."""
    top_n = int((config or {}).get("ptm_single_stock_top_n", 3))
    picks = get_top_n_single_stock_rotation_picks(lookback_days, top_n=top_n)
    rankings = get_single_stock_rotation_rankings(lookback_days, top_n=5)
    # For backward compat: top_ticker = first pick, top_sector = first name
    first = picks[0] if picks else None
    top_3_tickers = [(p[0], p[1], round(p[2], 2), p[3]) for p in picks]  # ticker, name, ret, weight
    return {
        "top_sector": first[1] if first else None,
        "top_ticker": first[0] if first else None,
        "top_return_5d": round(first[2], 2) if first else None,
        "top_2_tickers": None,
        "top_3_tickers": top_3_tickers,
        "n_positions": top_n,
        "use_bear": False,
        "rankings": [(r[0], r[1], round(r[2], 2)) for r in rankings],
        "mode": "single_stock_rotation",
        "strategy_name": "3 Stock Rotation",
    }


def get_single_stock_rotation_rankings(lookback_days: int = 5, top_n: int = 5) -> List[Tuple[str, str, float]]:
    """Return top N (ticker, name, return_pct) sorted by return desc."""
    try:
        import yfinance as yf
    except ImportError:
        return []

    results = []
    for name, sig, lev in UNIVERSE:
        try:
            t = yf.Ticker(sig)
            hist = t.history(period="1mo")
            if hist is None or len(hist) < lookback_days + 2:
                continue
            close = hist["Close"]
            start_p = float(close.iloc[-lookback_days - 1])
            end_p = float(close.iloc[-1])
            if start_p <= 0:
                continue
            ret = (end_p - start_p) / start_p * 100
            t_lev = yf.Ticker(lev)
            if t_lev.history(period="5d") is None or len(t_lev.history(period="5d")) < 2:
                continue
            results.append((lev, name, ret))
        except Exception:
            continue

    results.sort(key=lambda x: -x[2])
    return results[:top_n]
