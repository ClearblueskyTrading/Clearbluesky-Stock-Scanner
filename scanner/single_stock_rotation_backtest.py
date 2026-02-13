# ============================================================
# Single-Stock & Sector Leveraged Rotation Backtest
# ============================================================
# Weekly: pick (underlying) with best prior 5-day return.
# Daily: trade that leveraged ETF (buy close, sell next close, 5% stop).
# Run: python single_stock_rotation_backtest.py [--days 780] [--stop-pct 5]

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

# (name, signal_ticker for prior-week return, leveraged ETF to trade)
# Deduped: one per underlying, prefer longer-history issuer
UNIVERSE: List[Tuple[str, str, str]] = [
    # Direxion single-stock
    ("NVDA", "NVDA", "NVDU"),
    ("MU", "MU", "MUU"),
    ("AMD", "AMD", "AMUU"),
    ("TSM", "TSM", "TSMX"),
    ("AVGO", "AVGO", "AVL"),
    ("MSFT", "MSFT", "MSFU"),
    ("AAPL", "AAPL", "AAPU"),
    ("AMZN", "AMZN", "AMZU"),
    ("GOOGL", "GOOGL", "GGLL"),
    ("META", "META", "METU"),
    ("TSLA", "TSLA", "TSLL"),
    ("NFLX", "NFLX", "NFXL"),
    ("PLTR", "PLTR", "PLTU"),
    ("PANW", "PANW", "PALU"),
    ("QCOM", "QCOM", "QCMU"),
    ("SHOP", "SHOP", "SHPU"),
    ("ASML", "ASML", "ASMU"),
    ("MRVL", "MRVL", "MRVU"),
    ("CSCO", "CSCO", "CSCL"),
    ("INTC", "INTC", "LINT"),
    ("ORCL", "ORCL", "ORCU"),
    ("COIN", "COIN", "CONX"),
    # Sector
    ("Tech", "XLK", "TECL"),
    ("Energy", "XLE", "ERX"),
    ("XOM", "XOM", "XOMX"),
    # ProShares where no Direxion
    ("CRCL", "CRCL", "CRCA"),
    # Tradr (shorter history)
    ("LRCX", "LRCX", "LRCU"),
    ("WDC", "WDC", "WDCX"),
]

