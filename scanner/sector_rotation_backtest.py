# ============================================================
# Sector Rotation Backtest - Weekly signal, daily execution
# ============================================================
# Each week: pick sector with strongest prior-week return.
# Each day: buy that sector's leveraged ETF at close, sell next close (PDT-safe).
# Run: python sector_rotation_backtest.py [--days 780] [--stop-pct 5]

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

# Sector: (name, signal ETF 1x, leveraged ETF 2x/3x)
SECTORS: List[Tuple[str, str, str]] = [
    ("Tech", "XLK", "TECL"),       # XLK = signal, TECL = 3x tech
    ("Energy", "XLE", "ERX"),      # XLE -> ERX 2x
    ("Financials", "XLF", "UYG"),  # XLF -> UYG 2x
    ("Healthcare", "XLV", "RXL"),  # XLV -> RXL 2x
]

# Alternative: Energy, Consumer Staples, Industrials (current 30d top 3)
SECTORS_ENERGY_STAPLES_INDUSTRIAL: List[Tuple[str, str, str]] = [
    ("Energy", "XLE", "ERX"),
    ("Consumer Staples", "XLP", "UGE"),
    ("Industrials", "XLI", "UXI"),
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
        if rows.empty:
            return None
        return float(rows.iloc[-1])
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


def _prior_week_return(data: pd.DataFrame, signal_ticker: str, date: pd.Timestamp) -> Optional[float]:
    """Return for the calendar week ending before date (Fri to prior Fri)."""
    try:
        if isinstance(data.columns, pd.MultiIndex):
            close = data[signal_ticker]["Close"]
        else:
            close = data["Close"]
        rows = close.loc[close.index <= date].tail(10)
        if len(rows) < 6:
            return None
        # Need two Fridays (or last 2 weeks of closes)
        # Simpler: prior 5 trading days return (approx 1 week)
        end_price = float(rows.iloc[-1])
        start_price = float(rows.iloc[-6])
        if start_price <= 0:
            return None
        return (end_price - start_price) / start_price * 100
    except Exception:
        return None


def _lev_to_name(lev: str, sectors: Optional[List[Tuple[str, str, str]]] = None) -> str:
    pool = sectors or SECTORS
    for name, _, l in pool:
        if l == lev:
            return name
    return lev


def run_backtest(data: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp,
                 stop_pct: Optional[float] = None, sectors: Optional[List[Tuple[str, str, str]]] = None) -> Dict:
    """
    Weekly sector pick, daily execution. PDT-safe.
    sectors: subset to use (default: all SECTORS)
    """
    use_sectors = sectors if sectors is not None else SECTORS
    dates = sorted([d for d in data.index if start_date <= d <= end_date])
    dates = [pd.Timestamp(d) for d in dates]
    if len(dates) < 7:
        return {"error": "Need more data"}

    equity = 10000.0
    cycles = []
    position = None
    stops_hit = 0
    stop_saved = 0.0
    current_sector_ticker = None
    last_week_start = None
    sector_weekly_wins: Dict[str, int] = {}  # sector name -> weeks picked

    for i in range(len(dates)):
        day = dates[i]

        # Exit position from yesterday
        if position is not None:
            ticker, entry_price, entry_date = position
            close_price = _get_close(data, ticker, day)
            if close_price and entry_price and entry_price > 0:
                exit_price = close_price
                if stop_pct and stop_pct > 0:
                    stop_level = entry_price * (1 - stop_pct / 100)
                    low = _get_low(data, ticker, day)
                    if low is not None and low <= stop_level:
                        exit_price = stop_level
                        stops_hit += 1
                        close_pct = (close_price - entry_price) / entry_price * 100
                        stop_pct_real = (stop_level - entry_price) / entry_price * 100
                        stop_saved += (stop_pct_real - close_pct)
                pct = (exit_price - entry_price) / entry_price * 100
                equity *= (1 + pct / 100)
                cycles.append({
                    "ticker": ticker,
                    "entry": entry_date.strftime("%Y-%m-%d"),
                    "exit": day.strftime("%Y-%m-%d"),
                    "return_pct": round(pct, 2),
                    "equity": round(equity, 2),
                })
            position = None

        # Re-scan sector at start of each week (Mon, or first trading day)
        week_num = day.isocalendar()[1]
        if last_week_start != week_num:
            last_week_start = week_num
            best_ret = None
            best_lev = None
            for name, sig, lev in use_sectors:
                ret = _prior_week_return(data, sig, day)
                if ret is not None and (best_ret is None or ret > best_ret):
                    best_ret = ret
                    best_lev = lev
            current_sector_ticker = best_lev
            if best_lev:
                name = _lev_to_name(best_lev, use_sectors)
                sector_weekly_wins[name] = sector_weekly_wins.get(name, 0) + 1

        if i + 1 >= len(dates) or not current_sector_ticker:
            continue

        entry_price = _get_close(data, current_sector_ticker, day)
        if entry_price and entry_price > 0:
            position = (current_sector_ticker, entry_price, day)

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
        "sector_weekly_wins": sector_weekly_wins,
    }
    if stop_pct:
        result["stops_hit"] = stops_hit
        result["stop_saved_pct"] = round(stop_saved, 1)
    return result


