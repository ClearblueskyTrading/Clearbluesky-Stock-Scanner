# ============================================================
# Inverse Play Backtest - UPRO/SPXU based on SPY direction
# ============================================================
# Modes:
#   5-day: Prior N-day SPY return -> UPRO or SPXU, hold 5 days.
#   Daily: 1-day hold. PDT-safe: buy afternoon, hold overnight, sell next afternoon.
#     --signal-mode same_day: Use today's return (close vs open). Scan afternoon, buy before close.
#     --signal-mode prior_day: Use yesterday's return. Scan morning, buy at open.
# Run: python inverse_play_backtest.py --daily [--signal-mode same_day|prior_day] [--stop-pct 5]
#      python inverse_play_backtest.py [--cycle 5] [--lookback 5]

import argparse
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

try:
    import pandas as pd
    import yfinance as yf
except ImportError:
    print("Requires: pip install pandas yfinance")
    sys.exit(1)

BULL_TICKER = "UPRO"   # 3x S&P 500
BEAR_TICKER = "SPXU"   # 3x S&P 500 inverse
SIGNAL_TICKER = "SPY"  # S&P 500 for direction signal


def _get_ohlc(data: pd.DataFrame, ticker: str, date: pd.Timestamp) -> Optional[tuple]:
    """Return (open, close) for ticker on date."""
    try:
        if isinstance(data.columns, pd.MultiIndex):
            if ticker not in data.columns.get_level_values(0):
                return None
            o = data[ticker]["Open"]
            c = data[ticker]["Close"]
        else:
            o, c = data["Open"], data["Close"]
        rows = data.loc[data.index <= date].tail(1)
        if rows.empty:
            return None
        idx = rows.index[-1]
        return (float(o.loc[idx]), float(c.loc[idx]))
    except Exception:
        return None


def _get_close(data: pd.DataFrame, ticker: str, date: pd.Timestamp) -> Optional[float]:
    try:
        if isinstance(data.columns, pd.MultiIndex):
            if ticker not in data.columns.get_level_values(0):
                return None
            close = data[ticker]["Close"]
        else:
            close = data["Close"]
        rows = close.loc[close.index <= date]
        if rows.empty:
            return None
        return float(rows.iloc[-1])
    except Exception:
        return None


def _get_same_day_return(data: pd.DataFrame, date: pd.Timestamp) -> Optional[float]:
    """SPY return today: (close - open) / open. For afternoon scan."""
    try:
        if isinstance(data.columns, pd.MultiIndex):
            o = data[SIGNAL_TICKER]["Open"]
            c = data[SIGNAL_TICKER]["Close"]
        else:
            o, c = data["Open"], data["Close"]
        rows = data.loc[data.index <= date].tail(1)
        if rows.empty:
            return None
        idx = rows.index[-1]
        open_p = float(o.loc[idx])
        close_p = float(c.loc[idx])
        if open_p <= 0:
            return None
        return (close_p - open_p) / open_p * 100
    except Exception:
        return None


def _get_prior_day_return(data: pd.DataFrame, date: pd.Timestamp) -> Optional[float]:
    """SPY return yesterday: (close_D-1 - close_D-2) / close_D-2. For morning scan."""
    try:
        if isinstance(data.columns, pd.MultiIndex):
            close = data[SIGNAL_TICKER]["Close"]
        else:
            close = data["Close"]
        rows = close.loc[close.index <= date].tail(3)
        if len(rows) < 2:
            return None
        c0 = float(rows.iloc[-2])  # D-1 close
        c1 = float(rows.iloc[-1])  # D close (we want D-1 vs D-2, so we need 3 rows)
        if len(rows) < 3:
            return None
        c_prev = float(rows.iloc[-3])  # D-2 close
        if c_prev <= 0:
            return None
        return (c0 - c_prev) / c_prev * 100
    except Exception:
        return None