# Simplified: broad leveraged ETFs only (SOXL=semis, TECL=tech, ERX=energy, TQQQ=nasdaq)
UNIVERSE_SIMPLIFIED: List[Tuple[str, str, str]] = [
    ("Semis", "SOXX", "SOXL"),
    ("Tech", "XLK", "TECL"),
    ("Energy", "XLE", "ERX"),
    ("Nasdaq", "QQQ", "TQQQ"),
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


def _lev_has_history(data: pd.DataFrame, lev: str, date: pd.Timestamp, min_days: int = 5) -> bool:
    """Require leveraged ETF to have min_days of valid data before ranking date."""
    try:
        if isinstance(data.columns, pd.MultiIndex):
            if lev not in data.columns.get_level_values(0):
                return False
            close = data[lev]["Close"]
        else:
            close = data["Close"]
        rows = close.loc[close.index <= date].dropna()
        return len(rows) >= min_days
    except Exception:
        return False


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
        end_price = float(rows.iloc[-1])
        start_price = float(rows.iloc[-6])
        if start_price <= 0:
            return None
        return (end_price - start_price) / start_price * 100
    except Exception:
        return None


def _prior_month_return(data: pd.DataFrame, signal_ticker: str, date: pd.Timestamp, days: int = 21) -> Optional[float]:
    """Prior N trading-day return (~1 month)."""
    try:
        if isinstance(data.columns, pd.MultiIndex):
            if signal_ticker not in data.columns.get_level_values(0):
                return None
            close = data[signal_ticker]["Close"]
        else:
            close = data["Close"]
        rows = close.loc[close.index <= date].tail(days + 5)
        if len(rows) < days + 1:
            return None
        end_price = float(rows.iloc[-1])
        start_price = float(rows.iloc[-days - 1])
        if start_price <= 0:
            return None
        return (end_price - start_price) / start_price * 100
    except Exception:
        return None


def _pick_top_n(data: pd.DataFrame, use_universe: list, day: pd.Timestamp, n: int,
                monthly: bool) -> List[Tuple[str, str, float, float]]:
    """Return top N (name, lev, ret, weight). Weights: 40/35/25 for n=3, 50/50 for n=2, 100 for n=1."""
    candidates = []
    for name, sig, lev in use_universe:
        if not _lev_has_history(data, lev, day, min_days=22 if monthly else 5):
            continue
        ret = _prior_month_return(data, sig, day) if monthly else _prior_week_return(data, sig, day)
        if ret is not None:
            entry_price = _get_close(data, lev, day)
            if entry_price and entry_price > 0:
                candidates.append((name, lev, ret))
    candidates.sort(key=lambda x: -x[2])
    if not candidates:
        return []
    # Weights: n=1 -> 100; n=2 -> 60/40; n=3 -> 40/35/25
    if n == 1:
        weights = [100.0]
    elif n == 2:
        weights = [60.0, 40.0]
    else:
        weights = [40.0, 35.0, 25.0][:n]
    return [(c[0], c[1], c[2], weights[i]) for i, c in enumerate(candidates[:n])]


def run_backtest(data: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp,
                 stop_pct: Optional[float] = None,
                 universe: Optional[List[Tuple[str, str, str]]] = None,
                 principal: float = 20000.0,
                 flat_friday: bool = False,
                 monthly: bool = False,
                 top_n: int = 1) -> Dict:
    use_universe = universe or UNIVERSE
    dates = sorted([d for d in data.index if start_date <= d <= end_date])
    dates = [pd.Timestamp(d) for d in dates]
    if len(dates) < 7:
        return {"error": "Need more data"}

    equity = float(principal)
    cycles = []
    positions = []  # list of (ticker, entry_price, entry_date, weight_pct)
    stops_hit = 0
    stop_saved = 0.0
    current_picks: List[Tuple[str, str, float, float]] = []  # (name, lev, ret, weight)
    last_period = None  # (year, week) or (year, month) for rollover
    wins_by_name: Dict[str, int] = {}

    for i in range(len(dates)):
        day = dates[i]

        # Exit all positions
        if positions:
            day_return = 0.0
            for ticker, entry_price, entry_date, weight_pct in positions:
                close_price = _get_close(data, ticker, day)
                if close_price and entry_price and entry_price > 0:
                    exit_price = close_price
                    if stop_pct and stop_pct > 0:
                        stop_level = entry_price * (1 - stop_pct / 100)
                        low = _get_low(data, ticker, day)
                        if low is not None and low <= stop_level:
                            exit_price = stop_level
                            stops_hit += 1
                            stop_saved += max(0, (stop_level - close_price) / entry_price * 100)
                    pct = (exit_price - entry_price) / entry_price * 100
                    day_return += (weight_pct / 100) * (pct / 100)
            equity *= (1 + day_return)
            cycles.append({"entry": positions[0][2].strftime("%Y-%m-%d"), "exit": day.strftime("%Y-%m-%d"),
                          "return_pct": round(day_return * 100, 2), "equity": round(equity, 2),
                          "tickers": [p[0] for p in positions]})
            positions = []

        period_key = (day.year, day.month) if monthly else (day.year, day.isocalendar()[1])
        if last_period != period_key:
            last_period = period_key
            current_picks = _pick_top_n(data, use_universe, day, top_n, monthly)
            for name, lev, _, _ in current_picks:
                label = f"{name} ({lev})"
                wins_by_name[label] = wins_by_name.get(label, 0) + 1

        if i + 1 >= len(dates) or not current_picks:
            continue

        if flat_friday and day.weekday() == 4:
            continue

        for name, lev, _, weight in current_picks:
            entry_price = _get_close(data, lev, day)
            if entry_price and entry_price > 0:
                positions.append((lev, entry_price, day, weight))

    if not cycles:
        return {"cycles": 0, "total_return_pct": 0, "final_equity": principal, "max_drawdown_pct": 0,
                "wins_by_name": wins_by_name, "principal": principal}

    total_return = (equity - principal) / principal * 100
    equity_curve = [float(principal)] + [c["equity"] for c in cycles]
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
        "principal": principal,
        "cycle_return_avg": round(sum(c["return_pct"] for c in cycles) / len(cycles), 2),
        "max_drawdown_pct": round(max_dd, 2),
        "wins": sum(1 for c in cycles if c["return_pct"] > 0),
        "cycle_list": cycles,
        "wins_by_name": wins_by_name,
    }
    if stop_pct:
        result["stops_hit"] = stops_hit
        result["stop_saved_pct"] = round(stop_saved, 1)
    return result