def buy_and_hold_backtest(data: pd.DataFrame, ticker: str, start_date: pd.Timestamp,
                          end_date: pd.Timestamp) -> Dict:
    """Simple buy at start, hold to end."""
    try:
        if isinstance(data.columns, pd.MultiIndex):
            if ticker not in data.columns.get_level_values(0):
                return {"error": f"No data for {ticker}"}
            close = data[ticker]["Close"]
        else:
            close = data["Close"]
        rows = close.loc[(close.index >= start_date) & (close.index <= end_date)]
        if len(rows) < 2:
            return {"error": f"Insufficient data for {ticker}"}
        start_price = float(rows.iloc[0])
        end_price = float(rows.iloc[-1])
        if start_price <= 0:
            return {"error": f"Invalid start price for {ticker}"}
        total_return = (end_price - start_price) / start_price * 100
        equity_curve = [float(p) for p in rows]
        peak = equity_curve[0]
        max_dd = 0.0
        for eq in equity_curve:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100 if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
        return {
            "total_return_pct": round(total_return, 2),
            "final_equity": round(10000 * (1 + total_return / 100), 2),
            "max_drawdown_pct": round(max_dd, 2),
        }
    except Exception as e:
        return {"error": str(e)}


def main():
    ap = argparse.ArgumentParser(description="Sector rotation: weekly signal, daily execution")
    ap.add_argument("--days", type=int, default=780, help="Trading days to backtest")
    ap.add_argument("--stop-pct", type=float, default=None, metavar="PCT", help="Stop loss %% (e.g. 5)")
    ap.add_argument("--top-sectors", type=int, default=None, metavar="N",
                    help="Use only top N sectors by weekly-win count")
    ap.add_argument("--compare-tops", action="store_true",
                    help="Compare full vs top-3 vs top-2 sectors")
    ap.add_argument("--preset", choices=["default", "energy_staples_industrial"], default="default",
                    help="Sector universe: default (Tech/Energy/Fin/Health) or energy_staples_industrial")
    args = ap.parse_args()

    end = datetime.now()
    cal_days = int(args.days * 365 / 252)
    start = end - timedelta(days=cal_days)
    fetch_start = start - timedelta(days=90)
    start_str = fetch_start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    sectors_list = SECTORS_ENERGY_STAPLES_INDUSTRIAL if args.preset == "energy_staples_industrial" else SECTORS
    signal_tickers = [s[1] for s in sectors_list]
    lev_tickers = [s[2] for s in sectors_list]
    compare_tickers = ["GDX", "FCX"]
    # Add tickers for single-ticker comparison (TECL, ERX, MUU)
    extra = ["XLK", "XLE", "TECL", "ERX", "MU", "MUU"]  # MUU = 2x Micron (since Oct 2024)
    all_tickers = list(dict.fromkeys(signal_tickers + lev_tickers + compare_tickers + extra))

    print(f"Fetching {all_tickers}...")
    data = yf.download(all_tickers, start=start_str, end=end_str, interval="1d",
                       group_by="ticker", auto_adjust=True, progress=False, threads=True)
    if data is None or data.empty:
        print("No data")
        return 1

    start_ts = pd.Timestamp(start.strftime("%Y-%m-%d"))
    end_ts = pd.Timestamp(end_str)

    preset_label = " [Energy, Consumer Staples, Industrials]" if args.preset == "energy_staples_industrial" else ""
    print("\n" + "=" * 70)
    print(f"SECTOR ROTATION | Weekly signal (prior 5d return) + daily execution{preset_label}")
    print("=" * 70)
    print(f"Sectors: {', '.join(s[0] for s in sectors_list)}")
    print(f"Period: ~{args.days} trading days | {start_ts.strftime('%Y-%m')} to {end_ts.strftime('%Y-%m')}")
    if args.stop_pct:
        print(f"Stop: {args.stop_pct}%")
    print()

    # First run: get sector win counts
    r_full = run_backtest(data, start_ts, end_ts, stop_pct=args.stop_pct, sectors=sectors_list)
    wins = r_full.get("sector_weekly_wins", {})
    ranked = sorted(wins.items(), key=lambda x: -x[1])

    print("  Sector wins (weeks picked):")
    for name, count in ranked:
        pct = count / sum(wins.values()) * 100 if wins else 0
        print(f"    {name}: {count} weeks ({pct:.0f}%)")
    print()

    if args.compare_tops:
        # Run all: full, top-3, top-2
        results = [(f"All {len(sectors_list)} sectors", None)]
        for n in [3, 2]:
            top_names = [x[0] for x in ranked[:n]]
            sectors_n = [s for s in sectors_list if s[0] in top_names]
            results.append((f"Top {n} ({', '.join(top_names)})", sectors_n))

        print("  --- Comparison ---")
        for label, secs in results:
            rr = run_backtest(data, start_ts, end_ts, stop_pct=args.stop_pct, sectors=secs)
            if rr.get("error"):
                print(f"  {label}: Error")
                continue
            wr = rr["wins"] / rr["cycles"] * 100 if rr["cycles"] else 0
            stop_info = f" | stops:{rr.get('stops_hit', 0)}" if args.stop_pct else ""
            print(f"  {label:30} | {rr['total_return_pct']:+7.1f}% | ${rr['final_equity']:,.0f} | {wr:.1f}% win | DD {rr['max_drawdown_pct']:.1f}%{stop_info}")
        r = r_full
    elif args.top_sectors is not None:
        top_names = [x[0] for x in ranked[: args.top_sectors]]
        sectors_to_use = [s for s in sectors_list if s[0] in top_names]
        print(f"  Using only top {args.top_sectors}: {', '.join(top_names)}\n")
        r = run_backtest(data, start_ts, end_ts, stop_pct=args.stop_pct, sectors=sectors_to_use)
    else:
        r = r_full

    if r.get("error"):
        print(f"Error: {r['error']}")
        return 1

    sector_label = ""
    if args.top_sectors and not args.compare_tops:
        sector_label = f" [top {args.top_sectors}]"
    wr = r["wins"] / r["cycles"] * 100 if r["cycles"] else 0
    stop_info = f" | stops: {r.get('stops_hit', 0)} (saved {r.get('stop_saved_pct', 0)}pp)" if args.stop_pct else ""
    print(f"\n  Sector rotation{sector_label}{stop_info}")
    print(f"    {r['cycles']} cycles | {r['total_return_pct']:+7.1f}% | ${r['final_equity']:,.0f} | {wr:.1f}% win | DD {r['max_drawdown_pct']:.1f}%")

    # Single-ticker: always TECL, always ERX, always MUU (same daily + stop)
    single_tickers = [("Tech", "XLK", "TECL"), ("Energy", "XLE", "ERX"), ("Micron 2x", "MU", "MUU")]
    print("\n  --- Single-ticker (daily + 5% stop) vs Rotation ---")
    for name, sig, lev in single_tickers:
        r_s = run_backtest(data, start_ts, end_ts, stop_pct=args.stop_pct, sectors=[(name, sig, lev)])
        if not r_s.get("error") and r_s.get("cycles"):
            wr_s = r_s["wins"] / r_s["cycles"] * 100
            note = " (since Oct 2024)" if lev == "MUU" else ""
            print(f"  Always {lev:6} | {r_s['total_return_pct']:+7.1f}% | ${r_s['final_equity']:,.0f} | {wr_s:.1f}% win | DD {r_s['max_drawdown_pct']:.1f}%{note}")

    print("\n  --- Buy & Hold Comparison (same period, $10k start) ---")
    for ticker in compare_tickers:
        bh = buy_and_hold_backtest(data, ticker, start_ts, end_ts)
        if bh.get("error"):
            print(f"  {ticker:10} | Error: {bh['error']}")
        else:
            print(f"  {ticker:10} | {bh['total_return_pct']:+7.1f}% | ${bh['final_equity']:,.0f} | DD {bh['max_drawdown_pct']:.1f}%")

    years = args.days / 252
    print("\n  --- Weekly / Monthly on $20k (annualized from backtest) ---")
    r_top2 = run_backtest(data, start_ts, end_ts, stop_pct=args.stop_pct,
                          sectors=[s for s in sectors_list if s[0] in [x[0] for x in ranked[:2]]])
    r_top3 = run_backtest(data, start_ts, end_ts, stop_pct=args.stop_pct,
                          sectors=[s for s in sectors_list if s[0] in [x[0] for x in ranked[:3]]])
    top2_names = ", ".join(x[0] for x in ranked[:2])
    top3_names = ", ".join(x[0] for x in ranked[:3])
    strategies = [
        (f"Top 2 ({top2_names})", r_top2["total_return_pct"], r_top2["final_equity"]),
        (f"Top 3 ({top3_names})", r_top3["total_return_pct"], r_top3["final_equity"]),
        (f"All {len(sectors_list)} sectors", r_full["total_return_pct"], r_full["final_equity"]),
    ]
    for name, sig, lev in single_tickers:
        r_s = run_backtest(data, start_ts, end_ts, stop_pct=args.stop_pct, sectors=[(name, sig, lev)])
        if not r_s.get("error") and r_s.get("cycles"):
            strategies.append((f"Always {lev}", r_s["total_return_pct"], r_s["final_equity"]))
    for ticker in compare_tickers:
        bh = buy_and_hold_backtest(data, ticker, start_ts, end_ts)
        if not bh.get("error"):
            strategies.append((ticker, bh["total_return_pct"], bh["final_equity"]))

    for name, ret_pct, final in strategies:
        total_mult = (ret_pct / 100) + 1
        ann_mult = total_mult ** (1 / years) if years > 0 else 1
        monthly_pct = ann_mult ** (1 / 12) - 1
        weekly_pct = ann_mult ** (1 / 52) - 1
        monthly_20k = 20000 * monthly_pct
        weekly_20k = 20000 * weekly_pct
        print(f"  {name:20} | weekly ~${weekly_20k:,.0f} | monthly ~${monthly_20k:,.0f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