def _get_spy_return(data: pd.DataFrame, date: pd.Timestamp, lookback: int) -> Optional[float]:
    """SPY return over prior lookback days. Returns pct or None."""
    rows = data.loc[data.index <= date].tail(lookback + 5)
    if len(rows) < lookback + 1:
        return None
    try:
        if isinstance(data.columns, pd.MultiIndex):
            close = data[SIGNAL_TICKER]["Close"]
        else:
            close = data["Close"]
        close = close.loc[close.index <= date].tail(lookback + 5)
        if len(close) < lookback + 1:
            return None
        start = float(close.iloc[-lookback - 1])
        end = float(close.iloc[-1])
        if start <= 0:
            return None
        return (end - start) / start * 100
    except Exception:
        return None


def run_backtest(data: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp,
                 cycle_days: int, lookback: int = 5, strategy: str = "signal") -> Dict:
    """
    strategy: "signal" (use SPY direction), "bull" (always UPRO), "bear" (always SPXU)
    """
    dates = sorted([d for d in data.index if start_date <= d <= end_date])
    if not dates:
        return {"error": "No dates"}
    dates = [pd.Timestamp(d) for d in dates]

    equity = 10000.0
    cycles = []
    current_pos = None  # (ticker, entry_price)
    entry_date = None

    i = 0
    while i < len(dates):
        day = dates[i]
        if current_pos is not None and entry_date and (day - entry_date).days >= cycle_days:
            ticker, entry_price = current_pos
            price = _get_close(data, ticker, day)
            if price and entry_price and entry_price > 0:
                pct = (price - entry_price) / entry_price * 100
                equity *= (1 + pct / 100)
                cycles.append({
                    "ticker": ticker,
                    "entry": entry_date.strftime("%Y-%m-%d"),
                    "exit": day.strftime("%Y-%m-%d"),
                    "return_pct": round(pct, 2),
                    "equity": round(equity, 2),
                })
            current_pos = None

        if current_pos is None:
            if strategy == "signal":
                ret = _get_spy_return(data, day, lookback)
                if ret is None:
                    i += 1
                    continue
                ticker = BULL_TICKER if ret >= 0 else BEAR_TICKER
            elif strategy == "bull":
                ticker = BULL_TICKER
            else:
                ticker = BEAR_TICKER

            price = _get_close(data, ticker, day)
            if price and price > 0:
                current_pos = (ticker, price)
                entry_date = day
        i += 1

    if not cycles:
        return {"cycles": 0, "total_return_pct": 0, "final_equity": 10000, "max_drawdown_pct": 0}

    total_return = (equity - 10000) / 10000 * 100
    equity_curve = [10000.0] + [c["equity"] for c in cycles]
    peak = equity_curve[0]
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100 if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd

    return {
        "cycles": len(cycles),
        "total_return_pct": round(total_return, 2),
        "final_equity": round(equity, 2),
        "cycle_return_avg": round(sum(c["return_pct"] for c in cycles) / len(cycles), 2),
        "max_drawdown_pct": round(max_dd, 2),
        "wins": sum(1 for c in cycles if c["return_pct"] > 0),
        "cycle_list": cycles,
    }


def _get_open(data: pd.DataFrame, ticker: str, date: pd.Timestamp) -> Optional[float]:
    try:
        if isinstance(data.columns, pd.MultiIndex):
            if ticker not in data.columns.get_level_values(0):
                return None
            o = data[ticker]["Open"]
        else:
            o = data["Open"]
        rows = o.loc[o.index <= date].tail(1)
        return float(rows.iloc[-1]) if not rows.empty else None
    except Exception:
        return None


def _get_low(data: pd.DataFrame, ticker: str, date: pd.Timestamp) -> Optional[float]:
    try:
        if isinstance(data.columns, pd.MultiIndex):
            if ticker not in data.columns.get_level_values(0):
                return None
            low = data[ticker]["Low"]
        else:
            low = data["Low"]
        rows = low.loc[low.index <= date].tail(1)
        return float(rows.iloc[-1]) if not rows.empty else None
    except Exception:
        return None


