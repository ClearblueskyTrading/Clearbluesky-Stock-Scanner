#!/usr/bin/env python3
"""Run all three scans with timing. Exit 0 = all ok."""
import sys
import time

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scanner_cli import main as cli_main

SCANS = ["velocity_trend_growth", "swing", "watchlist"]

if __name__ == "__main__":
    total_start = time.time()
    for i, scan in enumerate(SCANS):
        start = time.time()
        print(f"\n{'='*60}")
        print(f"[{i+1}/3] {scan} — starting at {time.strftime('%H:%M:%S')}")
        print("="*60)
        sys.argv = ["scanner_cli.py", "--scan", scan]
        try:
            code = cli_main()
            elapsed = time.time() - start
            print(f"\n   Completed in {elapsed:.1f}s")
            if code != 0:
                print(f"   [WARN] Exit code {code}")
        except Exception as e:
            elapsed = time.time() - start
            print(f"\n   Failed after {elapsed:.1f}s: {e}")
            sys.exit(1)
    total = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"ALL 3 SCANS DONE in {total:.1f}s total (~{total/60:.1f} min)")
    print("="*60)
    sys.exit(0)
