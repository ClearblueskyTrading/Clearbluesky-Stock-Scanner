# ClearBlueSky - Velocity Trend Growth Scanner
# Momentum-based growth scanner: set trend days (5/20/50 trading days) and target return %.
# Ranks tickers by N-day total return; filters by desired return.
#
# Math: total return = (close_now - close_N_days_ago) / close_N_days_ago * 100
# Bars = trading days (no weekends/holidays). Uses adjusted close (splits/dividends).
# For 50 trading days we need ~72 calendar days of data (50 * 365/252).

import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

INDEX_UNIVERSE_CAP = 400  # S&P 500 + ETFs combined
TOP_SECTORS_COUNT = 4  # Scan only tickers in top N sectors by momentum
SECTOR_ETF_TO_FINVIZ = {
    "XLK": "Technology",
    "XLF": "Financial",
    "XLE": "Energy",
    "XLV": "Healthcare",
    "XLI": "Industrials",
    "XLP": "Consumer Defensive",
    "XLY": "Consumer Cyclical",
    "XLU": "Utilities",
    "XLB": "Basic Materials",
    "XLRE": "Real Estate",
    "XLC": "Communication Services",
}
INDEX_ETFS = ["SPY", "QQQ", "IWM", "DIA", "TQQQ", "QLD", "UPRO", "SOXL"]  # always include


def _rank_sectors_by_return(days: int, progress_callback=None) -> List[tuple]:
    """Rank sectors by N-day return using sector SPDRs. Returns [(sector_name, return_pct), ...] sorted best first."""
    results = []
    for ticker, sector in SECTOR_ETF_TO_FINVIZ.items():
        if progress_callback and len(results) == 0:
            progress_callback(f"Ranking sectors ({days}d return)...")
        row = _fetch_ticker_analysis(ticker, days, need_volume=False, need_rsi=False, need_ma=False)
        if row is not None:
            ret = row.get("n_day_return_pct", 0)
            results.append((sector, ret))
        time.sleep(0.15)
    results.sort(key=lambda x: -x[1])
    return results


def _get_universe(index: str, progress_callback=None, trend_days: int = 20) -> tuple:
    """
    Sector-first: rank sectors by momentum, then fetch tickers in leading sectors.
    index: 'sp500' = S&P 500 only; 'etfs' = ETFs only; 'sp500_etfs' = combined.
    Returns (tickers, sector_map). sector_map: ticker -> sector name.
    """
    if index not in ("sp500", "etfs", "sp500_etfs"):
        return [], {}
    try:
        # 1. Rank sectors by N-day return (sector ETFs)
        sector_rank = _rank_sectors_by_return(trend_days, progress_callback)
        top_sectors = {s[0] for s in sector_rank[:TOP_SECTORS_COUNT]} if sector_rank else set()
        if not top_sectors:
            top_sectors = set(SECTOR_ETF_TO_FINVIZ.values())  # fallback: all sectors
        if progress_callback and sector_rank:
            leading = ", ".join(f"{s[0]} ({s[1]:+.1f}%)" for s in sector_rank[:3])
            progress_callback(f"Leading sectors: {leading}")

        # 2. Fetch universe based on toggle (S&P 500 only, ETFs only, or combined)
        from breadth import fetch_sp500_only, fetch_etfs_only, fetch_sp500_plus_curated_etfs
        if index == "sp500":
            rows = fetch_sp500_only(progress_callback)
        elif index == "etfs":
            rows = fetch_etfs_only(progress_callback)
        else:
            rows = fetch_sp500_plus_curated_etfs(progress_callback)

        tickers = []
        sector_map = {}
        for r in (rows or []):
            t = str(r.get("Ticker") or "").strip().upper()
            if not t:
                continue
            sector = (r.get("Sector") or r.get("Industry") or "Unknown").strip()
            sector_map[t] = sector
            # ETFs-only: include all (full list). S&P 500 only: sectors. Combined: index ETFs + sectors
            if index == "etfs":
                tickers.append(t)
            elif index == "sp500":
                if sector in top_sectors:
                    tickers.append(t)
            else:
                if t in INDEX_ETFS or sector in top_sectors:
                    tickers.append(t)

        if index != "etfs":
            tickers = tickers[:INDEX_UNIVERSE_CAP]
        return tickers, sector_map
    except Exception:
        return [], {}


