#!/usr/bin/env python3
"""
ClearBlueSky CLI – for Claude / automation.
Runs scans without the GUI; exit 0 on success, 1 on failure.
No retries on rate limit (429).
"""
import argparse
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Default reports dir (same as app.py)
APP_DIR = BASE_DIR
DEFAULT_REPORTS_DIR = os.path.join(APP_DIR, "reports")

# Scan type -> display name for report generator
SCAN_DISPLAY_NAMES = {
    "trend": "Trend",
    "swing": "Swing",
    "velocity": "Velocity Barbell",
    "premarket": "Premarket",
    "insider": "Insider",
    "watchlist": "Watchlist",
}

# Scan types that use index (sp500 / russell2000 / etfs)
INDEX_SCANS = {"trend", "swing", "premarket"}


def _progress(msg: str) -> None:
    print(f"   {msg}", flush=True)


def _is_rate_limit(err: Exception) -> bool:
    s = str(err).lower()
    return "429" in s or "rate" in s or "rate limit" in s


def _generate_report_cli(results, scan_type_display: str, config: dict, index: str | None, progress_fn) -> str | None:
    """Generate PDF + JSON + optional _ai.txt. Returns base path (no extension) or None."""
    from report_generator import HTMLReportGenerator

    zero_min = ("Watchlist", "Watchlist 3pm", "Watchlist - All tickers", "Insider", "Velocity Barbell")
    default_min = 0 if scan_type_display in zero_min else 65
    min_score = int(config.get(f"{scan_type_display.lower()}_min_score", default_min))
    reports_dir = config.get("reports_folder") or DEFAULT_REPORTS_DIR
    reports_dir = os.path.abspath(reports_dir)
    os.makedirs(reports_dir, exist_ok=True)

    watchlist = config.get("watchlist") or []
    watchlist_set = set(str(t).upper().strip() for t in watchlist if t)

    gen = HTMLReportGenerator(save_dir=reports_dir)
    path, analysis_text, analysis_package = gen.generate_combined_report_pdf(
        results,
        scan_type_display,
        min_score,
        progress_fn,
        watchlist_tickers=watchlist_set,
        config=config,
        index=index,
    )
    if not path:
        return None

    base = path[:-4] if path.lower().endswith(".pdf") else path

    # Optional: OpenRouter AI analysis (no browser)
    if config.get("openrouter_api_key") and analysis_package:
        try:
            from openrouter_client import analyze_with_config
            progress_fn("Sending to OpenRouter for AI analysis...")
            system_prompt = (
                "You are a professional stock analyst. You are receiving a structured JSON analysis package. "
                "For each stock provide: YOUR SCORE (1-100), chart/TA summary, news check, RECOMMENDATION (BUY/HOLD/PASS), "
                "and if BUY: Entry, Stop, Target, position size. End with TOP PICKS, AVOID LIST, and RISK MANAGEMENT notes."
            )
            if config.get("rag_enabled") and config.get("rag_books_folder"):
                try:
                    from rag_engine import get_rag_context_for_scan
                    rag_ctx = get_rag_context_for_scan(scan_type_display or "Scan", k=5)
                    if rag_ctx:
                        system_prompt = system_prompt + "\n\n" + rag_ctx
                except Exception:
                    pass
            content = __import__("json").dumps(analysis_package, indent=2)
            ai_response = analyze_with_config(config, system_prompt, content, image_base64_list=None)
            ai_path = base + "_ai.txt"
            if ai_response:
                with open(ai_path, "w", encoding="utf-8") as f:
                    f.write(ai_response)
                progress_fn("AI analysis saved to " + ai_path)
            else:
                fallback = (analysis_package.get("instructions") or "") if isinstance(analysis_package, dict) else ""
                with open(ai_path, "w", encoding="utf-8") as f:
                    f.write("AI returned empty. Paste the report JSON into your preferred AI.\n\n---\n\n" + fallback)
                progress_fn("AI empty; instructions written to " + ai_path)
        except Exception as e:
            progress_fn("AI analysis failed: " + str(e))
            try:
                fallback = (analysis_package.get("instructions") or "") if isinstance(analysis_package, dict) else ""
                with open(base + "_ai.txt", "w", encoding="utf-8") as f:
                    f.write(f"AI analysis failed: {e}\n\n---\n\n{fallback}")
            except Exception:
                pass  # analysis_package may be undefined

    return base


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ClearBlueSky CLI – run scans for Claude/automation. Exit 0 = success, 1 = failure."
    )
    parser.add_argument(
        "--scan",
        required=True,
        choices=[
            "trend",
            "swing",
            "velocity",
            "premarket",
            "insider",
            "watchlist",
        ],
        help="Scan type to run",
    )
    parser.add_argument(
        "--index",
        choices=["sp500", "russell2000", "etfs"],
        default="sp500",
        help="Index for trend/swing/premarket (default: sp500)",
    )
    parser.add_argument(
        "--watchlist-file",
        metavar="PATH",
        help="Optional: text file with one ticker per line (overrides config watchlist for this run)",
    )
    args = parser.parse_args()

    from scan_settings import load_config
    config = load_config()

    if args.watchlist_file:
        path = os.path.abspath(args.watchlist_file)
        if not os.path.isfile(path):
            print(f"[FAIL] Watchlist file not found: {path}", file=sys.stderr)
            return 1
        with open(path, "r", encoding="utf-8") as f:
            tickers = [line.strip().upper() for line in f if line.strip()]
        config = dict(config) if config else {}
        config["watchlist"] = tickers
        _progress(f"Using watchlist from file: {len(tickers)} tickers")

    scan_key = args.scan
    index = args.index if scan_key in INDEX_SCANS else None
    display_name = SCAN_DISPLAY_NAMES[scan_key]

    print(f"Starting {display_name} scan...", flush=True)
    if index:
        print(f"   Index: {index}", flush=True)

    try:
        results = None

        if scan_key == "trend":
            from trend_scan_v2 import trend_scan
            _progress("Fetching overview data (this may take a minute)...")
            df = trend_scan(progress_callback=_progress, index=index)
            results = df.to_dict("records") if df is not None and len(df) > 0 else None

        elif scan_key == "swing":
            from emotional_dip_scanner import run_emotional_dip_scan
            results = run_emotional_dip_scan(progress_callback=_progress, index=index)

        elif scan_key == "velocity":
            from velocity_leveraged_scanner import run_velocity_leveraged_scan
            results = run_velocity_leveraged_scan(progress_callback=_progress, config=config)

        elif scan_key == "premarket":
            from premarket_volume_scanner import run_premarket_volume_scan
            results = run_premarket_volume_scan(progress_callback=_progress, index=index)

        elif scan_key == "insider":
            from insider_scanner import run_insider_scan
            results = run_insider_scan(progress_callback=_progress, config=config)

        elif scan_key == "watchlist":
            from watchlist_scanner import run_watchlist_scan, run_watchlist_tickers_scan
            use_all = (config.get("watchlist_filter") or "down_pct").strip().lower() == "all"
            results = run_watchlist_tickers_scan(progress_callback=_progress, config=config) if use_all else run_watchlist_scan(progress_callback=_progress, config=config)

        if not results or len(results) == 0:
            print(f"   No results from {display_name} scan.", flush=True)
            print(f"[OK] {display_name} scan completed (no candidates). Check reports folder if previous runs wrote files.", flush=True)
            return 0

        _progress(f"Generating PDF report ({len(results)} candidates)...")
        base_path = _generate_report_cli(results, display_name, config, index, _progress)
        if base_path:
            # Predictable output for Claude: reports/<basename>.* (ASCII so Windows console works)
            bn = os.path.basename(base_path)
            print(f"[OK] Scan complete: reports/{bn}.*", flush=True)
        else:
            print("[OK] Scan complete (no report: no stocks above min score).", flush=True)
        return 0

    except Exception as e:
        if _is_rate_limit(e):
            print(f"[FAIL] Rate limit hit: {e}", file=sys.stderr)
        else:
            print(f"[FAIL] Scan failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
