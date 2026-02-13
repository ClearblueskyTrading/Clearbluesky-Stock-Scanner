# ============================================================
# Day Trading Sector Leveraged - Cash $20K, PDT 3/5
# ============================================================
# Weekly: pick best sector by prior 5-day return. Day trade 1 leveraged ETF (PDT-safe: 1 trade/day).
# Buy at open, sell at close same day (or 5% stop).
# T1 settlement: $20K. PDT: max 3 day trades per rolling 5 biz days.
# Run: python daytrade_leveraged_backtest.py [--days 780] [--stop-pct 5]

import argparse
import sys
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

try:
    import pandas as pd
    import yfinance as yf
except ImportError:
    print("Requires: pip install pandas yfinance")
    sys.exit(1)

# Sector (name, 1x signal ETF, leveraged ETF) - only sectors with leveraged
SECTORS: List[Tuple[str, str, str]] = [
    ("Tech", "XLK", "TECL"),
    ("Energy", "XLE", "ERX"),
    ("Financials", "XLF", "FAS"),
    ("Healthcare", "XLV", "CURE"),
    ("Industrials", "XLI", "DUSL"),
    ("Consumer Disc", "XLY", "RETL"),
    ("Real Estate", "XLRE", "DRN"),
]


def _get_close(data: pd.DataFrame, ticker: str, date: pd.Timestamp) -> Optional[float]:
    try:
        if isinstance(data.columns, pd.MultiIndex):
            if ticker not in data.columns.get_level_values(0):
                return None
            close = data[ticker]["Close"]
        else:
            close = data["Close"]
        rows = close.loc[close.index <= date]
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


def _prior_week_return(data: pd.DataFrame, signal_ticker: str, date: pd.Timestamp) -> Optional[float]:
    """Prior 5 trading-day return."""
    try:
        if isinstance(data.columns, pd.MultiIndex):
            if signal_ticker not in data.columns.get_level_values(0):
                return None
            close = data[signal_ticker]["Close"]
        else:
            close = data["Close"]
        rows = close.loc[close.index <= date].tail(10)
        if len(rows) < 6:
            return None
        end_p = float(rows.iloc[-1])
        start_p = float(rows.iloc[-6])
        if start_p <= 0:
            return None
        return (end_p - start_p) / start_p * 100
    except Exception:
        return None


def _pick_best_sector_weekly(data: pd.DataFrame, day: pd.Timestamp) -> Optional[Tuple[str, str]]:
    """Pick best sector by prior week return. Return (name, leveraged_ticker). 1 pick = 1 day trade."""
    candidates = []
    for name, sig, lev in SECTORS:
        ret = _prior_week_return(data, sig, day)
        if ret is not None:
            open_p = _get_open(data, lev, day)
            if open_p and open_p > 0:
                candidates.append((name, lev, ret))
    if not candidates:
        return None
    candidates.sort(key=lambda x: -x[2])
    return (candidates[0][0], candidates[0][1])


def _count_pdt_day_trades(recent_days: deque) -> int:
    """Count day trades in most recent 5 business days."""
    return sum(1 for d in recent_days if d)  # d=True means we day-traded that day


def run_backtest(
    data: pd.DataFrame,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    position_size: float = 20000.0,
    stop_pct: float = 5.0,
    max_day_trades_per_5d: Optional[int] = 3,
    allow_dow: Optional[List[int]] = None,
) -> Dict:
    """
    Day trade: buy at open, sell at close (or stop).
    Weekly: pick best sector by prior 5d return. Day trade 1 ETF (PDT-safe).
    PDT: max 3 day trades per rolling 5 business days.
    Cash: position_size ($20K) per trade.
    """
    dates = sorted([d for d in data.index if start_date <= d <= end_date])
    dates = [pd.Timestamp(d) for d in dates]
    if len(dates) < 10:
        return {"error": "Need more data"}

    equity = float(position_size)
    trades = []
    recent_day_trade_days: deque = deque(maxlen=5)
    current_week_pick: Optional[Tuple[str, str]] = None
    last_week = None  # (year, week)

    for i in range(len(dates)):
        day = dates[i]
        week_key = (day.year, day.isocalendar()[1])

        if last_week != week_key:
            last_week = week_key
            current_week_pick = _pick_best_sector_weekly(data, day)

        if allow_dow is not None and day.weekday() not in allow_dow:
            recent_day_trade_days.append(False)
            continue

        if max_day_trades_per_5d is not None:
            pdt_count = _count_pdt_day_trades(recent_day_trade_days)
            if pdt_count >= max_day_trades_per_5d:
                recent_day_trade_days.append(False)
                continue

        pick = current_week_pick
        if not pick:
            recent_day_trade_days.append(False)
            continue

        name, lev = pick
        open_p = _get_open(data, lev, day)
        close_p = _get_close(data, lev, day)
        low_p = _get_low(data, lev, day)
        if not open_p or open_p <= 0 or not close_p:
            recent_day_trade_days.append(False)
            continue

        stop_level = open_p * (1 - stop_pct / 100)
        if low_p is not None and low_p <= stop_level:
            exit_price = stop_level
            exit_reason = "stop"
        else:
            exit_price = close_p
            exit_reason = "close"

        pct = (exit_price - open_p) / open_p * 100
        trade_pnl = position_size * (pct / 100)
        equity += trade_pnl

        trades.append({
            "date": day.strftime("%Y-%m-%d"),
            "dow": day.weekday(),  # Mon=0 .. Fri=4
            "ticker": lev,
            "name": name,
            "open": open_p,
            "exit": exit_price,
            "return_pct": round(pct, 2),
            "pnl": round(trade_pnl, 2),
            "exit_reason": exit_reason,
            "equity": round(equity, 2),
        })
        recent_day_trade_days.append(True)  # 1 day trade

    if not trades:
        return {
            "trades": 0,
            "total_return_pct": 0,
            "final_equity": position_size,
            "win_rate": 0,
            "trade_list": [],
        }

    total_return = (equity - position_size) / position_size * 100
    wins = sum(1 for t in trades if t["return_pct"] > 0)
    return {
        "trades": len(trades),
        "total_return_pct": round(total_return, 2),
        "final_equity": round(equity, 2),
        "principal": position_size,
        "win_rate": round(wins / len(trades) * 100, 1),
        "trade_list": trades,
        "stops": sum(1 for t in trades if t["exit_reason"] == "stop"),
        "avg_return": round(sum(t["return_pct"] for t in trades) / len(trades), 2),
    }


