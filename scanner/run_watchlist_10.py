#!/usr/bin/env python3
"""One-off: run watchlist scan with 10% down filter."""
import sys
import os
BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from scan_settings import load_config
from watchlist_scanner import run_watchlist_scan

config = load_config() or {}
config = dict(config)
config["watchlist_pct_down_from_open"] = 10.0
config["watchlist_filter"] = "down_pct"

def progress(msg):
    print("   ", msg, flush=True)

print("Running watchlist scan (down 0-10% today)...", flush=True)
results = run_watchlist_scan(progress_callback=progress, config=config)
if results:
    print(f"Found {len(results)} tickers", flush=True)
    for r in results[:15]:
        print(f"  {r.get('ticker')} {r.get('Change','')} score={r.get('score',0)}", flush=True)
else:
    print("No results", flush=True)
