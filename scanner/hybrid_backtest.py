# ============================================================
# Hybrid Backtest: 60% Swing Dip + 30% Sector Rotation + 10% Cash
# ============================================================
# Runs both strategies over same period, combines with allocation.
# Run: python hybrid_backtest.py [--days 780]
#
# Allocation: $20K total
#   - 60% ($12K): Emotional Dip / swing strategy
#   - 30% ($6K):  5-day sector rotation (1 pos bull)
#   - 10% ($2K):  Cash (no return)

import argparse
import sys
from datetime import datetime, timedelta

try:
    import pandas as pd
    import yfinance as yf
except ImportError:
    print("Requires: pip install pandas yfinance")
    sys.exit(1)

# Allocation
SWING_PCT = 0.60
SECTOR_PCT = 0.30
CASH_PCT = 0.10
INITIAL_CAPITAL = 20000.0

SWING_CAPITAL = INITIAL_CAPITAL * SWING_PCT   # $12,000
SECTOR_CAPITAL = INITIAL_CAPITAL * SECTOR_PCT # $6,000
CASH = INITIAL_CAPITAL * CASH_PCT             # $2,000

# Sector rotation tickers (from sector_rotation_backtest)
SECTOR_ETFS = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
SECTOR_TO_LEVERAGED = {
    "XLK": "TQQQ", "XLF": "FAS", "XLE": "ERX", "XLV": "CURE",
    "XLI": "DUSL", "XLY": "RETL", "XLP": None, "XLU": None, "XLB": None,
    "XLRE": "DRN", "XLC": None,
}


def _get_close(data: pd.DataFrame, ticker: str, date: pd.Timestamp):
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


def _rank_sectors(data: pd.DataFrame, date: pd.Timestamp, lookback: int = 5):
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


def run_sector_backtest(data: pd.DataFrame, start_ts, end_ts, cycle_days: int = 5):
    """1 pos bull sector rotation. Returns cycle_list with entry, exit, return_pct."""
    dates = sorted([d for d in data.index if start_ts <= d <= end_ts])
    if not dates:
        return {"error": "No dates", "cycle_list": []}
    dates = [pd.Timestamp(d) for d in dates]
    equity = 10000.0
    cycles = []
    current_pos = None
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
                    "entry": entry_date, "exit": day,
                    "return_pct": pct, "equity": equity,
                    "entry_str": entry_date.strftime("%Y-%m-%d"), "exit_str": day.strftime("%Y-%m-%d"),
                })
            current_pos = None
        if current_pos is None:
            ranked = _rank_sectors(data, day, lookback=5)
            if ranked:
                top_etf, top_ret = ranked[0]
                ticker = SECTOR_TO_LEVERAGED.get(top_etf) or top_etf
                price = _get_close(data, ticker, day)
                if price and price > 0:
                    current_pos = (ticker, price)
                    entry_date = day
        i += 1
    return {"cycle_list": cycles, "final_equity": equity}


def run_swing_backtest_simple(tickers, start_str, end_str, position_size: float = 5000):
    """Import and run swing backtest. Returns trade_list."""
    from strategy_backtest import run_backtest
    return run_backtest(tickers, start_str, end_str, position_size=position_size)


def build_hybrid_equity_curve(sector_cycles, swing_trades, swing_position_size, all_dates):
    """Build daily equity for hybrid portfolio."""
    sector_equity = SECTOR_CAPITAL
    sector_cycle_idx = 0
    swing_equity = SWING_CAPITAL
    realized_swing_pnl = 0.0
    trade_exits = {}  # date_str -> list of pct_returns
    for t in swing_trades:
        exit_str = t["exit_date"]
        if exit_str not in trade_exits:
            trade_exits[exit_str] = []
        trade_exits[exit_str].append(t["pct_return"])

    equity_curve = []
    peak = INITIAL_CAPITAL
    max_dd = 0.0

    for d in all_dates:
        d_str = d.strftime("%Y-%m-%d")
        # Sector: update at cycle end
        while sector_cycle_idx < len(sector_cycles) and sector_cycles[sector_cycle_idx]["exit"] <= d:
            c = sector_cycles[sector_cycle_idx]
            sector_equity *= (1 + c["return_pct"] / 100)
            sector_cycle_idx += 1
        # Swing: add P&L for trades that exited on or before today
        if d_str in trade_exits:
            for r in trade_exits[d_str]:
                realized_swing_pnl += swing_position_size * (r / 100)
        swing_equity = SWING_CAPITAL + realized_swing_pnl
        total = sector_equity + swing_equity + CASH
        equity_curve.append((d, total))
        if total > peak:
            peak = total
        dd = (peak - total) / peak * 100 if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd

    return equity_curve, max_dd