def main():
    ap = argparse.ArgumentParser(
        description="Day trade sector leveraged: $20K, PDT 3/5, weekly best sector -> buy open sell close"
    )
    ap.add_argument("--days", type=int, default=780)
    ap.add_argument("--stop-pct", type=float, default=5.0)
    ap.add_argument("--size", type=float, default=20000.0)
    ap.add_argument("--pdt", type=int, default=3)
    ap.add_argument("--analyze-days", action="store_true",
                    help="Run without PDT, rank weekdays by return, show best 3 days")
    ap.add_argument("--best-days", type=str, default=None,
                    help="Only trade these days: 0-4 (Mon=0,Tue=1,Wed=2,Thu=3,Fri=4) e.g. 0,1,2")
    args = ap.parse_args()

    allow_dow = None
    if args.best_days:
        allow_dow = [int(x.strip()) for x in args.best_days.split(",") if x.strip()]
        allow_dow = [d for d in allow_dow if 0 <= d <= 4]

    end = datetime.now()
    cal_days = int(args.days * 365 / 252)
    start = end - timedelta(days=cal_days)
    fetch_start = start - timedelta(days=60)
    start_str = fetch_start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    start_ts = pd.Timestamp(start.strftime("%Y-%m-%d"))
    end_ts = pd.Timestamp(end_str)

    signal_tickers = [u[1] for u in SECTORS]
    lev_tickers = [u[2] for u in SECTORS]
    all_tickers = list(dict.fromkeys(signal_tickers + lev_tickers))

    print("=" * 70)
    print("DAY TRADING SECTOR LEVERAGED - Cash $20K, PDT 3/5")
    print("=" * 70)
    print(f"Position size: ${args.size:,.0f}  |  Stop: {args.stop_pct}%  |  PDT: {args.pdt} day trades / 5 days")
    print(f"Strategy: Best sector (weekly) -> 1 leveraged ETF, buy open sell close (or stop)")
    print(f"Period: ~{args.days} days")
    print()

    print("Fetching data...")
    data = yf.download(
        all_tickers, start=start_str, end=end_str, interval="1d",
        group_by="ticker", auto_adjust=True, progress=False, threads=True
    )
    if data is None or data.empty:
        print("No data")
        return 1

    if args.analyze_days:
        r = run_backtest(
            data, start_ts, end_ts,
            position_size=args.size,
            stop_pct=args.stop_pct,
            max_day_trades_per_5d=None,
            allow_dow=None,
        )
        if r.get("error"):
            print(r["error"])
            return 1
        trades = r["trade_list"]
        dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        by_dow: Dict[int, List[float]] = {d: [] for d in range(5)}
        for t in trades:
            by_dow[t["dow"]].append(t["return_pct"])
        rows = []
        for d in range(5):
            rets = by_dow[d]
            if not rets:
                rows.append((dow_names[d], 0, 0, 0, 0))
            else:
                avg = sum(rets) / len(rets)
                total = sum(rets)
                wins = sum(1 for x in rets if x > 0)
                wr = wins / len(rets) * 100
                rows.append((dow_names[d], len(rets), avg, total, wr))
        rows.sort(key=lambda x: -x[2])  # by avg return
        print("-" * 70)
        print("BEST DAYS FOR DAY TRADING (by avg return %)")
        print("-" * 70)
        for name, n, avg, total, wr in rows:
            print(f"  {name}:  {n:4} trades  |  avg {avg:+.2f}%  |  sum {total:+.1f}%  |  win {wr:.1f}%")
        best3 = [r[0] for r in rows[:3]]
        print()
        print(f"  -> Best 3 days: {', '.join(best3)}")
        print(f"  -> Run with: --best-days {','.join(str(dow_names.index(d)) for d in best3)}")
        print("=" * 70)
        return 0

    r = run_backtest(
        data, start_ts, end_ts,
        position_size=args.size,
        stop_pct=args.stop_pct,
        max_day_trades_per_5d=args.pdt,
        allow_dow=allow_dow,
    )
    if r.get("error"):
        print(r["error"])
        return 1

    if allow_dow:
        dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        print(f"  Best days only: {', '.join(dow_names[d] for d in allow_dow)}")
        print()

    print("-" * 70)
    print("RESULTS")
    print("-" * 70)
    print(f"  Trades:      {r['trades']}")
    print(f"  Win rate:    {r['win_rate']}%")
    print(f"  Stops hit:   {r.get('stops', 0)}")
    print(f"  Avg ret:     {r.get('avg_return', 0)}% per trade")
    print(f"  Total ret:   {r['total_return_pct']:+.1f}%")
    print(f"  Final:       ${r['final_equity']:,.0f}")
    print()

    years = args.days / 252
    if years > 0:
        total_mult = (r["total_return_pct"] / 100) + 1
        ann_ret = (total_mult ** (1 / years) - 1) * 100
        daily_ret = (r["final_equity"] - args.size) / args.days
        print(f"  CAGR:        {ann_ret:.1f}%")
        print(f"  ~$/day:     ${daily_ret:.0f}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
