#!/usr/bin/env python3
"""
ClearBlueSky CLI – for AI / automation.
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
    "velocity_trend_growth": "Velocity Trend Growth",
    "swing": "Swing",
    "watchlist": "Watchlist",
}

# Scan types that use index (S&P 500 + ETFs)
INDEX_SCANS = {"velocity_trend_growth", "swing"}


def _progress(msg: str) -> None:
    print(f"   {msg}", flush=True)


def _is_rate_limit(err: Exception) -> bool:
    s = str(err).lower()
    return "429" in s or "rate" in s or "rate limit" in s


def _is_watchlist_all_mode(filter_value) -> bool:
    """Accept both stored value ('all') and display text ('All tickers')."""
    return str(filter_value or "down_pct").strip().lower() in ("all", "all tickers")


def _get_min_score(config: dict, scan_key: str, scan_type_display: str) -> int:
    """
    Keep CLI min-score behavior aligned with GUI/report path in app.py.
    Supports legacy keys for backward compatibility.
    """
    zero_min_scans = {"watchlist", "velocity_trend_growth"}
    default_min = 0 if scan_key in zero_min_scans else 65

    if scan_key == "swing":
        raw = config.get("emotional_min_score", config.get("swing_min_score", default_min))
    else:
        normalized_key = f"{scan_key}_min_score"
        legacy_display_key = f"{scan_type_display.lower()}_min_score"
        raw = config.get(normalized_key, config.get(legacy_display_key, default_min))

    try:
        return int(raw)
    except (TypeError, ValueError):
        return default_min


def _generate_report_cli(results, scan_key: str, scan_type_display: str, config: dict, index: str | None, progress_fn) -> str | None:
    """Generate single .md report. Returns path to .md file or None."""
    from report_generator import HTMLReportGenerator, build_markdown_report

    min_score = _get_min_score(config, scan_key, scan_type_display)
    reports_dir = config.get("reports_folder") or DEFAULT_REPORTS_DIR
    if not os.path.isabs(reports_dir):
        reports_dir = os.path.join(APP_DIR, reports_dir)
    reports_dir = os.path.abspath(reports_dir)
    os.makedirs(reports_dir, exist_ok=True)

    watchlist = config.get("watchlist") or []
    watchlist_set = set(str(t).upper().strip() for t in watchlist if t)

    gen = HTMLReportGenerator(save_dir=reports_dir)
    base_path, report_text, analysis_package = gen.generate_combined_report_pdf(
        results,
        scan_type_display,
        min_score,
        progress_fn,
        watchlist_tickers=watchlist_set,
        config=config,
        index=index,
    )
    if not base_path:
        return None

    ai_response = ""
    if config.get("openrouter_api_key") and analysis_package:
        try:
            from openrouter_client import analyze_with_all_models
            progress_fn("Sending to OpenRouter (3 models)...")
            system_prompt = (analysis_package.get("instructions") or "").strip() or "You are a professional stock analyst. Analyze the JSON package and produce the report in the required format."
            if config.get("rag_enabled") and config.get("rag_books_folder"):
                try:
                    from rag_engine import get_rag_context_for_scan
                    rag_ctx = get_rag_context_for_scan(scan_type_display or "Scan", k=5)
                    if rag_ctx:
                        system_prompt = system_prompt + "\n\n" + rag_ctx
                except Exception:
                    pass
            content = __import__("json").dumps(analysis_package, indent=2)
            image_list = None
            ai_response = analyze_with_all_models(config, system_prompt, content, progress_callback=progress_fn, image_base64_list=image_list) or ""
            if ai_response:
                ai_response = "Consensus from 3 AI models (Llama, OpenAI, DeepSeek).\n\n" + ai_response
        except Exception as e:
            progress_fn("AI analysis failed: " + str(e))
            ai_response = f"AI analysis failed: {e}\n\nSet OpenRouter API key for analysis."
    else:
        ai_response = ""

    md_content = build_markdown_report(analysis_package, report_text, ai_response)
    md_path = base_path + ".md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    progress_fn("Report saved: " + md_path)
    return md_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ClearBlueSky CLI – run scans for AI/automation. Exit 0 = success, 1 = failure."
    )
    parser.add_argument(
        "--scan",
        required=True,
        choices=[
            "velocity_trend_growth",
            "swing",
            "watchlist",
        ],
        help="Scan type to run",
    )
    parser.add_argument(
        "--watchlist-file",
        metavar="PATH",
        help="Optional: text file with one ticker per line (overrides config watchlist for this run)",
    )
    parser.add_argument(
        "--index",
        choices=["sp500", "etfs"],
        help="Universe override: sp500 or etfs (for velocity_trend_growth, swing). Overrides user_config.json",
    )
    parser.add_argument(
        "--reports-dir",
        metavar="PATH",
        help="Override reports output directory (default: reports/ under app folder or user_config)",
    )
    args = parser.parse_args()

    from scan_settings import load_config
    config = load_config()

    config = dict(config) if config else {}
    if args.index and args.scan in INDEX_SCANS:
        config["scan_index"] = args.index
        _progress(f"Universe override: {args.index}")
    if args.reports_dir:
        config["reports_folder"] = os.path.abspath(args.reports_dir)
        _progress(f"Reports dir: {config['reports_folder']}")

    if args.watchlist_file:
        path = os.path.abspath(args.watchlist_file)
        if not os.path.isfile(path):
            print(f"[FAIL] Watchlist file not found: {path}", file=sys.stderr)
            return 1
        with open(path, "r", encoding="utf-8") as f:
            tickers = [line.strip().upper() for line in f if line.strip()]
        config["watchlist"] = tickers
        _progress(f"Using watchlist from file: {len(tickers)} tickers")

    scan_key = args.scan
    index = None
    if scan_key in INDEX_SCANS:
        idx_raw = config.get("scan_index", "sp500")
        index = idx_raw if idx_raw in ("sp500", "etfs", "sp500_etfs") else "sp500"
    display_name = SCAN_DISPLAY_NAMES[scan_key]
    idx_label = "S&P 500" if index == "sp500" else "ETFs" if index == "etfs" else "S&P 500 + ETFs"
    print(f"Starting {display_name} scan ({idx_label})...", flush=True)

    try:
        results = None

        if scan_key == "swing":
            from emotional_dip_scanner import run_emotional_dip_scan
            results = run_emotional_dip_scan(progress_callback=_progress, index=index)

        elif scan_key == "velocity_trend_growth":
            from velocity_trend_growth import run_velocity_trend_growth_scan
            cfg = config or {}
            trend_days = int(cfg.get("vtg_trend_days", 20) or 20)
            target_pct = float(cfg.get("vtg_target_return_pct", 5) or 5)
            risk_pct = float(cfg.get("vtg_risk_pct", 30) or 30)
            max_tickers = int(cfg.get("vtg_max_tickers", 20) or 20)
            min_price = float(cfg.get("vtg_min_price", 25) or 25)
            max_price = float(cfg.get("vtg_max_price", 600) or 600)
            min_vol_k = int(cfg.get("vtg_min_volume", 100) or 100)
            min_volume = min_vol_k * 1000
            require_beats_spy = bool(cfg.get("vtg_require_beats_spy", False))
            require_volume_confirm = bool(cfg.get("vtg_require_volume_confirm", False))
            require_above_sma200 = bool(cfg.get("vtg_require_above_sma200", True))
            require_ma_stack = bool(cfg.get("vtg_require_ma_stack", False))
            rsi_min = int(cfg.get("vtg_rsi_min", 0) or 0)
            rsi_max = int(cfg.get("vtg_rsi_max", 100) or 100)
            results = run_velocity_trend_growth_scan(
                progress_callback=_progress,
                index=index,
                trend_days=trend_days,
                target_return_pct=target_pct,
                risk_pct=risk_pct,
                max_tickers=max_tickers,
                min_price=min_price,
                max_price=max_price,
                require_beats_spy=require_beats_spy,
                min_volume=min_volume,
                require_volume_confirm=require_volume_confirm,
                require_above_sma200=require_above_sma200,
                require_ma_stack=require_ma_stack,
                rsi_min=rsi_min,
                rsi_max=rsi_max,
            )

        elif scan_key == "watchlist":
            from watchlist_scanner import run_watchlist_scan, run_watchlist_tickers_scan
            use_all = _is_watchlist_all_mode(config.get("watchlist_filter"))
            results = run_watchlist_tickers_scan(progress_callback=_progress, config=config) if use_all else run_watchlist_scan(progress_callback=_progress, config=config)

        if not results or len(results) == 0:
            print(f"   No results from {display_name} scan.", flush=True)
            print(f"[OK] {display_name} scan completed (no candidates). Check reports folder if previous runs wrote files.", flush=True)
            return 0

        _progress(f"Generating report ({len(results)} candidates)...")
        base_path = _generate_report_cli(results, scan_key, display_name, config, index, _progress)
        if base_path:
            bn = os.path.basename(base_path)
            print(f"[OK] Scan complete: reports/{bn}", flush=True)
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