def main():
    ap = argparse.ArgumentParser(description="Hybrid backtest: 60% swing + 30% sector + 10% cash")
    ap.add_argument("--days", type=int, default=780, help="Trading days (default 780 ~3yr)")
    args = ap.parse_args()

    end = datetime.now()
    cal_days = int(args.days * 365 / 252)
    start = end - timedelta(days=cal_days)
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    fetch_start = (start - timedelta(days=60)).strftime("%Y-%m-%d")
    start_ts = pd.Timestamp(start_str)
    end_ts = pd.Timestamp(end_str)

    print("=" * 70)
    print("HYBRID BACKTEST: 60% Swing Dip + 30% Sector Rotation + 10% Cash")
    print("=" * 70)
    print(f"Period: {args.days} trading days (~{args.days/252:.1f} years)")
    print(f"Capital: ${INITIAL_CAPITAL:,.0f}  |  Swing ${SWING_CAPITAL:,.0f}  |  Sector ${SECTOR_CAPITAL:,.0f}  |  Cash ${CASH:,.0f}")
    print()

    # 1. Fetch sector data
    sector_tickers = SECTOR_ETFS + list(set(SECTOR_TO_LEVERAGED.values()) - {None})
    sector_tickers = [t for t in sector_tickers if t]
    print("Fetching sector data...")
    sector_data = yf.download(sector_tickers, start=fetch_start, end=end_str, interval="1d",
                              group_by="ticker", auto_adjust=True, progress=False, threads=True)
    if sector_data is None or sector_data.empty:
        print("No sector data")
        return 1

    sector_res = run_sector_backtest(sector_data, start_ts, end_ts, cycle_days=5)
    if sector_res.get("error"):
        print("Sector backtest error")
        return 1

    sector_cycles = sector_res["cycle_list"]
    sector_final = SECTOR_CAPITAL * (sector_res["final_equity"] / 10000.0)
    sector_ret = (sector_final - SECTOR_CAPITAL) / SECTOR_CAPITAL * 100

    # 2. Run swing backtest
    from strategy_backtest import _get_tickers, run_backtest
    tickers = _get_tickers(100, universe="sp500")
    print("Running swing backtest (S&P 500, position size $5K)...")
    swing_res = run_backtest(tickers, start_str, end_str, position_size=5000)
    if swing_res.get("error"):
        print(f"Swing error: {swing_res['error']}")
        return 1

    swing_trades = swing_res.get("trade_list", [])
    swing_total_ret = swing_res["total_return_pct"]
    # Swing P&L: each trade $5K * pct_return. With $12K sleeve, effective growth
    swing_pnl = sum(5000 * (t["pct_return"] / 100) for t in swing_trades)
    swing_final = SWING_CAPITAL + swing_pnl
    swing_ret = (swing_final - SWING_CAPITAL) / SWING_CAPITAL * 100

    # 3. Build hybrid equity curve
    all_dates = sorted([d for d in sector_data.index if start_ts <= d <= end_ts])
    all_dates = [pd.Timestamp(d) for d in all_dates]
    equity_curve, max_dd = build_hybrid_equity_curve(
        sector_cycles, swing_trades, 5000, all_dates
    )

    total_final = swing_final + sector_final + CASH
    total_ret = (total_final - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    daily_avg_pct = total_ret / args.days if args.days else 0
    daily_avg_dollars = (total_final - INITIAL_CAPITAL) / args.days if args.days else 0

    # Report
    print()
    print("-" * 70)
    print("SLEEVE RESULTS")
    print("-" * 70)
    print(f"  Swing (60%):  ${SWING_CAPITAL:,.0f} -> ${swing_final:,.0f}  |  {swing_ret:+.1f}%  |  {len(swing_trades)} trades, {swing_res['win_rate']}% win")
    print(f"  Sector (30%): ${SECTOR_CAPITAL:,.0f} -> ${sector_final:,.0f}  |  {sector_ret:+.1f}%  |  {len(sector_cycles)} cycles")
    print(f"  Cash (10%):   ${CASH:,.0f} -> ${CASH:,.0f}  |  +0.0%")
    print()
    print("-" * 70)
    print("HYBRID PORTFOLIO")
    print("-" * 70)
    print(f"  Initial:     ${INITIAL_CAPITAL:,.0f}")
    print(f"  Final:       ${total_final:,.0f}")
    print(f"  Total Return: {total_ret:+.1f}%")
    print(f"  Max Drawdown: {max_dd:.1f}%")
    print(f"  ~$/day avg:   ${daily_avg_dollars:.0f}")
    print(f"  ~%/day avg:  {daily_avg_pct:.3f}%")
    print()
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