def _compute_rsi(closes, period: int = 14) -> Optional[float]:
    """Compute RSI from close series. Returns None if insufficient data."""
    if closes is None or len(closes) < period + 1:
        return None
    try:
        deltas = closes.diff()
        gains = deltas.where(deltas > 0, 0.0)
        losses = (-deltas).where(deltas < 0, 0.0)
        avg_gain = gains.rolling(period).mean().iloc[-1]
        avg_loss = losses.rolling(period).mean().iloc[-1]
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return float(100 - (100 / (1 + rs)))
    except Exception:
        return None


def _fetch_ticker_analysis(
    ticker: str,
    days: int,
    need_volume: bool = True,
    need_rsi: bool = True,
    need_ma: bool = True,
    need_sma200: bool = False,
) -> Optional[Dict[str, Any]]:
    """Fetch N-day history and compute return, RSI, volume, MA stack, optional SMA200 status."""
    if days < 1:
        return None
    df = None
    need_bars = max(days + 1, 51) if need_ma else (max(days + 1, 15) if need_rsi else days + 1)
    if need_sma200:
        need_bars = max(need_bars, 220)
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        cal_days = max(need_bars + 30, int(need_bars * 1.5))
        period = f"{min(cal_days, 365)}d"
        df = t.history(period=period, interval="1d", auto_adjust=True)
    except Exception:
        pass
    if df is None or df.empty or len(df) < days:
        try:
            from alpaca_data import has_alpaca_keys, get_bars, bars_to_dataframe
            if has_alpaca_keys():
                bars = get_bars(ticker, days=need_bars + 20, timeframe="1Day", limit=100)
                if bars:
                    df = bars_to_dataframe(bars)
        except Exception:
            pass
    if df is None or df.empty or len(df) < 2:
        return None
    try:
        df = df.sort_index()
        closes = df["Close"].dropna()
        if len(closes) < 2:
            return None
        lookback = min(days, len(closes) - 1)
        if lookback < 1:
            return None
        start_price = float(closes.iloc[-1 - lookback])
        end_price = float(closes.iloc[-1])
        if not start_price or start_price <= 0:
            return None
        ret_pct = (end_price - start_price) / start_price * 100

        out = {
            "ticker": ticker,
            "n_day_return_pct": round(ret_pct, 2),
            "price": round(end_price, 2),
            "start_price": round(start_price, 2),
            "days": lookback,
        }
        if need_volume and "Volume" in df.columns:
            vol = df["Volume"].dropna()
            if len(vol) >= 20:
                avg_vol = float(vol.iloc[-21:-1].mean())
                recent_vol = float(vol.iloc[-5:].mean())
                out["avg_volume"] = avg_vol
                out["recent_volume"] = recent_vol
                out["volume_above_avg"] = recent_vol > avg_vol if avg_vol > 0 else False
        if need_rsi and len(closes) >= 15:
            out["rsi"] = round(_compute_rsi(closes, 14) or 50, 1)
        if need_ma and len(closes) >= 51:
            ema10 = closes.ewm(span=10, adjust=False).mean().iloc[-1]
            ema20 = closes.ewm(span=20, adjust=False).mean().iloc[-1]
            ema50 = closes.ewm(span=50, adjust=False).mean().iloc[-1]
            out["ma_stack"] = end_price > ema10 > ema20 > ema50
        if need_sma200 and len(closes) >= 200:
            sma200 = closes.rolling(200).mean().iloc[-1]
            out["sma200"] = round(float(sma200), 2)
            out["above_sma200"] = bool(end_price > sma200)
        return out
    except Exception:
        return None


