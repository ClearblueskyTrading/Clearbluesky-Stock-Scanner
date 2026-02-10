# ============================================================
# ClearBlueSky - Scan History Analyzer & Report Generator
# ============================================================
# Reads scan_history.json (accumulated over time) and produces
# a comprehensive History Report with stats, patterns, and insights.

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GITHUB_URL = "https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner/releases"


def load_history(reports_dir: str = None) -> List[Dict]:
    """Load scan_history.json and return list of scan entries."""
    if reports_dir is None:
        reports_dir = os.path.join(BASE_DIR, "reports")
    path = os.path.join(reports_dir, "scan_history.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else [data]
    except Exception:
        return []


def _parse_report_timestamp(ts_str: str) -> Optional[str]:
    """Try to parse various timestamp formats from report JSON files into YYYY-MM-DD HH:MM."""
    for fmt in ("%B %d, %Y at %I:%M:%S %p", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
                "%B %d, %Y at %H:%M:%S", "%m/%d/%Y %H:%M"):
        try:
            dt = datetime.strptime(ts_str.strip(), fmt)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            continue
    # Fallback: try extracting date from filename-style timestamps
    try:
        # "February 06, 2026 at 10:20:51 AM" format
        dt = datetime.strptime(ts_str.strip(), "%B %d, %Y at %I:%M:%S %p")
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass
    return ts_str[:16] if len(ts_str) >= 16 else ts_str


def backfill_from_reports(reports_dir: str = None, progress_callback=None) -> int:
    """
    Scan all JSON report files in reports_dir and backfill scan_history.json.
    Deduplicates by scan_type + timestamp.
    Returns number of new entries added.
    """
    if reports_dir is None:
        reports_dir = os.path.join(BASE_DIR, "reports")

    # Load existing history
    history_path = os.path.join(reports_dir, "scan_history.json")
    existing = []
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                existing = [existing]
        except Exception:
            existing = []

    # Build set of existing keys for dedup
    existing_keys = set()
    for e in existing:
        key = f"{e.get('scan_type', '')}|{e.get('timestamp', '')}"
        existing_keys.add(key)

    # Find all JSON report files (exclude scan_history.json itself)
    import glob
    json_files = sorted(glob.glob(os.path.join(reports_dir, "*.json")))
    json_files = [f for f in json_files if "scan_history" not in os.path.basename(f).lower()]

    if progress_callback:
        progress_callback(f"Scanning {len(json_files)} report files...")

    added = 0
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                report = json.load(f)
        except Exception:
            continue

        scan_type = report.get("scan_type", "Unknown")
        raw_ts = report.get("timestamp", "")
        timestamp = _parse_report_timestamp(raw_ts)

        # Dedup check
        key = f"{scan_type}|{timestamp}"
        if key in existing_keys:
            continue

        stocks = report.get("stocks", [])
        if not stocks:
            continue

        # Build slim stock entries (same format as report_generator appends)
        slim_stocks = []
        for s in stocks:
            slim = {}
            for k in ("ticker", "score", "price", "change", "sector", "industry",
                       "rsi", "sma200_status", "rel_volume", "recom", "on_watchlist"):
                if k in s:
                    slim[k] = s[k]
            if s.get("leveraged_play"):
                slim["leveraged_play"] = s["leveraged_play"]
            if s.get("smart_money"):
                slim["smart_money"] = s["smart_money"]
            slim_stocks.append(slim)

        entry = {
            "scan_type": scan_type,
            "timestamp": timestamp,
            "stocks": slim_stocks,
        }
        if report.get("market_breadth"):
            entry["market_breadth"] = report["market_breadth"]
        if report.get("price_history_30d"):
            entry["price_history_30d"] = report["price_history_30d"]

        existing.append(entry)
        existing_keys.add(key)
        added += 1

        if progress_callback:
            progress_callback(f"Imported: {os.path.basename(filepath)} ({len(slim_stocks)} stocks)")

    # Sort by timestamp
    existing.sort(key=lambda x: x.get("timestamp", ""))

    # Save
    try:
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2)
    except Exception as e:
        if progress_callback:
            progress_callback(f"Error saving history: {e}")
        return 0

    if progress_callback:
        progress_callback(f"Backfill complete: {added} new entries added ({len(existing)} total)")

    return added


