# ============================================================
# Sector Rotation Backtest - Cycle length comparison
# ============================================================
# Ranks sectors by momentum, deploys 100% into top sector each cycle.
# Liquidates at end of cycle, redeploys into new hottest sector.
# Run: python sector_rotation_backtest.py [--days 780] [--cycle 5|10|15|20]
#       --sweep to compare all cycle lengths

import argparse
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

try:
    import pandas as pd
    import yfinance as yf
except ImportError:
    print("Requires: pip install pandas yfinance")
    sys.exit(1)

SECTOR_ETFS = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
SECTOR_TO_LEVERAGED = {
    "XLK": "TQQQ", "XLF": "FAS", "XLE": "ERX", "XLV": "CURE",
    "XLI": "DUSL", "XLY": "RETL", "XLP": None, "XLU": None, "XLB": None,
    "XLRE": "DRN", "XLC": None,
}
SECTOR_TO_BEAR = {
    "XLK": "SQQQ", "XLF": "FAZ", "XLE": "ERY", "XLV": "LABD",
    "XLI": None, "XLY": None, "XLP": None, "XLU": None, "XLB": None,
    "XLRE": None, "XLC": None,
}
BEAR_FALLBACK = "SPXU"


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


def _rank_sectors(data: pd.DataFrame, date: pd.Timestamp, lookback: int = 5) -> List[Tuple[str, float]]:
    """Rank sectors by lookback-day return. Returns [(etf, return_pct), ...] best first."""
    results = []
    for etf in SECTOR_ETFS:
        try:
            if isinstance(data.columns, pd.MultiIndex):
                if etf not in data.columns.get_level_values(0):
                    continue
                close = data[etf]["Close"]
            else:
                close = data["Close"]
            rows = close.loc[close.index <= date].tail(lookback + 5)
            if len(rows) < lookback + 1:
                continue
            start = float(rows.iloc[-lookback - 1])
            end = float(rows.iloc[-1])
            if start <= 0:
                continue
            ret = (end - start) / start * 100
            results.append((etf, ret))
        except Exception:
            continue
    results.sort(key=lambda x: -x[1])
    return results


def _ticker_for_sector(etf: str, ret: float, use_leveraged: bool, use_bear: bool) -> str:
    """Resolve sector ETF to deploy ticker (bull or bear)."""
    if use_bear and ret < 0:
        ticker = SECTOR_TO_BEAR.get(etf) or BEAR_FALLBACK
    else:
        ticker = SECTOR_TO_LEVERAGED.get(etf) if use_leveraged else etf
        if ticker is None:
            ticker = etf
    return ticker


def run_backtest(data: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp,
                 cycle_days: int, use_leveraged: bool = True, lookback: int = 5,
                 n_positions: int = 1, use_bear: bool = False) -> Dict:
    """Run sector rotation backtest. n_positions=2 uses 60/40 split. use_bear uses inverse ETFs when sector negative."""
    dates = sorted([d for d in data.index if start_date <= d <= end_date])
    if not dates:
        return {"error": "No dates"}
    dates = [pd.Timestamp(d) for d in dates]

    equity = 10000.0
    cycles = []
    # For 1 pos: current_pos = str. For 2 pos: current_pos = [(ticker, w, entry_price), ...]
    current_pos = None
    entry_date = None

    i = 0
    while i < len(dates):
        day = dates[i]
        # End of cycle: liquidate
        if current_pos is not None and entry_date and (day - entry_date).days >= cycle_days:
            cycle_ret = 0.0
            if n_positions == 1:
                ticker, entry_price = current_pos
                price = _get_close(data, ticker, day)
                if price and entry_price and entry_price > 0:
                    pct = (price - entry_price) / entry_price * 100
                    cycle_ret = pct
                    equity *= (1 + pct / 100)
                cycles.append({"sector": ticker, "entry": entry_date.strftime("%Y-%m-%d"),
                              "exit": day.strftime("%Y-%m-%d"), "return_pct": round(cycle_ret, 2),
                              "equity": round(equity, 2)})
            else:
                total_w = 0
                for ticker, w, entry_price in current_pos:
                    price = _get_close(data, ticker, day)
                    if price and entry_price and entry_price > 0:
                        pct = (price - entry_price) / entry_price * 100
                        total_w += w * (1 + pct / 100)
                    else:
                        total_w += w
                cycle_ret = (total_w - 1.0) * 100
                equity *= total_w
                tickers_str = ",".join(p[0] for p in current_pos)
                cycles.append({"sector": tickers_str, "entry": entry_date.strftime("%Y-%m-%d"),
                              "exit": day.strftime("%Y-%m-%d"), "return_pct": round(cycle_ret, 2),
                              "equity": round(equity, 2)})
            current_pos = None

        # Start new cycle if no position
        if current_pos is None:
            ranked = _rank_sectors(data, day, lookback=lookback)
            if not ranked:
                i += 1
                continue
            if n_positions == 1:
                top_etf, top_ret = ranked[0]
                ticker = _ticker_for_sector(top_etf, top_ret, use_leveraged, use_bear)
                price = _get_close(data, ticker, day)
                if price and price > 0:
                    current_pos = (ticker, price)
                    entry_date = day
            else:
                weights = [0.6, 0.4]
                entries = []
                for j, (etf, ret) in enumerate(ranked[:2]):
                    ticker = _ticker_for_sector(etf, ret, use_leveraged, use_bear)
                    price = _get_close(data, ticker, day)
                    if price and price > 0:
                        entries.append((ticker, weights[j], price))
                if entries:
                    current_pos = entries
                    entry_date = day
        i += 1

    if not cycles:
        return {"cycles": 0, "total_return_pct": 0, "final_equity": 10000, "cycle_return_avg": 0}

    total_return = (equity - 10000) / 10000 * 100
    avg_cycle = sum(c["return_pct"] for c in cycles) / len(cycles)

    return {
        "cycles": len(cycles),
        "total_return_pct": round(total_return, 2),
        "final_equity": round(equity, 2),
        "cycle_return_avg": round(avg_cycle, 2),
        "wins": sum(1 for c in cycles if c["return_pct"] > 0),
        "cycle_list": cycles,
    }