def run_velocity_trend_growth_scan(
    progress_callback=None,
    index: str = "sp500",
    trend_days: int = 20,
    target_return_pct: float = 12.0,
    risk_pct: float = 30.0,
    max_tickers: int = 20,
    min_price: float = 25.0,
    max_price: float = 600.0,
    require_beats_spy: bool = True,
    min_volume: int = 500000,
    require_volume_confirm: bool = True,
    require_above_sma200: bool = True,
    require_ma_stack: bool = False,
    rsi_min: int = 55,
    rsi_max: int = 80,
    cancel_event=None,
) -> Optional[List[Dict[str, Any]]]:
    """
    Velocity Trend Growth: momentum scan with sector grouping, SPY relative strength,
    volume confirmation, optional MA stack and RSI filters.
    """
    def progress(msg):
        print(msg)
        if progress_callback:
            progress_callback(msg)

    progress(f"Velocity Trend Growth: {trend_days}d trend, target {target_return_pct}% (S&P 500 + ETFs)...")

    try:
        from breadth import CURATED_ETFS, ETF_MIN_AVG_VOLUME
        etf_set = {str(t).strip().upper() for t in CURATED_ETFS}
        etf_min_avg_volume = ETF_MIN_AVG_VOLUME
    except Exception:
        etf_set = set()
        etf_min_avg_volume = 100_000

    tickers, sector_map = _get_universe(index, progress_callback, trend_days=trend_days)
    if not tickers:
        progress("No universe fetched")
        return None

    # Fetch SPY return for relative strength filter
    spy_return = None
    if require_beats_spy:
        spy_row = _fetch_ticker_analysis("SPY", trend_days, need_volume=False, need_rsi=False, need_ma=False)
        spy_return = spy_row.get("n_day_return_pct") if spy_row else None
        if spy_return is not None:
            progress(f"SPY {trend_days}d return: {spy_return:.1f}% (filter: must beat)")
        time.sleep(0.3)

    need_vol = require_volume_confirm or min_volume > 0
    need_rsi = rsi_min > 0 or rsi_max < 100
    results = []
    for i, t in enumerate(tickers):
        if cancel_event and getattr(cancel_event, "is_set", lambda: False)():
            progress("Cancelled")
            return None
        if (i + 1) % 30 == 0:
            progress(f"  {i + 1}/{len(tickers)}...")
        time.sleep(0.25)
        row = _fetch_ticker_analysis(
            t,
            trend_days,
            need_volume=need_vol,
            need_rsi=need_rsi,
            need_ma=require_ma_stack,
            need_sma200=require_above_sma200,
        )
        if row is None:
            continue
        price = row.get("price", 0)
        if price < min_price or price > max_price:
            continue
        ret = row.get("n_day_return_pct", 0)
        if target_return_pct > 0 and ret < target_return_pct:
            continue
        if require_beats_spy and spy_return is not None and ret <= spy_return:
            continue
        min_volume_required = min_volume
        if t in etf_set:
            min_volume_required = max(min_volume, etf_min_avg_volume)
        if min_volume_required > 0 and row.get("avg_volume", 0) < min_volume_required:
            continue
        if require_volume_confirm and row.get("volume_above_avg") is False:
            continue
        if require_above_sma200 and row.get("above_sma200") is not True:
            continue
        if require_ma_stack and row.get("ma_stack") is not True:
            continue
        rsi = row.get("rsi")
        if rsi is not None:
            if rsi_min > 0 and rsi < rsi_min:
                continue
            if rsi_max < 100 and rsi > rsi_max:
                continue

        sector = sector_map.get(t, "Unknown")
        # Tighter curve: only strong momentum (15%+) gets 70+, 20%+ gets 80+
        # 5%→42, 10%→55, 15%→68, 20%→80, 25%→92, 30%→100
        score = min(100, max(1, int(25 + ret * 2.5)))
        results.append({
            "Ticker": t,
            "ticker": t,
            "SCORE": score,
            "Score": score,
            "score": score,
            "Price": f"${price:.2f}",
            "price": price,
            "Change": f"+{ret:.1f}%" if ret >= 0 else f"{ret:.1f}%",
            "change": f"+{ret:.1f}%" if ret >= 0 else f"{ret:.1f}%",
            "n_day_return_pct": ret,
            "sector": sector,
            "rsi": rsi,
            "above_sma200": row.get("above_sma200"),
            "trend_days": trend_days,
            "target_return_pct": target_return_pct,
            "risk_pct": risk_pct,
        })

    # Sort by sector avg return (sector strength), then by individual return
    sector_avg = {}
    for r in results:
        s = r.get("sector", "Unknown")
        if s not in sector_avg:
            sector_avg[s] = []
        sector_avg[s].append(r.get("n_day_return_pct", 0))
    sector_mean = {s: sum(vals) / len(vals) for s, vals in sector_avg.items()}
    results.sort(key=lambda r: (-sector_mean.get(r.get("sector", "Unknown"), 0), -r.get("n_day_return_pct", 0)))
    results = results[:max_tickers]

    # Add sector heat: count per sector (e.g. "Technology (5)" for over/under representation)
    sector_count = {}
    for r in results:
        s = r.get("sector", "Unknown")
        sector_count[s] = sector_count.get(s, 0) + 1
    for r in results:
        s = r.get("sector", "Unknown")
        r["sector_heat"] = f"{s} ({sector_count.get(s, 0)})"

    progress(f"Done: {len(results)} tickers (>={target_return_pct}% in {trend_days}d)")
    return results if results else None