def analyze_history(history: List[Dict]) -> Dict:
    """Analyze scan history and return stats dict."""
    if not history:
        return {"error": "No scan history found. Run some scans first."}

    stats = {
        "total_scans": len(history),
        "date_range": {"first": None, "last": None},
        "scans_by_type": Counter(),
        "scans_by_day": Counter(),
        "top_tickers": Counter(),         # Most frequently flagged
        "top_scored": [],                  # Highest individual scores ever
        "ticker_appearances": defaultdict(list),  # ticker -> list of {timestamp, score, price, scan_type}
        "repeat_tickers": {},             # Tickers appearing 3+ times
        "score_distribution": {"elite_90": 0, "strong_80": 0, "good_70": 0, "decent_60": 0, "below_60": 0},
        "avg_score_by_type": defaultdict(list),
        "sector_frequency": Counter(),
        "regime_history": [],             # Market regime over time
        "leveraged_plays": Counter(),     # How often leveraged plays were suggested
        "watchlist_hit_rate": {"hits": 0, "total_stocks": 0},
        "smart_money_overlap": {"wsb_flagged": 0, "insider_activity": 0, "institutional": 0, "total_stocks": 0},
        "price_trends": {},               # Tickers with enough history to show price movement
    }

    all_scores = []

    for entry in history:
        scan_type = entry.get("scan_type", "Unknown")
        timestamp = entry.get("timestamp", "")
        stocks = entry.get("stocks", [])

        stats["scans_by_type"][scan_type] += 1

        # Parse date for day-of-week
        try:
            dt = datetime.strptime(timestamp[:10], "%Y-%m-%d")
            stats["scans_by_day"][dt.strftime("%A")] += 1
            date_str = dt.strftime("%Y-%m-%d")
            if stats["date_range"]["first"] is None or date_str < stats["date_range"]["first"]:
                stats["date_range"]["first"] = date_str
            if stats["date_range"]["last"] is None or date_str > stats["date_range"]["last"]:
                stats["date_range"]["last"] = date_str
        except Exception:
            pass

        # Market regime
        breadth = entry.get("market_breadth", {})
        if breadth and breadth.get("market_regime"):
            stats["regime_history"].append({
                "timestamp": timestamp,
                "regime": breadth.get("market_regime"),
                "above_sma50": breadth.get("sp500_above_sma50_pct"),
                "above_sma200": breadth.get("sp500_above_sma200_pct"),
            })

        for s in stocks:
            ticker = s.get("ticker", "")
            score = s.get("score", 0)
            price = s.get("price", "N/A")

            stats["top_tickers"][ticker] += 1
            stats["ticker_appearances"][ticker].append({
                "timestamp": timestamp,
                "score": score,
                "price": price,
                "change": s.get("change", "N/A"),
                "scan_type": scan_type,
            })

            all_scores.append(score)
            stats["avg_score_by_type"][scan_type].append(score)

            # Score distribution
            if score >= 90:
                stats["score_distribution"]["elite_90"] += 1
            elif score >= 80:
                stats["score_distribution"]["strong_80"] += 1
            elif score >= 70:
                stats["score_distribution"]["good_70"] += 1
            elif score >= 60:
                stats["score_distribution"]["decent_60"] += 1
            else:
                stats["score_distribution"]["below_60"] += 1

            # Top scored
            stats["top_scored"].append({
                "ticker": ticker, "score": score, "price": price,
                "scan_type": scan_type, "timestamp": timestamp,
            })

            # Sector
            sector = s.get("sector")
            if sector and sector != "N/A":
                stats["sector_frequency"][sector] += 1

            # Leveraged plays
            if s.get("leveraged_play"):
                stats["leveraged_plays"][s["leveraged_play"]] += 1

            # Watchlist
            stats["watchlist_hit_rate"]["total_stocks"] += 1
            if s.get("on_watchlist"):
                stats["watchlist_hit_rate"]["hits"] += 1

            # Smart money
            sm = s.get("smart_money", {})
            stats["smart_money_overlap"]["total_stocks"] += 1
            if sm.get("wsb"):
                stats["smart_money_overlap"]["wsb_flagged"] += 1
            if sm.get("insider_filings"):
                stats["smart_money_overlap"]["insider_activity"] += 1
            if sm.get("institutional"):
                stats["smart_money_overlap"]["institutional"] += 1

    # Post-processing
    stats["top_scored"] = sorted(stats["top_scored"], key=lambda x: x["score"], reverse=True)[:20]

    # Repeat tickers (3+ appearances)
    stats["repeat_tickers"] = {
        t: len(apps) for t, apps in stats["ticker_appearances"].items() if len(apps) >= 3
    }

    # Average score by scan type
    avg_by_type = {}
    for st, scores in stats["avg_score_by_type"].items():
        avg_by_type[st] = round(sum(scores) / len(scores), 1) if scores else 0
    stats["avg_score_by_type"] = avg_by_type

    # Overall average
    stats["avg_score_overall"] = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0
    stats["total_stock_picks"] = len(all_scores)

    # Price trend tracking: for tickers with 2+ appearances, show first vs last price
    for ticker, appearances in stats["ticker_appearances"].items():
        if len(appearances) >= 2:
            first = appearances[0]
            last = appearances[-1]
            try:
                p1 = float(first["price"]) if first["price"] != "N/A" else None
                p2 = float(last["price"]) if last["price"] != "N/A" else None
                if p1 and p2 and p1 != 0:
                    pct = round(((p2 - p1) / p1) * 100, 1)
                    stats["price_trends"][ticker] = {
                        "first_price": p1, "first_date": first["timestamp"][:10],
                        "first_score": first["score"],
                        "last_price": p2, "last_date": last["timestamp"][:10],
                        "last_score": last["score"],
                        "price_change_pct": pct,
                        "appearances": len(appearances),
                    }
            except Exception:
                pass

    # Sort price trends by appearances (most tracked first)
    stats["price_trends"] = dict(
        sorted(stats["price_trends"].items(), key=lambda x: x[1]["appearances"], reverse=True)
    )

    return stats


