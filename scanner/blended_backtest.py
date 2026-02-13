# ============================================================
# Blended Allocation: 60% Single-Stock Rotation + 15% GDX + 15% FCX + 10% Cash
# ============================================================
# Run: python blended_backtest.py [--days 780]

import argparse
import sys
from datetime import datetime, timedelta

try:
    import pandas as pd
    import yfinance as yf
except ImportError:
    print("Requires: pip install pandas yfinance")
    sys.exit(1)

# Import rotation backtest
from single_stock_rotation_backtest import run_backtest, UNIVERSE

ALLOCATION = {
    "rotation": 0.60,
    "gdx": 0.15,
    "fcx": 0.15,
    "cash": 0.10,
}


def main():
    ap = argparse.ArgumentParser(description="60% rotation + 15% GDX + 15% FCX + 10% cash")
    ap.add_argument("--days", type=int, default=780)
    ap.add_argument("--principal", type=float, default=20000)
    args = ap.parse_args()

    end = datetime.now()
    cal_days = int(args.days * 365 / 252)
    start = end - timedelta(days=cal_days)
    fetch_start = start - timedelta(days=120)
    start_str = fetch_start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    start_ts = pd.Timestamp(start.strftime("%Y-%m-%d"))
    end_ts = pd.Timestamp(end_str)

    cap = args.principal
    rotation_cap = cap * ALLOCATION["rotation"]
    gdx_cap = cap * ALLOCATION["gdx"]
    fcx_cap = cap * ALLOCATION["fcx"]
    cash_cap = cap * ALLOCATION["cash"]

    print("=" * 70)
    print("BLENDED ALLOCATION: 60% Rotation + 15% GDX + 15% FCX + 10% Cash")
    print("=" * 70)
    print(f"Principal: ${cap:,.0f}  |  Period: ~{args.days} days")
    print(f"  Rotation (60%): ${rotation_cap:,.0f}")
    print(f"  GDX (15%):     ${gdx_cap:,.0f}")
    print(f"  FCX (15%):     ${fcx_cap:,.0f}")
    print(f"  Cash (10%):    ${cash_cap:,.0f}")
    print()

    # 1. Run single-stock rotation on 60% sleeve
    signal_tickers = list(dict.fromkeys([u[1] for u in UNIVERSE]))
    lev_tickers = list(dict.fromkeys([u[2] for u in UNIVERSE]))
    all_tickers = list(dict.fromkeys(signal_tickers + lev_tickers))
    print("Fetching rotation data...")
    data = yf.download(all_tickers, start=start_str, end=end_str, interval="1d",
                       group_by="ticker", auto_adjust=True, progress=False, threads=True)
    if data is None or data.empty:
        print("No rotation data")
        return 1

    r = run_backtest(data, start_ts, end_ts, stop_pct=5, principal=rotation_cap)
    if r.get("error"):
        print(f"Rotation error: {r['error']}")
        return 1

    rotation_final = r["final_equity"]
    rotation_ret = r["total_return_pct"]
    print(f"  Rotation: ${rotation_cap:,.0f} -> ${rotation_final:,.0f}  ({rotation_ret:+.1f}%)")

    # 2. GDX and FCX buy-and-hold
    print("Fetching GDX, FCX...")
    bnh = yf.download(["GDX", "FCX"], start=start_str, end=end_str, interval="1d",
                      group_by="ticker", auto_adjust=True, progress=False)
    if bnh is None or bnh.empty:
        print("No GDX/FCX data")
        return 1

    def _bnh_return(ticker: str) -> tuple:
        try:
            if isinstance(bnh.columns, pd.MultiIndex):
                close = bnh[ticker]["Close"]
            else:
                close = bnh["Close"]
            rows = close.loc[close.index >= start_ts].dropna()
            if len(rows) < 2:
                return 0.0, 0.0
            start_p = float(rows.iloc[0])
            end_p = float(rows.iloc[-1])
            if start_p <= 0:
                return 0.0, 0.0
            ret = (end_p - start_p) / start_p * 100
            return ret, ret
        except Exception:
            return 0.0, 0.0

    gdx_ret, _ = _bnh_return("GDX")
    fcx_ret, _ = _bnh_return("FCX")

    gdx_final = gdx_cap * (1 + gdx_ret / 100)
    fcx_final = fcx_cap * (1 + fcx_ret / 100)

    print(f"  GDX:     ${gdx_cap:,.0f} -> ${gdx_final:,.0f}  ({gdx_ret:+.1f}%)")
    print(f"  FCX:     ${fcx_cap:,.0f} -> ${fcx_final:,.0f}  ({fcx_ret:+.1f}%)")
    print(f"  Cash:    ${cash_cap:,.0f} -> ${cash_cap:,.0f}  (0%)")
    print()

    # 3. Total
    total_final = rotation_final + gdx_final + fcx_final + cash_cap
    total_ret = (total_final - cap) / cap * 100
    years = args.days / 252
    ann_mult = (1 + total_ret / 100) ** (1 / years) if years > 0 else 1
    weekly_pct = ann_mult ** (1 / 52) - 1
    monthly_pct = ann_mult ** (1 / 12) - 1
    weekly_amt = cap * weekly_pct
    monthly_amt = cap * monthly_pct

    print("-" * 70)
    print("BLENDED PORTFOLIO")
    print("-" * 70)
    print(f"  Initial:  ${cap:,.0f}")
    print(f"  Final:    ${total_final:,.0f}")
    print(f"  Return:   {total_ret:+.1f}%")
    print()
    print("  --- Weekly / Monthly on ${:,.0f} ---".format(cap))
    print(f"  weekly ~${weekly_amt:,.0f}  |  monthly ~${monthly_amt:,.0f}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