def run_backtest_daily(data: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp,
                       signal_mode: str = "same_day", strategy: str = "signal",
                       stop_pct: Optional[float] = None) -> Dict:
    """
    PDT-safe: 1-day hold. Buy afternoon (or morning), hold overnight, sell next afternoon.
    signal_mode: "same_day" = today's return (close vs open), scan afternoon, buy before close.
                 "prior_day" = yesterday's return, scan morning, buy at open.
    """
    dates = sorted([d for d in data.index if start_date <= d <= end_date])
    if not dates or len(dates) < 2:
        return {"error": "No dates"}
    dates = [pd.Timestamp(d) for d in dates]

    equity = 10000.0
    cycles = []
    position = None
    stops_hit = 0
    stop_saved = 0.0  # pct points saved when close was worse than stop

    for i in range(len(dates)):
        day = dates[i]
        if position is not None:
            ticker, entry_price, entry_date = position
            close_price = _get_close(data, ticker, day)
            if close_price and entry_price and entry_price > 0:
                exit_price = close_price
                if stop_pct is not None and stop_pct > 0:
                    stop_level = entry_price * (1 - stop_pct / 100)
                    low = _get_low(data, ticker, day)
                    if low is not None and low <= stop_level:
                        exit_price = stop_level
                        stops_hit += 1
                        # vs no-stop: positive = we saved (close was worse than stop)
                        close_pct = (close_price - entry_price) / entry_price * 100
                        stop_pct_real = (stop_level - entry_price) / entry_price * 100
                        stop_saved += (stop_pct_real - close_pct)
                pct = (exit_price - entry_price) / entry_price * 100
                equity *= (1 + pct / 100)
                cycles.append({"ticker": ticker, "entry": entry_date.strftime("%Y-%m-%d"),
                              "exit": day.strftime("%Y-%m-%d"), "return_pct": round(pct, 2), "equity": round(equity, 2)})
            position = None

        if i + 1 >= len(dates):
            continue

        ticker = None
        entry_price = None

        if strategy == "signal":
            if signal_mode == "same_day":
                ret = _get_same_day_return(data, day)
                if ret is None:
                    continue
                ticker = BULL_TICKER if ret >= 0 else BEAR_TICKER
                entry_price = _get_close(data, ticker, day)
            else:
                ret = _get_prior_day_return(data, day)
                if ret is None:
                    continue
                ticker = BULL_TICKER if ret >= 0 else BEAR_TICKER
                entry_price = _get_open(data, ticker, day)
        elif strategy == "bull":
            ticker = BULL_TICKER
            entry_price = _get_close(data, ticker, day) if signal_mode == "same_day" else _get_open(data, ticker, day)
        else:
            ticker = BEAR_TICKER
            entry_price = _get_close(data, ticker, day) if signal_mode == "same_day" else _get_open(data, ticker, day)

        if ticker and entry_price and entry_price > 0:
            position = (ticker, entry_price, day)

    if not cycles:
        return {"cycles": 0, "total_return_pct": 0, "final_equity": 10000, "max_drawdown_pct": 0}

    total_return = (equity - 10000) / 10000 * 100
    equity_curve = [10000.0] + [c["equity"] for c in cycles]
    peak = equity_curve[0]
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100 if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd

    result = {
        "cycles": len(cycles),
        "total_return_pct": round(total_return, 2),
        "final_equity": round(equity, 2),
        "cycle_return_avg": round(sum(c["return_pct"] for c in cycles) / len(cycles), 2),
        "max_drawdown_pct": round(max_dd, 2),
        "wins": sum(1 for c in cycles if c["return_pct"] > 0),
        "cycle_list": cycles,
    }
    if stop_pct:
        result["stops_hit"] = stops_hit
        result["stop_saved_pct"] = round(stop_saved, 1)  # cumulative pct points saved
    return result