def main():
    ap = argparse.ArgumentParser(description="Single-stock + sector leveraged rotation")
    ap.add_argument("--days", type=int, default=780, help="Trading days")
    ap.add_argument("--stop-pct", type=float, default=5, metavar="PCT", help="Stop loss %%")
    ap.add_argument("--principal", type=float, default=20000, metavar="AMT", help="Starting capital")
    ap.add_argument("--verify", action="store_true", help="Print cycle details and sanity check")
    ap.add_argument("--sectors-only", action="store_true", help="Compare: only TECL+ERX (long history)")
    ap.add_argument("--simplified", action="store_true", help="SOXL+TECL+ERX+TQQQ only (broad ETFs)")
    ap.add_argument("--flat-friday", action="store_true", help="Sell Friday, flat over weekend, re-enter Monday")
    ap.add_argument("--monthly", action="store_true", help="Monthly rotation (prior 21d return, re-pick each month)")
    ap.add_argument("--top-n", type=int, default=1, metavar="N", help="Top N positions (1=100%%, 2=60/40, 3=40/35/25)")
    args = ap.parse_args()

    end = datetime.now()
    cal_days = int(args.days * 365 / 252)
    start = end - timedelta(days=cal_days)
    fetch_start = start - timedelta(days=120)
    start_str = fetch_start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    use_universe = UNIVERSE_SIMPLIFIED if args.simplified else ([("Tech","XLK","TECL"),("Energy","XLE","ERX")] if args.sectors_only else UNIVERSE)
    signal_tickers = list(dict.fromkeys([u[1] for u in use_universe]))
    lev_tickers = list(dict.fromkeys([u[2] for u in use_universe]))
    all_tickers = list(dict.fromkeys(signal_tickers + lev_tickers))

    print(f"Fetching {len(all_tickers)} tickers...")
    data = yf.download(all_tickers, start=start_str, end=end_str, interval="1d",
                       group_by="ticker", auto_adjust=True, progress=False, threads=True)
    if data is None or data.empty:
        print("No data")
        return 1

    start_ts = pd.Timestamp(start.strftime("%Y-%m-%d"))
    end_ts = pd.Timestamp(end_str)

    print("\n" + "=" * 70)
    print("SINGLE-STOCK + SECTOR LEVERAGED ROTATION")
    print("=" * 70)
    print(f"Universe: {len(UNIVERSE)} names (Direxion, ProShares, Tradr)")
    print(f"Period: ~{args.days} days | {start_ts.strftime('%Y-%m')} to {end_ts.strftime('%Y-%m')} | Stop: {args.stop_pct}% | Principal: ${args.principal:,.0f}")
    print()

    universe = None
    if args.sectors_only:
        universe = [("Tech", "XLK", "TECL"), ("Energy", "XLE", "ERX")]
    elif args.simplified:
        universe = UNIVERSE_SIMPLIFIED

    r = run_backtest(data, start_ts, end_ts, stop_pct=args.stop_pct, principal=args.principal, universe=universe, flat_friday=args.flat_friday, monthly=args.monthly, top_n=args.top_n)
    if r.get("error"):
        print(f"Error: {r['error']}")
        return 1

    wr = r["wins"] / r["cycles"] * 100 if r["cycles"] else 0
    stop_info = f" | stops: {r.get('stops_hit', 0)} (saved {r.get('stop_saved_pct', 0)}pp)" if args.stop_pct else ""
    label = "Sectors only (TECL+ERX)" if args.sectors_only else ("Simplified (SOXL+TECL+ERX+TQQQ)" if args.simplified else "Full universe rotation")
    if args.flat_friday:
        label += " [Fri flat, Mon in]"
    if args.monthly:
        label += " [Monthly]"
    if args.top_n > 1:
        label += f" [Top {args.top_n}]"
    print(f"  {label}{stop_info}")
    print(f"    {r['cycles']} cycles | {r['total_return_pct']:+7.1f}% | ${r['final_equity']:,.0f} | {wr:.1f}% win | DD {r['max_drawdown_pct']:.1f}%")

    ranked = sorted(r.get("wins_by_name", {}).items(), key=lambda x: -x[1])[:10]
    print("\n  Top 10 by weeks picked (underlying -> leveraged ETF traded):")
    for label, cnt in ranked:
        print(f"    {label}: {cnt} weeks")

    years = args.days / 252
    total_mult = (r["total_return_pct"] / 100) + 1
    ann_mult = total_mult ** (1 / years) if years > 0 else 1
    monthly_pct = ann_mult ** (1 / 12) - 1
    weekly_pct = ann_mult ** (1 / 52) - 1
    principal = r.get("principal", args.principal)
    monthly_amt = principal * monthly_pct
    weekly_amt = principal * weekly_pct

    print("\n  --- Weekly / Monthly on ${:,.0f} ---".format(principal))
    print(f"  Full rotation | weekly ~${weekly_amt:,.0f} | monthly ~${monthly_amt:,.0f}")

    print("\n  --- SUMMARY (all numbers) ---")
    print(f"  Principal:        ${principal:,.2f}")
    print(f"  Final equity:     ${r['final_equity']:,.2f}")
    print(f"  Total return:     {r['total_return_pct']:+.1f}%")
    print(f"  CAGR (approx):    {(ann_mult - 1) * 100:.1f}%")
    print(f"  Cycles:           {r['cycles']}")
    print(f"  Win rate:         {wr:.1f}%")
    print(f"  Max drawdown:     {r['max_drawdown_pct']:.1f}%")
    print(f"  Stops hit:        {r.get('stops_hit', 0)}")
    print(f"  Stop saved (pp):  {r.get('stop_saved_pct', 0):.1f}")
    print(f"  Period (years):   {years:.2f}")
    print(f"  Weekly (on $20k): ${weekly_amt:,.0f}")
    print(f"  Monthly (on $20k): ${monthly_amt:,.0f}")

    # Risk-adjusted metrics
    cycle_list = r.get("cycle_list", [])
    returns = [c["return_pct"] for c in cycle_list]
    if returns:
        ann_ret = (total_mult ** (1 / years) - 1) * 100 if years > 0 else 0
        vol_pct = pd.Series(returns).std()  # daily vol
        ann_vol = vol_pct * (252 ** 0.5) if vol_pct and vol_pct > 0 else 0
        sharpe = (ann_ret / ann_vol) if ann_vol > 0 else 0
        calmar = ann_ret / r["max_drawdown_pct"] if r["max_drawdown_pct"] > 0 else 0
        ret_per_dd = r["total_return_pct"] / r["max_drawdown_pct"] if r["max_drawdown_pct"] > 0 else 0
        print("\n  --- Risk ---")
        print(f"  Vol (daily): {vol_pct:.2f}% | Ann vol: {ann_vol:.0f}%")
        print(f"  Sharpe: {sharpe:.2f} | Calmar (ann/D D): {calmar:.2f} | Return/D D: {ret_per_dd:.1f}x")

    if args.verify:
        print("\n  --- VERIFICATION ---")
        recomputed = args.principal
        for c in r["cycle_list"]:
            recomputed *= (1 + c["return_pct"] / 100)
        print(f"  Recomputed equity from cycles: ${recomputed:,.2f} (reported ${r['final_equity']:,.2f})")
        diff_pct = abs(recomputed - r["final_equity"]) / r["final_equity"] * 100
        if diff_pct > 0.5:
            print("  WARNING: Mismatch - possible compounding bug!")
        else:
            print(f"  (Recompute uses rounded cycle returns; {diff_pct:.3f}% diff is rounding)")
        returns = [c["return_pct"] for c in r["cycle_list"]]
        geom = 1.0
        for rr in returns:
            geom *= (1 + rr / 100)
        avg_daily = (geom ** (1 / len(returns)) - 1) * 100 if returns else 0
        print(f"  {len(returns)} cycles | avg return: {sum(returns)/len(returns):.2f}% | geom avg daily: {avg_daily:.3f}%")
        print(f"  Min: {min(returns):.1f}% | Max: {max(returns):.1f}% | Std: {pd.Series(returns).std():.2f}%")
        print("  First 5 cycles:")
        for c in r["cycle_list"][:5]:
            tk = c.get("tickers", [c.get("ticker", "")])
            tk_str = ",".join(tk) if isinstance(tk, list) else str(tk)
            print(f"    {c['entry']} -> {c['exit']} [{tk_str}]: {c['return_pct']:+.2f}%  eq=${c['equity']:,.0f}")
        print("  Last 5 cycles:")
        for c in r["cycle_list"][-5:]:
            tk = c.get("tickers", [c.get("ticker", "")])
            tk_str = ",".join(tk) if isinstance(tk, list) else str(tk)
            print(f"    {c['entry']} -> {c['exit']} [{tk_str}]: {c['return_pct']:+.2f}%  eq=${c['equity']:,.0f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
