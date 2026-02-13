"""
ClearBlueSky - Backtest old reports through current AI pipeline.
Re-runs 5 historical .md reports through analyze_with_all_models, compares
CONSENSUS_VOTE vs realized T+1/T+3/T+5/T+10 returns.
Respects API limits: 25s delay between reports, optional vision disable.
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = Path(BASE_DIR) / "reports"
CONFIG_PATH = Path(BASE_DIR) / "user_config.json"
DELAY_BETWEEN_REPORTS_SEC = 25  # Rate limit: avoid OpenRouter/Google API throttling
MAX_REPORTS = 5


def _parse_md_frontmatter(filepath: str) -> dict | None:
    """Parse YAML frontmatter from .md file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.strip().startswith("---"):
            return None
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None
        try:
            import yaml
            return yaml.safe_load(parts[1].strip()) or {}
        except Exception:
            return None
    except Exception:
        return None


def _parse_report_timestamp(ts_str: str) -> str | None:
    """Parse timestamp to YYYY-MM-DD for signal_date."""
    if not ts_str or not isinstance(ts_str, str):
        return None
    ts_str = ts_str.strip()
    for fmt in (
        "%B %d, %Y at %I:%M:%S %p",
        "%B %d, %Y at %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %H:%M",
    ):
        try:
            dt = datetime.strptime(ts_str[:50], fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    # Extract date-like pattern
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", ts_str)
    if m:
        return m.group(0)
    return None


def _build_analysis_package_from_frontmatter(front: dict) -> dict | None:
    """Reconstruct analysis_package from report frontmatter."""
    stocks = front.get("stocks") or []
    if not stocks:
        return None
    scan_type = front.get("scan_type", "Scan")
    timestamp = front.get("timestamp", "")

    # Select directive by scan type
    from report_generator import (
        MASTER_TRADING_REPORT_DIRECTIVE,
        MOMENTUM_TREND_DIRECTIVE,
        DIP_DIRECTIVE,
    )
    st_lower = (scan_type or "").lower()
    if "velocity" in st_lower or "velocity_trend" in st_lower:
        directive = MOMENTUM_TREND_DIRECTIVE.strip()
    elif "dip" in st_lower or "emotional" in st_lower or "enhanced_dip" in st_lower:
        directive = DIP_DIRECTIVE.strip()
    else:
        directive = MASTER_TRADING_REPORT_DIRECTIVE.strip()

    tickers_list = ", ".join(s.get("ticker", "") for s in stocks if s.get("ticker"))
    watchlist = front.get("watchlist_matches") or []
    watchlist_line = f"Watchlist matches: {', '.join(watchlist)}" if watchlist else "No watchlist matches."
    data_lines = []
    for s in stocks[:20]:
        t = s.get("ticker", "")
        sc = s.get("score", "?")
        p = s.get("price", "N/A")
        ch = s.get("change", "N/A")
        sec = s.get("sector", "N/A")
        data_lines.append(f"{t}: score {sc}, ${p} ({ch}), sector {sec}")

    ai_prompt = f"""SCAN: {scan_type}
STOCKS TO ANALYZE: {tickers_list}
{watchlist_line}

DATA SUMMARY:
{chr(10).join(data_lines)}

Use the directive above. Produce output: MARKET SNAPSHOT → TIER 1/2/3 → AVOID LIST → RISK MANAGEMENT → TOP 5 PLAYS.
At the end add: CONSENSUS_VOTE: TICKER:BUY|SKIP|AVOID for each stock discussed. Example: CONSENSUS_VOTE: AAPL:BUY, NVDA:SKIP, META:AVOID
"""

    instructions = directive + "\n\n" + ai_prompt
    return {
        "scan_type": scan_type,
        "timestamp": timestamp,
        "watchlist_matches": watchlist,
        "stocks": stocks,
        "instructions": instructions,
    }


def _extract_consensus_votes(text: str) -> dict[str, str]:
    """Extract CONSENSUS_VOTE: TICKER:BUY|SKIP|AVOID from AI response."""
    out = {}
    if not text:
        return out
    m = re.search(r"CONSENSUS_VOTE:\s*([^\n]+)", text, re.IGNORECASE | re.DOTALL)
    if not m:
        return out
    raw = m.group(1).strip()
    for part in re.split(r"[,;]+", raw):
        part = part.strip()
        if ":" in part:
            ticker, vote = part.split(":", 1)
            ticker = ticker.strip().upper()
            vote = vote.strip().upper()
            if ticker and vote in ("BUY", "SKIP", "AVOID"):
                out[ticker] = vote
    return out


def _get_returns_for_ticker(ticker: str, signal_date_str: str, price_at_signal: float) -> dict[str, float | None]:
    """Fetch T+1, T+3, T+5, T+10 returns via yfinance."""
    try:
        import yfinance as yf
    except ImportError:
        return {"t1": None, "t3": None, "t5": None, "t10": None}

    try:
        signal_dt = datetime.strptime(signal_date_str[:10], "%Y-%m-%d")
    except Exception:
        return {"t1": None, "t3": None, "t5": None, "t10": None}
    if price_at_signal is None or price_at_signal <= 0:
        return {"t1": None, "t3": None, "t5": None, "t10": None}

    end_dt = signal_dt + timedelta(days=25)
    start_str = signal_dt.strftime("%Y-%m-%d")
    end_str = end_dt.strftime("%Y-%m-%d")

    hist = None
    try:
        sym = yf.Ticker(ticker)
        hist = sym.history(start=start_str, end=end_str, interval="1d", timeout=30)
    except Exception:
        pass
    if hist is None or hist.empty or len(hist) < 2:
        return {"t1": None, "t3": None, "t5": None, "t10": None}

    hist = hist.sort_index()
    closes = hist["Close"]
    mask = hist.index > signal_dt
    future_closes = closes.loc[mask].iloc[:15]
    if len(future_closes) < 2:
        return {"t1": None, "t3": None, "t5": None, "t10": None}

    def at(n):
        if len(future_closes) <= n:
            return None
        try:
            p = float(future_closes.iloc[n])
            return round((p - price_at_signal) / price_at_signal * 100, 2)
        except Exception:
            return None

    return {"t1": at(0), "t3": at(2), "t5": at(4), "t10": at(9)}


def run_backtest(progress_callback=None):
    """Run backtest on 5 reports. Returns summary dict."""
    def progress(msg):
        print(msg)
        if progress_callback:
            progress_callback(msg)

    # Load config
    config = {}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            pass

    if not (config.get("openrouter_api_key") or config.get("google_ai_api_key")):
        progress("ERROR: No OpenRouter or Google AI API key. Set in user_config.json.")
        return None

    # Find .md reports (exclude backtest_*.md)
    md_files = sorted(REPORTS_DIR.glob("*.md"))
    md_files = [f for f in md_files if "backtest_" not in f.name.lower()]
    if not md_files:
        progress("No scan reports found in reports/")
        return None

    # Take 5 most recent by mtime
    md_files = sorted(md_files, key=lambda p: p.stat().st_mtime, reverse=True)[:MAX_REPORTS]
    progress(f"Backtesting {len(md_files)} reports: {[f.name for f in md_files]}")

    results = []
    for i, md_path in enumerate(md_files):
        progress(f"\n--- Report {i+1}/{len(md_files)}: {md_path.name} ---")
        front = _parse_md_frontmatter(str(md_path))
        if not front:
            progress(f"  Skip: no valid frontmatter")
            continue

        pkg = _build_analysis_package_from_frontmatter(front)
        if not pkg:
            progress(f"  Skip: no stocks in package")
            continue

        signal_date = _parse_report_timestamp(pkg.get("timestamp", ""))
        if not signal_date:
            progress(f"  Skip: could not parse timestamp")
            continue

        # Rate limit: wait before AI call (except first)
        if i > 0:
            import time
            progress(f"  Waiting {DELAY_BETWEEN_REPORTS_SEC}s (API rate limit)...")
            time.sleep(DELAY_BETWEEN_REPORTS_SEC)

        # Run AI pipeline (disable vision for backtest to reduce load)
        backtest_config = dict(config)
        backtest_config["use_vision_charts"] = False

        system_prompt = (pkg.get("instructions") or "").strip() or "Analyze the stock scan and produce CONSENSUS_VOTE."
        content = json.dumps(pkg, indent=2)

        progress("  Calling AI (6 OpenRouter + 1 Google)...")
        try:
            from openrouter_client import analyze_with_all_models
            ai_response = analyze_with_all_models(
                backtest_config,
                system_prompt,
                content,
                progress_callback=lambda m: progress(f"    {m}"),
                image_base64_list=None,
            ) or ""
        except Exception as e:
            progress(f"  AI ERROR: {e}")
            continue

        votes = _extract_consensus_votes(ai_response)
        if not votes:
            progress("  No CONSENSUS_VOTE found in response")
            votes = {}

        # Compute realized returns for each ticker
        ticker_results = []
        for s in pkg.get("stocks", [])[:15]:
            ticker = (s.get("ticker") or "").strip().upper()
            if not ticker:
                continue
            price_raw = s.get("price")
            try:
                price = float(str(price_raw).replace("$", "").replace(",", "")) if price_raw not in (None, "", "N/A") else None
            except (TypeError, ValueError):
                price = None
            vote = votes.get(ticker, "SKIP")
            rets = _get_returns_for_ticker(ticker, signal_date, price) if price else {"t1": None, "t3": None, "t5": None, "t10": None}
            ticker_results.append({
                "ticker": ticker,
                "vote": vote,
                "price": price,
                "ret_t1": rets["t1"],
                "ret_t3": rets["t3"],
                "ret_t5": rets["t5"],
                "ret_t10": rets["t10"],
            })

        # Aggregate accuracy
        buy_wins_t5 = sum(1 for r in ticker_results if r["vote"] == "BUY" and r["ret_t5"] is not None and r["ret_t5"] > 0)
        buy_total_t5 = sum(1 for r in ticker_results if r["vote"] == "BUY" and r["ret_t5"] is not None)
        avoid_wins_t5 = sum(1 for r in ticker_results if r["vote"] == "AVOID" and r["ret_t5"] is not None and r["ret_t5"] <= 0)
        avoid_total_t5 = sum(1 for r in ticker_results if r["vote"] == "AVOID" and r["ret_t5"] is not None)

        report_summary = {
            "report": md_path.name,
            "scan_type": pkg.get("scan_type", ""),
            "signal_date": signal_date,
            "tickers": len(ticker_results),
            "votes": dict(votes),
            "buy_win_rate_t5": (buy_wins_t5 / buy_total_t5 * 100) if buy_total_t5 else None,
            "buy_total_t5": buy_total_t5,
            "avoid_win_rate_t5": (avoid_wins_t5 / avoid_total_t5 * 100) if avoid_total_t5 else None,
            "avoid_total_t5": avoid_total_t5,
            "details": ticker_results,
        }
        results.append(report_summary)
        progress(f"  BUY T+5 win rate: {report_summary['buy_win_rate_t5']:.1f}% ({buy_wins_t5}/{buy_total_t5})" if buy_total_t5 else "  No BUY votes with T+5 data")
        progress(f"  AVOID T+5 correct: {report_summary['avoid_win_rate_t5']:.1f}% ({avoid_wins_t5}/{avoid_total_t5})" if avoid_total_t5 else "")

    # Overall summary
    all_buy = sum(r["buy_total_t5"] or 0 for r in results)
    all_buy_wins = sum(
        sum(1 for d in r["details"] if d["vote"] == "BUY" and d["ret_t5"] is not None and d["ret_t5"] > 0)
        for r in results
    )
    summary = {
        "reports_run": len(results),
        "overall_buy_win_rate_t5": (all_buy_wins / all_buy * 100) if all_buy else None,
        "reports": results,
    }
    return summary


def main():
    os.chdir(BASE_DIR)
    sys.path.insert(0, BASE_DIR)
    print("=" * 60)
    print("AI Report Backtest — 5 reports through current pipeline")
    print("=" * 60)
    summary = run_backtest()
    if not summary:
        return 1

    out_path = REPORTS_DIR / "backtest_ai_summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary saved to: {out_path}")

    wr = summary.get("overall_buy_win_rate_t5")
    if wr is not None:
        print(f"\nOverall BUY T+5 win rate: {wr:.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
