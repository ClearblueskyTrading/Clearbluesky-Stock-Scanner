#!/usr/bin/env python3
"""Check premarket/market prices every 5 min. Run until user says stop."""

import time
from datetime import datetime

TICKERS = ["UAL", "APP", "GGLL"]


def fetch_prices():
    out = {}
    try:
        import yfinance as yf
        for t in TICKERS:
            try:
                info = yf.Ticker(t).info
                # Prefer premarket when available
                p = info.get("preMarketPrice") or info.get("currentPrice") or info.get("regularMarketPrice")
                if p is not None:
                    out[t] = round(float(p), 2)
            except Exception:
                pass
    except Exception:
        pass
    return out if out else None


def main():
    print("=== Price check every 5 min (stop with Ctrl+C) ===\n")
    count = 0
    while True:
        count += 1
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prices = fetch_prices()
        print(f"[{ts}] Check #{count}")
        if prices:
            for t, p in prices.items():
                print(f"  {t}: ${p}")
        else:
            print("  (no data)")
        print("  --- Your Schwab prices: check your screen ---\n")
        time.sleep(300)


if __name__ == "__main__":
    main()