def generate_history_report(reports_dir: str = None, progress_callback=None) -> Tuple[str, str]:
    """
    Generate a text history report from scan_history.json.
    Returns (report_text, filepath).
    """
    if reports_dir is None:
        reports_dir = os.path.join(BASE_DIR, "reports")

    # Auto-backfill from existing JSON report files first
    if progress_callback:
        progress_callback("Backfilling from existing reports...")
    try:
        backfill_from_reports(reports_dir=reports_dir, progress_callback=progress_callback)
    except Exception:
        pass

    if progress_callback:
        progress_callback("Loading scan history...")

    history = load_history(reports_dir)
    if not history:
        return "No scan history found. Run some scans first — history accumulates automatically.", ""

    if progress_callback:
        progress_callback(f"Analyzing {len(history)} scans...")

    stats = analyze_history(history)
    if "error" in stats:
        return stats["error"], ""

    # Build report
    lines = []
    lines.append("═" * 65)
    lines.append("  CLEARBLUESKY SCAN HISTORY REPORT")
    lines.append("═" * 65)
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"  History period: {stats['date_range']['first']} to {stats['date_range']['last']}")
    lines.append(f"  Total scans: {stats['total_scans']}  |  Total stock picks: {stats['total_stock_picks']}")
    lines.append(f"  Average score: {stats['avg_score_overall']}")
    lines.append("")

    # --- SCAN BREAKDOWN ---
    lines.append("─" * 65)
    lines.append("  SCANS BY TYPE")
    lines.append("─" * 65)
    for scan_type, count in stats["scans_by_type"].most_common():
        avg = stats["avg_score_by_type"].get(scan_type, 0)
        lines.append(f"  {scan_type:<30} {count:>4} scans  |  Avg score: {avg}")
    lines.append("")

    # --- SCAN DAYS ---
    lines.append("─" * 65)
    lines.append("  SCANS BY DAY OF WEEK")
    lines.append("─" * 65)
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for day in day_order:
        count = stats["scans_by_day"].get(day, 0)
        if count:
            bar = "█" * min(count, 40)
            lines.append(f"  {day:<12} {count:>3}  {bar}")
    lines.append("")

    # --- SCORE DISTRIBUTION ---
    lines.append("─" * 65)
    lines.append("  SCORE DISTRIBUTION (all picks)")
    lines.append("─" * 65)
    dist = stats["score_distribution"]
    total = stats["total_stock_picks"] or 1
    for label, key in [("90-100 Elite", "elite_90"), ("80-89 Strong", "strong_80"),
                       ("70-79 Good", "good_70"), ("60-69 Decent", "decent_60"),
                       ("<60 Skip", "below_60")]:
        count = dist[key]
        pct = round(count / total * 100, 1)
        bar = "█" * int(pct / 2)
        lines.append(f"  {label:<15} {count:>5}  ({pct:>5.1f}%)  {bar}")
    lines.append("")

    # --- TOP 15 MOST FLAGGED TICKERS ---
    lines.append("─" * 65)
    lines.append("  TOP 15 MOST FLAGGED TICKERS")
    lines.append("─" * 65)
    lines.append(f"  {'Ticker':<8} {'Count':>6} {'Avg Score':>10} {'Sectors':<20}")
    lines.append("  " + "─" * 50)
    for ticker, count in stats["top_tickers"].most_common(15):
        apps = stats["ticker_appearances"][ticker]
        avg_s = round(sum(a["score"] for a in apps) / len(apps), 1) if apps else 0
        sectors = set()
        for a in apps:
            # sector comes from the stock entry, not the appearance
            pass
        lines.append(f"  {ticker:<8} {count:>6} {avg_s:>10}")
    lines.append("")

    # --- REPEAT TICKERS (3+ appearances) ---
    if stats["repeat_tickers"]:
        lines.append("─" * 65)
        lines.append("  REPEAT TICKERS (appearing 3+ times — persistent signals)")
        lines.append("─" * 65)
        sorted_repeats = sorted(stats["repeat_tickers"].items(), key=lambda x: x[1], reverse=True)
        for ticker, count in sorted_repeats[:20]:
            apps = stats["ticker_appearances"][ticker]
            scores = [a["score"] for a in apps]
            lines.append(f"  {ticker:<8} {count} appearances | Scores: {min(scores)}-{max(scores)} | Avg: {round(sum(scores)/len(scores),1)}")
        lines.append("")

    # --- PRICE TRENDS (tickers with 2+ data points) ---
    if stats["price_trends"]:
        lines.append("─" * 65)
        lines.append("  PRICE TRENDS (first scan vs latest scan)")
        lines.append("─" * 65)
        lines.append(f"  {'Ticker':<8} {'First':>8} {'Latest':>8} {'Change':>8} {'#Scans':>7} {'First Date':<12} {'Last Date':<12}")
        lines.append("  " + "─" * 60)
        for ticker, pt in list(stats["price_trends"].items())[:20]:
            chg = pt["price_change_pct"]
            sign = "+" if chg >= 0 else ""
            lines.append(
                f"  {ticker:<8} ${pt['first_price']:>7.2f} ${pt['last_price']:>7.2f} {sign}{chg:>6.1f}% {pt['appearances']:>7} {pt['first_date']:<12} {pt['last_date']:<12}"
            )
        lines.append("")

    # --- TOP 20 HIGHEST SCORES EVER ---
    lines.append("─" * 65)
    lines.append("  TOP 20 HIGHEST SCORES EVER")
    lines.append("─" * 65)
    for i, pick in enumerate(stats["top_scored"][:20], 1):
        lines.append(f"  {i:>2}. {pick['ticker']:<8} Score {pick['score']:>3}  |  ${pick['price']}  |  {pick['scan_type']}  |  {pick['timestamp'][:10]}")
    lines.append("")

    # --- SECTOR FREQUENCY ---
    lines.append("─" * 65)
    lines.append("  SECTORS (most flagged)")
    lines.append("─" * 65)
    for sector, count in stats["sector_frequency"].most_common(11):
        bar = "█" * min(count, 40)
        lines.append(f"  {sector:<25} {count:>4}  {bar}")
    lines.append("")

    # --- MARKET REGIME HISTORY ---
    if stats["regime_history"]:
        lines.append("─" * 65)
        lines.append("  MARKET REGIME HISTORY")
        lines.append("─" * 65)
        regime_counts = Counter(r["regime"] for r in stats["regime_history"])
        for regime, count in regime_counts.most_common():
            lines.append(f"  {regime:<20} {count:>4} scans")
        lines.append("")
        # Last 10 regime readings
        lines.append("  Recent regime readings:")
        for r in stats["regime_history"][-10:]:
            sma50 = r.get("above_sma50", "?")
            sma200 = r.get("above_sma200", "?")
            lines.append(f"    {r['timestamp'][:16]}  {r['regime']:<15}  SMA50: {sma50}%  SMA200: {sma200}%")
        lines.append("")

    # --- LEVERAGED PLAYS ---
    if stats["leveraged_plays"]:
        lines.append("─" * 65)
        lines.append("  LEVERAGED PLAYS SUGGESTED")
        lines.append("─" * 65)
        for etf, count in stats["leveraged_plays"].most_common(10):
            lines.append(f"  {etf:<10} suggested {count} times")
        lines.append("")

    # --- SMART MONEY OVERLAP ---
    sm = stats["smart_money_overlap"]
    if sm["total_stocks"] > 0:
        lines.append("─" * 65)
        lines.append("  SMART MONEY OVERLAP")
        lines.append("─" * 65)
        lines.append(f"  Total stock picks analyzed:  {sm['total_stocks']}")
        lines.append(f"  WSB/Reddit trending:         {sm['wsb_flagged']}  ({round(sm['wsb_flagged']/sm['total_stocks']*100,1)}%)")
        lines.append(f"  Insider filing activity:     {sm['insider_activity']}  ({round(sm['insider_activity']/sm['total_stocks']*100,1)}%)")
        lines.append(f"  Institutional holders noted:  {sm['institutional']}  ({round(sm['institutional']/sm['total_stocks']*100,1)}%)")
        lines.append("")

    # --- WATCHLIST ---
    wl = stats["watchlist_hit_rate"]
    if wl["total_stocks"] > 0:
        lines.append("─" * 65)
        lines.append("  WATCHLIST HIT RATE")
        lines.append("─" * 65)
        pct = round(wl["hits"] / wl["total_stocks"] * 100, 1)
        lines.append(f"  Watchlist matches: {wl['hits']} out of {wl['total_stocks']} total picks ({pct}%)")
        lines.append("")

    # --- ACCURACY RATING (live check vs current prices) ---
    try:
        from accuracy_tracker import calculate_accuracy, format_accuracy_for_report
        if progress_callback:
            progress_callback("Calculating accuracy (fetching current prices)...")
        acc = calculate_accuracy(reports_dir=reports_dir)
        acc_text = format_accuracy_for_report(acc)
        if acc_text:
            lines.append(acc_text)
    except Exception:
        pass

    # --- FOOTER ---
    lines.append("═" * 65)
    lines.append(f"  This report was created using the ClearBlueSky Stock Scanner")
    lines.append(f"  Scanner: {GITHUB_URL}")
    lines.append("═" * 65)

    report_text = "\n".join(lines)

    # Save report
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M")
    filepath = os.path.join(reports_dir, f"{timestamp_str}_History_Report.txt")
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_text)
    except Exception:
        filepath = ""

    if progress_callback:
        progress_callback(f"History report saved: {filepath}")

    return report_text, filepath