def main():
    ap = argparse.ArgumentParser(description="Sector rotation backtest - compare cycle lengths")
    ap.add_argument("--days", type=int, default=780, help="Trading days to backtest (default 780)")
    ap.add_argument("--cycle", type=int, default=None, help="Cycle length in days (5=week, 20=month)")
    ap.add_argument("--sweep", action="store_true", help="Sweep cycles 5,10,15,20 and report best")
    ap.add_argument("--compare", action="store_true", help="Compare 1pos vs 2pos vs 2pos+bear (5d cycle)")
    ap.add_argument("--positions", type=int, default=1, choices=[1, 2], help="Number of positions (2 = 60/40)")
    ap.add_argument("--bear", action="store_true", help="Use bear leveraged ETFs when sector momentum negative")
    ap.add_argument("--conservative", action="store_true", help="Use sector ETFs instead of leveraged")
    args = ap.parse_args()

    end = datetime.now()
    cal_days = int(args.days * 365 / 252)
    start = end - timedelta(days=cal_days)
    fetch_start = start - timedelta(days=60)
    start_str = fetch_start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    bear_tickers = list(set(SECTOR_TO_BEAR.values()) - {None}) + [BEAR_FALLBACK]
    tickers = SECTOR_ETFS + list(set(SECTOR_TO_LEVERAGED.values()) - {None}) + bear_tickers
    tickers = list(dict.fromkeys(t for t in tickers if t))

    print(f"Fetching data for {len(tickers)} tickers...")
    data = yf.download(tickers, start=start_str, end=end_str, interval="1d", group_by="ticker",
                      auto_adjust=True, progress=False, threads=True)
    if data is None or data.empty:
        print("No data")
        return 1

    start_ts = pd.Timestamp(start.strftime("%Y-%m-%d"))
    end_ts = pd.Timestamp(end_str)

    if args.compare:
        print("\n" + "=" * 65)
        print("SECTOR ROTATION - 1pos vs 2pos vs 2pos+bear | 5-day cycle | 780 days")
        print("=" * 65)
        cycle = 5
        for label, n_pos, use_bear in [
            ("1 position (100% top)", 1, False),
            ("2 positions (60/40)", 2, False),
            ("2 positions + bear ETFs", 2, True),
        ]:
            r = run_backtest(data, start_ts, end_ts, cycle,
                            use_leveraged=not args.conservative,
                            n_positions=n_pos, use_bear=use_bear)
            if r.get("error"):
                print(f"  {label}: Error")
                continue
            wr = r["wins"] / r["cycles"] * 100 if r["cycles"] else 0
            print(f"  {label:30} | {r['cycles']:3} cycles | {r['total_return_pct']:+7.1f}% cum | ${r['final_equity']:,.0f} | {wr:.1f}% win")
        return 0

    if args.sweep:
        print("\n" + "=" * 60)
        print("SECTOR ROTATION - CYCLE LENGTH SWEEP (780 trading days)")
        print("=" * 60)
        best = None
        best_ret = -999
        for cycle in [3, 5, 7, 10, 15, 20]:
            r = run_backtest(data, start_ts, end_ts, cycle, use_leveraged=not args.conservative,
                             n_positions=args.positions, use_bear=args.bear)
            if r.get("error"):
                continue
            ret = r["total_return_pct"]
            wr = r["wins"] / r["cycles"] * 100 if r["cycles"] else 0
            print(f"  {cycle:2}d cycle: {r['cycles']:3} cycles | {ret:+6.1f}% cum | {wr:.1f}% win rate")
            if ret > best_ret:
                best_ret = ret
                best = (cycle, r)
        if best:
            c, r = best
            print(f"\n  Best: {c}-day cycle | {r['total_return_pct']:+.1f}% cumulative | {r['cycles']} cycles")
        return 0

    cycle = args.cycle or 20
    r = run_backtest(data, start_ts, end_ts, cycle, use_leveraged=not args.conservative,
                     n_positions=args.positions, use_bear=args.bear)
    if r.get("error"):
        print(f"Error: {r['error']}")
        return 1

    print("\n" + "=" * 60)
    print(f"SECTOR ROTATION BACKTEST | {cycle}-day cycle | pos={args.positions}" + (" bear=on" if args.bear else ""))
    print("=" * 60)
    print(f"Period: ~{args.days} trading days")
    print(f"Cycles: {r['cycles']}")
    print(f"Cumulative return: {r['total_return_pct']}%")
    print(f"Final equity: ${r['final_equity']:,.0f} (from $10,000)")
    print(f"Avg return/cycle: {r['cycle_return_avg']}%")
    print(f"Win rate: {r['wins']}/{r['cycles']} = {r['wins']/r['cycles']*100:.1f}%")
    if r.get("cycle_list"):
        print("\nLast 10 cycles:")
        for c in r["cycle_list"][-10:]:
            print(f"  {c['sector']}: {c['entry']} -> {c['exit']} | {c['return_pct']:+.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
