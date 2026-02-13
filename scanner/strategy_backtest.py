# ============================================================
# ClearBlueSky - Emotional Dip Strategy Backtest
# ============================================================
# Simulates our swing strategy over historical data:
# - Signal: Down 1-5% that day, above SMA200, RSI 25-55, rel vol > 1.2
# - Entry: Buy at close on signal day
# - Exit: Stop -2.5%, Target +3%, or max 5 trading days
#
# Run: python strategy_backtest.py [--months 6] [--tickers 100]

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import pandas as pd
    import yfinance as yf
except ImportError as e:
    print("Requires: pip install pandas yfinance")
    sys.exit(1)

# Strategy params – best cumulative (780d backtest: ~195%)
DIP_MIN_PCT = 1.5
DIP_MAX_PCT = 4.0
STOP_PCT = -2.0
TARGET_PCT = 3.0
MAX_HOLD_DAYS = 5
MAX_HOLD_LEVERAGED = 3

# Win-rate mode (use --win-rate): stop -2.5%, target +1%, 3d hold → 56% win, lower cumulative
WIN_RATE_STOP = -2.5
WIN_RATE_TARGET = 1.0
WIN_RATE_MAX_HOLD = 3
MIN_VOL_RATIO = 1.2
REQUIRE_ABOVE_SMA200 = True
RSI_MIN = 30
RSI_MAX = 50
MIN_PRICE = 5.0
MAX_PRICE = 500.0
TRAIL_TRIGGER_PCT = None  # no trail; using hard target/stop

SECTOR_TO_ETF = {
    "Technology": "XLK",
    "Financial": "XLF",
    "Financials": "XLF",
    "Energy": "XLE",
    "Healthcare": "XLV",
    "Health Care": "XLV",
    "Industrials": "XLI",
    "Consumer Defensive": "XLP",
    "Consumer Staples": "XLP",
    "Consumer Cyclical": "XLY",
    "Consumer Discretionary": "XLY",
    "Utilities": "XLU",
    "Basic Materials": "XLB",
    "Materials": "XLB",
    "Real Estate": "XLRE",
    "Communication Services": "XLC",
    "Telecom Services": "XLC",
}
SECTOR_ETFS = sorted(set(SECTOR_TO_ETF.values()))

# Static ETF -> sector ETF (for momentum check). No yfinance .info on ETFs.
GICS_TO_SECTOR_ETF = {
    "Technology": "XLK", "Information Technology": "XLK",
    "Financial": "XLF", "Financials": "XLF",
    "Energy": "XLE",
    "Healthcare": "XLV", "Health Care": "XLV",
    "Industrials": "XLI",
    "Consumer Defensive": "XLP", "Consumer Staples": "XLP",
    "Consumer Cyclical": "XLY", "Consumer Discretionary": "XLY",
    "Utilities": "XLU",
    "Basic Materials": "XLB", "Materials": "XLB",
    "Real Estate": "XLRE",
    "Communication Services": "XLC", "Telecom Services": "XLC",
}
ETF_TO_SECTOR_ETF = {
    "TQQQ": "XLK", "QLD": "XLK", "SOXL": "XLK", "TECL": "XLK", "NVDL": "XLK",
    "UPRO": "SPY", "SSO": "SPY", "SPXL": "SPY",
    "FAS": "XLF", "DPST": "XLF",
    "TNA": "IWM", "IWM": "IWM",
    "ERX": "XLE", "GUSH": "XLE", "NUGT": "GDX", "JNUG": "GDX",
    "CURE": "XLV", "LABU": "XLV", "XBI": "XLV",
    "DUSL": "XLI", "DFEN": "XLI",
    "WANT": "XLY", "RETL": "XLY",
    "DRN": "XLRE", "NAIL": "XHB",
    "SPY": "SPY", "QQQ": "QQQ", "DIA": "DIA", "IWM": "IWM",
    "XLK": "XLK", "XLF": "XLF", "XLE": "XLE", "XLV": "XLV", "XLI": "XLI",
    "XLP": "XLP", "XLY": "XLY", "XLU": "XLU", "XLB": "XLB", "XLRE": "XLRE", "XLC": "XLC",
    "SMH": "XLK", "GDX": "GDX", "GLD": "GLD", "SLV": "SLV", "USO": "USO",
}

