"""
ClearBlueSky – Backtest scanner & PTM settings for T1 and T2 strategies.
Uses backtest_signals.db to optimize min_score, stop/target, hold period.
Run: python backtest_scanner_settings.py [--update-outcomes] [--days 780]

T1 (Trader 1): 3 Stock Rotation — sweeps ptm_single_stock_stop_pct (3–7%).
T2 (Trader 2): Swing sleeve — sweeps ptm_min_score (80–95), stop/target/max_hold.
"""

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "user_config.json"


def _ensure_outcomes():
    """Fill outcomes for signals that don't have them."""
    from backtest_db import update_outcomes
    print("Updating T+1/T+3/T+5/T+10 outcomes (yfinance)...")
    n = update_outcomes(progress_callback=lambda m: print(f"  {m}"))
    print(f"  Updated {n} signals.")
    return n


def _get_signals_with_outcomes(scan_types=None):
    """Return list of (ticker, scan_type, score, price_at_signal, pct_t1, t3, t5, t10)."""
    from backtest_db import init_db, _get_conn
    init_db()
    conn = _get_conn()
    try:
        if scan_types:
            placeholders = ",".join("?" * len(scan_types))
            rows = conn.execute(f"""
                SELECT s.ticker, s.scan_type, s.score, s.price_at_signal,
                       o.pct_t1, o.pct_t3, o.pct_t5, o.pct_t10
                FROM signals s
                JOIN outcomes o ON s.id = o.signal_id
                WHERE s.scan_type IN ({placeholders})
            """, scan_types).fetchall()
        else:
            rows = conn.execute("""
                SELECT s.ticker, s.scan_type, s.score, s.price_at_signal,
                       o.pct_t1, o.pct_t3, o.pct_t5, o.pct_t10
                FROM signals s
                JOIN outcomes o ON s.id = o.signal_id
            """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _simulate_swing_exit(pct_t1, pct_t3, pct_t5, pct_t10, stop_pct, target_pct, max_hold):
    """
    Simulate T2 swing exit: stop, target, or max_hold. Returns (exit_day, return_pct).
    Assumes we check at EOD. Uses T+1, T+3, T+5, T+10 (no T+2, T+4, etc.).
    """
    checks = [(1, pct_t1), (3, pct_t3), (5, pct_t5), (10, pct_t10)]
    for day, pct in checks:
        if pct is None or day > max_hold:
            continue
        if pct <= stop_pct:
            return day, stop_pct
        if pct >= target_pct:
            return day, target_pct
    # No stop/target hit — exit at max_hold (use closest available day)
    exit_vals = [(d, p) for d, p in checks if d <= max_hold and p is not None]
    return (exit_vals[-1][0], exit_vals[-1][1]) if exit_vals else (max_hold, 0.0)


def run_t2_settings_backtest(signals, min_scores, stop_targets, max_holds):
    """Sweep T2 swing settings. Returns best config and full grid."""
    SWING_SCAN_TYPES = (
        "Swing", "Swing - Dips", "Emotional Dip", "Emotional Dip Scan",
        "Enhanced Dip", "Dip Scan", "Watchlist Scan"  # Watchlist can feed swing
    )
    swing_signals = [s for s in signals if s["scan_type"] in SWING_SCAN_TYPES]
    if len(swing_signals) < 5:
        return None, "Not enough swing signals with outcomes"

    results = []
    for min_score in min_scores:
        filtered = [s for s in swing_signals if s["score"] >= min_score]
        if len(filtered) < 3:
            continue
        for stop_pct, target_pct in stop_targets:
            for max_hold in max_holds:
                total_ret = 0.0
                n = 0
                for s in filtered:
                    exit_day, ret = _simulate_swing_exit(
                        s["pct_t1"], s["pct_t3"], s["pct_t5"], s["pct_t10"],
                        stop_pct, target_pct, max_hold
                    )
                    total_ret += ret
                    n += 1
                avg_ret = total_ret / n if n else 0
                win_count = sum(
                    1 for s in filtered
                    if _simulate_swing_exit(
                        s["pct_t1"], s["pct_t3"], s["pct_t5"], s["pct_t10"],
                        stop_pct, target_pct, max_hold
                    )[1] > 0
                )
                win_rate = win_count / n * 100 if n else 0
                results.append({
                    "ptm_min_score": min_score,
                    "ptm_stop_pct": stop_pct,
                    "ptm_target_pct": target_pct,
                    "ptm_max_hold_days": max_hold,
                    "n_signals": n,
                    "avg_return_pct": round(avg_ret, 2),
                    "win_rate": round(win_rate, 1),
                })

    if not results:
        return None, "No valid combinations"
    best = max(results, key=lambda r: (r["avg_return_pct"], r["win_rate"]))
    return best, results


def run_t1_stop_sweep(days=780):
    """Sweep T1 rotation stop_pct (3–7%). Returns best stop."""
    try:
        from single_stock_rotation_backtest import run_backtest, UNIVERSE
        import pandas as pd
        import yfinance as yf
        from datetime import datetime, timedelta
    except ImportError as e:
        return None, str(e)

    end = datetime.now()
    cal_days = int(days * 365 / 252)
    start = end - timedelta(days=cal_days)
    fetch_start = start - timedelta(days=120)
    start_str = fetch_start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    start_ts = pd.Timestamp(start.strftime("%Y-%m-%d"))
    end_ts = pd.Timestamp(end_str)

    signal_tickers = list(dict.fromkeys([u[1] for u in UNIVERSE]))
    lev_tickers = list(dict.fromkeys([u[2] for u in UNIVERSE]))
    all_tickers = list(dict.fromkeys(signal_tickers + lev_tickers))

    print("Fetching rotation data for T1 stop sweep...")
    data = yf.download(all_tickers, start=start_str, end=end_str, interval="1d",
                       group_by="ticker", auto_adjust=True, progress=False, threads=True)
    if data is None or data.empty:
        return None, "No rotation data"

    cap = 12000  # 60% of $20K
    results = []
    for stop_pct in [3, 4, 5, 6, 7]:
        r = run_backtest(data, start_ts, end_ts, stop_pct=stop_pct, principal=cap)
        if r.get("error"):
            continue
        results.append({
            "ptm_single_stock_stop_pct": stop_pct,
            "total_return_pct": round(r.get("total_return_pct", 0), 1),
            "final_equity": r.get("final_equity", 0),
        })
    if not results:
        return None, "T1 backtest failed"
    best = max(results, key=lambda x: x["total_return_pct"])
    return best, results


def main():
    ap = argparse.ArgumentParser(description="Backtest scanner settings for T1/T2")
    ap.add_argument("--update-outcomes", action="store_true", help="Fill outcomes first (yfinance)")
    ap.add_argument("--days", type=int, default=780, help="T1 rotation backtest days")
    ap.add_argument("--t1-only", action="store_true", help="Only run T1 stop sweep")
    ap.add_argument("--t2-only", action="store_true", help="Only run T2 settings backtest")
    args = ap.parse_args()

    print("=" * 60)
    print("Scanner Settings Backtest — T1 & T2")
    print("=" * 60)

    if args.update_outcomes:
        _ensure_outcomes()
    elif not args.t1_only:
        from backtest_db import _get_conn, init_db
        init_db()
        conn = _get_conn()
        n_out = conn.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0]
        conn.close()
        if n_out == 0:
            print("No outcomes in DB. Run with --update-outcomes first.")
            _ensure_outcomes()

    recommendations = {}
    t1_result = None
    t2_result = None

    # T1: Rotation stop sweep
    if not args.t2_only:
        print("\n--- T1: Single Stock Rotation (60% sleeve) ---")
        t1_result, t1_data = run_t1_stop_sweep(args.days)
        if t1_result:
            print(f"  Best stop: {t1_result['ptm_single_stock_stop_pct']}%  Return: {t1_result['total_return_pct']:+.1f}%")
            for r in (t1_data or []):
                print(f"    stop {r['ptm_single_stock_stop_pct']}%: {r['total_return_pct']:+.1f}%")
            recommendations["ptm_single_stock_stop_pct"] = t1_result["ptm_single_stock_stop_pct"]
        else:
            print(f"  T1: {t1_data}")

    # T2: Swing settings sweep
    if not args.t1_only:
        print("\n--- T2: Swing sleeve settings ---")
        signals = _get_signals_with_outcomes()
        if len(signals) < 5:
            print("  Not enough signals with outcomes. Run --update-outcomes and ensure scans have run.")
        else:
            t2_result, t2_data = run_t2_settings_backtest(
                signals,
                min_scores=[80, 85, 90, 95],
                stop_targets=[(-2, 3), (-2.5, 3.5), (-2, 4), (-2.5, 4)],
                max_holds=[5, 7],
            )
            if t2_result:
                print(f"  Best: min_score={t2_result['ptm_min_score']}, stop={t2_result['ptm_stop_pct']}%, target={t2_result['ptm_target_pct']}%, max_hold={t2_result['ptm_max_hold_days']}d")
                print(f"  Avg return: {t2_result['avg_return_pct']:.2f}%  Win rate: {t2_result['win_rate']:.1f}%  (n={t2_result['n_signals']})")
                recommendations["ptm_min_score"] = t2_result["ptm_min_score"]
                recommendations["ptm_stop_pct"] = t2_result["ptm_stop_pct"]
                recommendations["ptm_target_pct"] = t2_result["ptm_target_pct"]
                recommendations["ptm_max_hold_days"] = t2_result["ptm_max_hold_days"]
            else:
                print(f"  T2: {t2_data}")

    # Write recommendations
    if recommendations:
        out_path = BASE_DIR / "reports" / "scanner_settings_recommendations.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump({
                "recommendations": recommendations,
                "t1_best": t1_result,
                "t2_best": t2_result,
                "note": "Apply these to user_config.json to improve T1/T2 performance.",
            }, f, indent=2)
        print(f"\nRecommendations saved to: {out_path}")
        print("\nSuggested user_config.json changes:")
        for k, v in recommendations.items():
            print(f"  \"{k}\": {v}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