def main():
    ap = argparse.ArgumentParser(description="UPRO/SPXU inverse play backtest")
    ap.add_argument("--days", type=int, default=780, help="Trading days to backtest")
    ap.add_argument("--cycle", type=int, default=5, help="Cycle length in days (5-day mode)")
    ap.add_argument("--lookback", type=int, default=5, help="SPY lookback for signal")
    ap.add_argument("--daily", action="store_true", help="1-day hold (PDT-safe) instead of 5-day")
    ap.add_argument("--signal-mode", choices=["same_day", "prior_day"], default="same_day",
                    help="same_day=afternoon scan/buy; prior_day=morning scan/buy")
    ap.add_argument("--stop-pct", type=float, default=None, metavar="PCT",
                    help="Stop loss %% (e.g. 5). Exit at this %% below entry if low is breached. Daily mode only.")
    args = ap.parse_args()

    end = datetime.now()
    cal_days = int(args.days * 365 / 252)
    start = end - timedelta(days=cal_days)
    fetch_start = start - timedelta(days=60)
    start_str = fetch_start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    tickers = [SIGNAL_TICKER, BULL_TICKER, BEAR_TICKER]
    print(f"Fetching {tickers}...")
    data = yf.download(tickers, start=start_str, end=end_str, interval="1d", group_by="ticker",
                      auto_adjust=True, progress=False, threads=True)
    if data is None or data.empty:
        print("No data")
        return 1

    start_ts = pd.Timestamp(start.strftime("%Y-%m-%d"))
    end_ts = pd.Timestamp(end_str)

    if args.daily:
        print("\n" + "=" * 70)
        stop_str = f" | stop={args.stop_pct}%" if args.stop_pct else ""
        print(f"UPRO/SPXU DAILY (1-day hold) | signal-mode={args.signal_mode}{stop_str}")
        print("=" * 70)
        print(f"Period: ~{args.days} trading days | PDT-safe\n")

        for label, strat in [
            ("Signal-based (SPY dir -> UPRO/SPXU)", "signal"),
            ("Always UPRO (bull)", "bull"),
            ("Always SPXU (bear)", "bear"),
        ]:
            r = run_backtest_daily(data, start_ts, end_ts, signal_mode=args.signal_mode, strategy=strat,
                                   stop_pct=args.stop_pct)
            if r.get("error"):
                print(f"  {label}: Error")
                continue
            wr = r["wins"] / r["cycles"] * 100 if r["cycles"] else 0
            stop_info = f" | stops: {r.get('stops_hit', 0)} (saved {r.get('stop_saved_pct', 0)}pp)" if args.stop_pct else ""
            print(f"  {label:40} | {r['cycles']:3} cy | {r['total_return_pct']:+7.1f}% | ${r['final_equity']:,.0f} | {wr:.1f}% win | DD {r['max_drawdown_pct']:.1f}%{stop_info}")

        print("\n  -- Run with --signal-mode prior_day for morning-scan results --")
        return 0

    print("\n" + "=" * 70)
    print("UPRO/SPXU INVERSE PLAY | 5-day cycle | SPY momentum signal")
    print("=" * 70)
    print(f"Period: ~{args.days} trading days | Lookback: {args.lookback}d for signal\n")

    results = []
    for label, strat in [
        ("Signal-based (SPY up->UPRO, down->SPXU)", "signal"),
        ("Always UPRO (bull)", "bull"),
        ("Always SPXU (bear)", "bear"),
    ]:
        r = run_backtest(data, start_ts, end_ts, args.cycle, lookback=args.lookback, strategy=strat)
        if r.get("error"):
            print(f"  {label}: Error")
            continue
        wr = r["wins"] / r["cycles"] * 100 if r["cycles"] else 0
        stop_info = f" | stops: {r.get('stops_hit', 0)} (saved {r.get('stop_saved_pct', 0)}pp)" if args.stop_pct else ""
        print(f"  {label:40} | {r['cycles']:3} cy | {r['total_return_pct']:+7.1f}% | ${r['final_equity']:,.0f} | {wr:.1f}% win | DD {r['max_drawdown_pct']:.1f}%{stop_info}")
        results.append((label, r))

    print("\n--- Last 10 cycles (signal strategy) ---")
    r_sig = next((r for _, r in results if "Signal" in str(r)), None)
    if r_sig and r_sig.get("cycle_list"):
        for c in r_sig["cycle_list"][-10:]:
            print(f"  {c['ticker']}: {c['entry']} -> {c['exit']} | {c['return_pct']:+.2f}% | eq ${c['equity']:,.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