LEVERAGED_ETFS = frozenset([
    "TQQQ", "QLD", "UPRO", "SSO", "SPXL", "TNA", "SOXL", "TECL",
    "FAS", "LABU", "ERX", "GUSH", "NUGT", "CURE", "DFEN", "DPST", "UTSL",
    "NVDL", "TSLL", "AAPU", "AMZU", "GGLL", "MSFU", "CONL", "BITX", "BITU",
    "YINN", "EDC", "SQQQ", "QID", "SPXU", "SDS", "SPXS", "SOXS", "TECS", "TZA",
    "FAZ", "LABD", "ERY", "DRIP", "DUST", "SDOW", "SRTY", "WANT", "RETL", "DRN",
    "NAIL", "UCO", "JNUG",
])


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))


FALLBACK_TICKERS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "JPM", "V", "UNH", "XOM", "JNJ", "WMT",
    "PG", "MA", "HD", "CVX", "MRK", "ABBV", "PEP", "KO", "COST", "AVGO", "MCD", "CSCO",
    "ACN", "ABT", "TMO", "DHR", "ADBE", "NEE", "NFLX", "WFC", "DIS", "CRM", "TXN", "BMY",
    "RTX", "UPS", "HON", "ORCL", "INTC", "AMD", "QCOM", "COP", "IBM", "GE", "CAT", "BA",
    "GS", "MS", "AXP", "BLK", "SBUX", "DE", "INTU", "LOW", "AMGN", "GILD", "MDT", "ISRG",
    "VRTX", "REGN", "LMT", "ADI", "BKNG", "SYK", "TJX", "MMC", "CI", "DUK", "SO", "CMCSA",
    "EOG", "MO", "APD", "BDX", "CL", "BSX", "ITW", "PM", "C", "BAC", "USB", "PNC", "TFC",
    "AXP", "COF", "BK", "STT", "NUE", "FCX", "APTV", "ALGN", "IDXX", "DXCM", "HCA", "ELV",
]


def _get_sp500_tickers(limit: int = 150) -> List[str]:
    """Get S&P 500 tickers - CSV first, then fallback list."""
    try:
        from breadth import _FALLBACK_SP500, _fetch_sp500_from_csv
        rows = _fetch_sp500_from_csv(None)
        if rows:
            tickers = [str(r.get("Ticker", r.get("Symbol", ""))).strip().upper().replace("BRK-B", "BRK.B") for r in rows if r]
            tickers = [t for t in tickers if t and len(t) <= 6 and not t.startswith(".")]
            return tickers[:limit] if limit else tickers
        return [t for t in _FALLBACK_SP500 if isinstance(t, str)][:limit]
    except Exception:
        pass
    return FALLBACK_TICKERS[:limit]


def _get_tickers(limit: int = 150, universe: str = "sp500") -> List[str]:
    """
    Get ticker list by universe.
    sp500: S&P 500 only
    sp500_etfs: S&P 500 + curated ETFs (includes leveraged TQQQ, SOXL, SPXL, etc.)
    etfs: Curated ETFs only (sector + leveraged)
    velocity: High-conviction list (TQQQ, SOXL, NVDA, etc.)
    """
    if universe == "velocity":
        try:
            from velocity_scanner import SCAN_UNIVERSE
            return list(SCAN_UNIVERSE)[:limit]
        except Exception:
            return ["TQQQ", "SOXL", "SPXL", "NVDA", "AMD", "META", "AAPL", "MSFT", "JPM"][:limit]

    if universe == "etfs":
        try:
            from breadth import CURATED_ETFS
            return list(CURATED_ETFS)[:limit]
        except Exception:
            return ["SPY", "QQQ", "TQQQ", "SOXL", "SPXL", "XLF", "XLK", "XLE", "XLV", "IWM", "TNA"][:limit]

    if universe == "sp500_etfs":
        sp500 = _get_sp500_tickers(limit or 150)
        try:
            from breadth import CURATED_ETFS
            # Put ETFs (incl. leveraged) first so they're never dropped when capping
            etfs = [t for t in CURATED_ETFS if t]
            combined = list(dict.fromkeys(etfs + sp500))
            return combined[:limit] if limit else combined
        except Exception:
            etfs = ["SPY", "QQQ", "TQQQ", "SOXL", "SPXL", "TECL", "UPRO", "SSO", "TNA", "FAS", "XLF", "XLK"]
            combined = list(dict.fromkeys(etfs + sp500))
            return combined[:limit] if limit else combined

    return _get_sp500_tickers(limit)


def _get_ticker_data(data: pd.DataFrame, ticker: str) -> Optional[pd.DataFrame]:
    """Extract OHLCV for one ticker from multi-ticker download."""
    try:
        if isinstance(data.columns, pd.MultiIndex):
            if ticker in data.columns.get_level_values(0):
                return data[ticker].copy()
        else:
            return data.copy()
    except Exception:
        pass
    return None


def _load_sp500_sector_map() -> Dict[str, str]:
    """Build ticker -> sector ETF from S&P 500 CSV. Static, no yfinance."""
    out = {}
    try:
        from breadth import _fetch_sp500_from_csv
        rows = _fetch_sp500_from_csv(None)
        for r in (rows or []):
            t = str(r.get("Ticker") or "").strip().upper().replace("BRK-B", "BRK.B")
            sector = (r.get("Sector") or "").strip()
            if t and sector:
                etf = GICS_TO_SECTOR_ETF.get(sector) or SECTOR_TO_ETF.get(sector)
                if etf:
                    out[t] = etf
    except Exception:
        pass
    return out


def _get_sector_etf(ticker: str, sector_cache: dict, sp500_map: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Map ticker to sector ETF. Uses static maps only (no yfinance .info)."""
    t = str(ticker or "").strip().upper()
    if t in sector_cache:
        return sector_cache[t]
    # 1) Known ETF
    if t in ETF_TO_SECTOR_ETF:
        sector_cache[t] = ETF_TO_SECTOR_ETF[t]
        return sector_cache[t]
    # 2) S&P 500 stock from CSV
    if sp500_map and t in sp500_map:
        sector_cache[t] = sp500_map[t]
        return sector_cache[t]
    sector_cache[t] = None
    return None


def _sector_uptrend(data: pd.DataFrame, ticker: str, date: pd.Timestamp, sector_cache: dict, sp500_map: Optional[Dict[str, str]] = None) -> bool:
    """Require sector ETF above SMA50; if unknown or missing data, allow."""
    etf = _get_sector_etf(ticker, sector_cache, sp500_map)
    if not etf:
        return True
    td = _get_ticker_data(data, etf)
    if td is None or "Close" not in td.columns:
        return True
    close = td["Close"].loc[td.index <= date].tail(100)
    if len(close) < 50:
        return True
    sma50 = close.rolling(50).mean().iloc[-1]
    current = close.iloc[-1]
    return bool(current > sma50)


def _earnings_within(ticker: str, date: pd.Timestamp, earnings_cache: dict, window_days: int = 5) -> bool:
    """Check if earnings within ±window_days. ETFs have no earnings (return False). Stocks: yfinance .calendar only."""
    t = str(ticker or "").strip().upper()
    # ETFs don't have earnings - skip yfinance entirely to avoid 404
    if t in ETF_TO_SECTOR_ETF or t in LEVERAGED_ETFS or t in SECTOR_ETFS:
        return False
    if t in earnings_cache:
        next_earn = earnings_cache[t]
    else:
        next_earn = None
        try:
            import yfinance as yf
            cal = yf.Ticker(t).calendar
            if cal is not None:
                if "Earnings Date" in cal.index:
                    val = cal.loc["Earnings Date"].values[0]
                    if hasattr(val, "to_pydatetime"):
                        next_earn = val.to_pydatetime()
                elif "Earnings Date" in cal.columns:
                    val = cal["Earnings Date"].iloc[0]
                    if hasattr(val, "to_pydatetime"):
                        next_earn = val.to_pydatetime()
        except Exception:
            pass
        earnings_cache[t] = next_earn
    if not next_earn:
        return False
    delta = abs((next_earn - date).days)
    return delta <= window_days


def compute_signals(data: pd.DataFrame, date: pd.Timestamp, tickers: List[str], sector_cache: dict, earnings_cache: dict, sp500_map: Optional[Dict[str, str]] = None, use_sector_filter: bool = False, use_earnings_filter: bool = False) -> List[Dict]:
    """
    For a given date, find stocks that would have triggered our emotional dip signal.
    """
    if data is None or data.empty or len(data) < 50:
        return []

    signals = []
    for ticker in tickers:
        try:
            td = _get_ticker_data(data, ticker)
            if td is None or "Close" not in td.columns:
                continue

            close = td["Close"].loc[td.index <= date].tail(220)
            if len(close) < 200:
                continue
            if close.empty or close.index[-1] != date:
                continue

            prev_close = float(close.iloc[-2])
            current = float(close.iloc[-1])
            if prev_close <= 0:
                continue

            chg_pct = (current - prev_close) / prev_close * 100
            if not (-DIP_MAX_PCT <= chg_pct <= -DIP_MIN_PCT):
                continue
            if not (MIN_PRICE <= current <= MAX_PRICE):
                continue

            sma200 = close.rolling(200).mean().iloc[-1]
            if pd.isna(sma200) or sma200 <= 0:
                continue
            if REQUIRE_ABOVE_SMA200 and current <= sma200:
                continue

            rsi_series = _rsi(close, 14)
            rsi = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50
            if rsi < RSI_MIN or rsi > RSI_MAX:
                continue

            if "Volume" in td.columns:
                vol = td["Volume"].loc[td.index <= date].tail(25)
                if len(vol) >= 21:
                    avg_vol = vol.iloc[-21:-1].mean()
                    if avg_vol and avg_vol > 0:
                        rel_vol = vol.iloc[-1] / avg_vol
                        if rel_vol < MIN_VOL_RATIO:
                            continue

            # Sector momentum gate (optional)
            if use_sector_filter and not _sector_uptrend(data, ticker, date, sector_cache, sp500_map):
                continue

            # Earnings proximity gate (optional)
            if use_earnings_filter and _earnings_within(ticker, date, earnings_cache, window_days=5):
                continue

            signals.append({
                "ticker": str(ticker),
                "date": date.strftime("%Y-%m-%d"),
                "close": current,
                "change_pct": round(chg_pct, 2),
                "rsi": round(rsi, 1),
            })
        except Exception:
            continue

    return signals


def _get_close_on_date(data: pd.DataFrame, ticker: str, date: pd.Timestamp) -> Optional[float]:
    """Get close price for ticker on given date."""
    try:
        td = _get_ticker_data(data, ticker)
        if td is None or "Close" not in td.columns:
            return None
        row = td["Close"][td.index == date]
        if row.empty:
            row = td["Close"][td.index <= date]
            if row.empty:
                return None
            return float(row.iloc[-1])
        return float(row.iloc[0])
    except Exception:
        return None


def _get_high_on_date(data: pd.DataFrame, ticker: str, date: pd.Timestamp) -> Optional[float]:
    """Get high price for ticker on given date (for trailing stop)."""
    try:
        td = _get_ticker_data(data, ticker)
        if td is None or "High" not in td.columns:
            return None
        row = td["High"][td.index == date]
        if row.empty:
            return None
        return float(row.iloc[0])
    except Exception:
        return None


def _is_bear_regime(data: pd.DataFrame, date: pd.Timestamp) -> bool:
    """SPY below SMA200 = Bear regime (reduce positions)."""
    try:
        td = _get_ticker_data(data, "SPY")
        if td is None or "Close" not in td.columns:
            return False
        close = td["Close"].loc[td.index <= date].tail(220)
        if len(close) < 200:
            return False
        sma200 = close.rolling(200).mean().iloc[-1]
        current = close.iloc[-1]
        return current < sma200
    except Exception:
        return False


def run_backtest(tickers: List[str], start_date: str, end_date: str, position_size: float = 5000, use_sector_filter: bool = False, use_earnings_filter: bool = False, stop_pct: Optional[float] = None, target_pct: Optional[float] = None, max_hold_days: Optional[int] = None, max_hold_leveraged: Optional[int] = None) -> Dict:
    """
    Run full backtest. Returns stats dict.
    """
    print(f"Backtest: {start_date} to {end_date} | {len(tickers)} tickers")
    # Fetch extra history for SMA200 warmup
    from datetime import datetime as dt
    start_dt = dt.strptime(start_date[:10], "%Y-%m-%d")
    fetch_start = (start_dt - timedelta(days=300)).strftime("%Y-%m-%d")
    # Add SPY for regime check and sector ETFs for sector momentum
    base_tickers = list(tickers)
    if "SPY" not in base_tickers:
        base_tickers = ["SPY"] + base_tickers
    sector_proxies = sorted(set(ETF_TO_SECTOR_ETF.values()))
    dl_tickers = list(dict.fromkeys(base_tickers + SECTOR_ETFS + sector_proxies))
    print("Fetching historical data (this may take 1-2 min)...")

    try:
        data = yf.download(
            dl_tickers,
            start=fetch_start,
            end=end_date,
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
    except Exception as e:
        print(f"Download error: {e}")
        return {"error": str(e)}

    if data is None or data.empty:
        print("No data returned.")
        return {"error": "No data"}

    # Flatten if single ticker (yfinance returns non-MultiIndex for 1 ticker)
    if len(tickers) == 1 or not isinstance(data.columns, pd.MultiIndex):
        if "Close" in data.columns and not isinstance(data.columns, pd.MultiIndex):
            tmp = data.copy()
            tmp.columns = pd.MultiIndex.from_product([[tickers[0]], data.columns])
            data = tmp

    dates = sorted([d for d in data.index if isinstance(d, (pd.Timestamp, datetime))])
    start_ts = pd.Timestamp(start_date)
    dates = [d for d in dates if d >= start_ts]
    if not dates:
        print("No valid dates in data.")
        return {"error": "No dates"}

    trades: List[Dict] = []
    open_positions: Dict[str, Dict] = {}
    sector_cache: dict = {}
    earnings_cache: dict = {}
    sp500_map = _load_sp500_sector_map()
    stop_p = stop_pct if stop_pct is not None else STOP_PCT
    target_p = target_pct if target_pct is not None else TARGET_PCT
    max_hold_d = max_hold_days if max_hold_days is not None else MAX_HOLD_DAYS
    max_hold_l = max_hold_leveraged if max_hold_leveraged is not None else MAX_HOLD_LEVERAGED

    for i, d in enumerate(dates):
        day = d if isinstance(d, pd.Timestamp) else pd.Timestamp(d)
        day_str = day.strftime("%Y-%m-%d")

        # 1) Check exits for open positions
        for tkr, pos in list(open_positions.items()):
            price = _get_close_on_date(data, tkr, day)
            if price is None:
                continue
            entry_price = pos["entry_price"]
            pct = (price - entry_price) / entry_price * 100
            hold_days = (day - pos["entry_date"]).days
            max_hold = max_hold_l if tkr in LEVERAGED_ETFS else max_hold_d

            # Trailing stop (optional)
            exit_reason = None
            if TRAIL_TRIGGER_PCT is not None:
                trail_triggered = pos.get("trail_triggered", False)
                high = _get_high_on_date(data, tkr, day)
                if high is not None and high >= entry_price * (1 + TRAIL_TRIGGER_PCT / 100):
                    trail_triggered = True
                    pos["trail_triggered"] = True
                # Breakeven trail: once triggered, exit if close < entry
                if trail_triggered and price < entry_price:
                    exit_reason = "trail"

            if exit_reason is None and pct <= stop_p:
                exit_reason = "stop"
            elif exit_reason is None and target_p is not None and pct >= target_p:
                exit_reason = "target"
            elif exit_reason is None and hold_days >= max_hold:
                exit_reason = "max_days"

            if exit_reason:
                trades.append({
                    "ticker": tkr,
                    "entry_date": pos["entry_date"].strftime("%Y-%m-%d"),
                    "exit_date": day_str,
                    "entry_price": entry_price,
                    "exit_price": price,
                    "pct_return": round(pct, 2),
                    "exit_reason": exit_reason,
                })
                del open_positions[tkr]

        # 2) Regime: bear = max 2 positions, normal = 3
        bear = _is_bear_regime(data, day)
        max_pos = 2 if bear else 3

        if len(open_positions) >= max_pos:
            continue

        try:
            sigs = compute_signals(data, day, tickers, sector_cache, earnings_cache, sp500_map, use_sector_filter, use_earnings_filter)
        except Exception:
            sigs = []

        for s in sigs[: max_pos - len(open_positions)]:
            tkr = s["ticker"]
            if tkr in open_positions:
                continue
            open_positions[tkr] = {
                "entry_date": day,
                "entry_price": s["close"],
                "size": position_size,
            }

    # Close any remaining at last date
    last_date = dates[-1]
    for tkr, pos in list(open_positions.items()):
        price = _get_close_on_date(data, tkr, last_date)
        if price is not None:
            pct = (price - pos["entry_price"]) / pos["entry_price"] * 100
            trades.append({
                "ticker": tkr,
                "entry_date": pos["entry_date"].strftime("%Y-%m-%d"),
                "exit_date": last_date.strftime("%Y-%m-%d"),
                "entry_price": pos["entry_price"],
                "exit_price": price,
                "pct_return": round(pct, 2),
                "exit_reason": "eod",
            })

    # Stats
    if not trades:
        return {
            "trades": 0,
            "win_rate": 0,
            "avg_return": 0,
            "total_return_pct": 0,
            "stops": 0,
            "targets": 0,
            "trails": 0,
            "max_days": 0,
            "eod": 0,
            "by_exit": {},
        }

    wins = sum(1 for t in trades if t["pct_return"] > 0)
    stops = sum(1 for t in trades if t["exit_reason"] == "stop")
    targets = sum(1 for t in trades if t["exit_reason"] == "target")
    trails = sum(1 for t in trades if t["exit_reason"] == "trail")
    max_days_exits = sum(1 for t in trades if t["exit_reason"] == "max_days")
    eod_exits = sum(1 for t in trades if t["exit_reason"] == "eod")
    avg_ret = sum(t["pct_return"] for t in trades) / len(trades)

    return {
        "trades": len(trades),
        "win_rate": round(wins / len(trades) * 100, 1),
        "avg_return": round(avg_ret, 2),
        "total_return_pct": round(sum(t["pct_return"] for t in trades), 2),
        "stops": stops,
        "targets": targets,
        "trails": trails,
        "max_days": max_days_exits,
        "eod": eod_exits,
        "by_exit": {
            "stop": stops,
            "target": targets,
            "trail": trails,
            "max_days": max_days_exits,
            "eod": eod_exits,
        },
        "trade_list": trades,
    }


def _write_report(args, result: Dict, start_str: str, end_str: str, period_label: str, tickers: List[str]) -> None:
    """Write backtest results to MD file for Discord sharing."""
    lines = [
        "# Emotional Dip Strategy Backtest Report",
        "",
        f"**Period:** {start_str} to {end_str} ({period_label})",
        f"**Universe:** {args.universe} ({len(tickers)} tickers)",
        "",
        "---",
        "",
        "## Strategy Used",
        "",
        "### Entry Signal (approximates emotional dip scanner)",
        "- Down **1.5–4%** that day (close vs prior close)",
        "- Price **above SMA200**",
        "- **RSI 30–50** (oversold but not crashed)",
        "- **Relative volume ≥ 1.2x** (20-day avg)",
        "- Price between **$5–$500**",
        "- Sector ETF above SMA50 (--sector to enable)",
        "- Skip if earnings within ±5 days (--earnings to enable)",
        "",
        "### Exit Rules",
        "- **Stop:** -2%",
        "- **Target:** +3%",
        "- **Max hold:** 5 days (stocks) / 3 days (leveraged ETFs)",
        "- **Position limit:** 3 (normal) / 2 (bear regime: SPY < SMA200)",
        "",
        "### Entry",
        "- Buy at close on signal day",
        "",
        "---",
        "",
        "## Results",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| **Trades** | {result['trades']} |",
        f"| **Win Rate** | {result['win_rate']}% |",
        f"| **Avg Return/Trade** | {result['avg_return']}% |",
        f"| **Cumulative Return** | {result['total_return_pct']}% |",
        "",
        f"### Exits",
        f"- Stop: {result['stops']} | Target: {result['targets']} | Trail: {result.get('trails', 0)} | Max Days: {result['max_days']} | EOD: {result.get('eod', 0)}",
        "",
    ]
    if result.get("trade_list"):
        lines.extend(["### Sample Trades (first 15)", ""])
        for t in result["trade_list"][:15]:
            lines.append(f"- **{t['ticker']}**: {t['entry_date']} → {t['exit_date']} | {t['pct_return']:+.2f}% ({t['exit_reason']})")
        lines.extend(["", ""])
    lines.append("*Generated by ClearBlueSky strategy_backtest.py*")
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Backtest Emotional Dip strategy")
    ap.add_argument("--months", type=int, default=None, help="Months to backtest (ignored if --trading-days set)")
    ap.add_argument("--trading-days", type=int, default=None, help="Number of trading days to backtest (e.g. 780 = ~3 years)")
    ap.add_argument("--tickers", type=int, default=100, help="Max tickers in universe (default 100, 0=all)")
    ap.add_argument("--size", type=float, default=5000, help="Position size $ (default 5000)")
    ap.add_argument("--universe", choices=["sp500", "sp500_etfs", "etfs", "velocity"], default="sp500",
                    help="Universe: sp500, sp500_etfs (S&P+leveraged ETFs), etfs, velocity (default sp500)")
    ap.add_argument("--report", type=str, default=None, help="Write results to MD file (e.g. backtest_report.md)")
    ap.add_argument("--sector", action="store_true", help="Enable sector momentum filter (off by default)")
    ap.add_argument("--earnings", action="store_true", help="Enable earnings proximity filter (off by default)")
    ap.add_argument("--win-rate", action="store_true", help="Win-rate mode: stop -2.5%%, target +1%%, 3d hold (56%% win, lower cumulative)")
    ap.add_argument("--stop", type=float, default=None, help="Override stop %% (e.g. -1.5)")
    ap.add_argument("--target", type=float, default=None, help="Override target %% (e.g. 0.5)")
    ap.add_argument("--max-hold", type=int, default=None, help="Override max hold days")
    args = ap.parse_args()

    end = datetime.now()
    if args.trading_days is not None:
        # 252 trading days/year, ~1.45 calendar days per trading day
        cal_days = int(args.trading_days * 365 / 252)
        start = end - timedelta(days=cal_days)
        period_label = f"{args.trading_days} trading days (~{args.trading_days/252:.1f} years)"
    else:
        months = args.months or 6
        start = end - timedelta(days=months * 31)
        period_label = f"{months} months"
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    tickers = _get_tickers(args.tickers or 9999, universe=args.universe)
    kw = {"use_sector_filter": args.sector, "use_earnings_filter": args.earnings}
    if args.win_rate:
        kw.update(stop_pct=WIN_RATE_STOP, target_pct=WIN_RATE_TARGET, max_hold_days=WIN_RATE_MAX_HOLD, max_hold_leveraged=WIN_RATE_MAX_HOLD)
    if args.stop is not None:
        kw["stop_pct"] = args.stop
    if args.target is not None:
        kw["target_pct"] = args.target
    if args.max_hold is not None:
        kw["max_hold_days"] = kw["max_hold_leveraged"] = args.max_hold
    result = run_backtest(tickers, start_str, end_str, position_size=args.size, **kw)

    if result.get("error"):
        print(f"Error: {result['error']}")
        return 1

    print("\n" + "=" * 60)
    print("EMOTIONAL DIP STRATEGY BACKTEST RESULTS")
    print("=" * 60)
    print(f"Period: {start_str} to {end_str} ({period_label})")
    print(f"Trades: {result['trades']}")
    print(f"Win rate: {result['win_rate']}%")
    print(f"Avg return per trade: {result['avg_return']}%")
    print(f"Cumulative return (all trades): {result['total_return_pct']}%")
    print(f"\nExits: Stop={result['stops']} | Target={result['targets']} | Trail={result.get('trails', 0)} | MaxDays={result['max_days']} | EOD={result.get('eod', 0)}")

    if result.get("trade_list"):
        print("\n--- Sample trades (first 10) ---")
        for t in result["trade_list"][:10]:
            print(f"  {t['ticker']}: {t['entry_date']} -> {t['exit_date']} | {t['pct_return']:+.2f}% ({t['exit_reason']})")

    if args.report:
        _write_report(args, result, start_str, end_str, period_label, tickers)
        print(f"\nReport saved to: {args.report}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
