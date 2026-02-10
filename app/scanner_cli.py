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
    "velocity_trend_growth": "Velocity Trend Growth",
    "swing": "Swing",
    "premarket": "Premarket",
    "watchlist": "Watchlist",
}

# Scan types that use index (S&P 500 + ETFs)
INDEX_SCANS = {"velocity_trend_growth", "swing", "premarket"}


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
    zero_min_scans = {"watchlist", "premarket", "velocity_trend_growth"}
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
    """Generate PDF + JSON + optional _ai.txt. Returns base path (no extension) or None."""
    from report_generator import HTMLReportGenerator

    min_score = _get_min_score(config, scan_key, scan_type_display)
    reports_dir = config.get("reports_folder") or DEFAULT_REPORTS_DIR
    if not os.path.isabs(reports_dir):
        reports_dir = os.path.join(APP_DIR, reports_dir)
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
            ai_response = analyze_with_config(config, system_prompt, content, image_base64_list=None)
            ai_path = base + "_ai.txt"
            from report_generator import SCANNER_GITHUB_URL
            _ai_header = f"Created using ClearBlueSky Stock Scanner. Scanner: {SCANNER_GITHUB_URL}\n\nPrompt for AI (when using this file alone or with the matching PDF/JSON): Follow the instructions in the JSON. Produce output in the required format: MARKET SNAPSHOT, TIER 1/2/3 picks, AVOID LIST, RISK MANAGEMENT, KEY INSIGHT, TOP 5 PLAYS. Include news/catalysts for each pick.\n\n---\n\n"
            if ai_response:
                with open(ai_path, "w", encoding="utf-8") as f:
                    f.write(_ai_header + ai_response)
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
            "velocity_trend_growth",
            "swing",
            "premarket",
            "watchlist",
        ],
        help="Scan type to run",
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
    index = "sp500_etfs" if scan_key in INDEX_SCANS else None
    display_name = SCAN_DISPLAY_NAMES[scan_key]

    print(f"Starting {display_name} scan (S&P 500 + ETFs)...", flush=True)

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
                require_ma_stack=require_ma_stack,
                rsi_min=rsi_min,
                rsi_max=rsi_max,
            )

        elif scan_key == "premarket":
            from premarket_volume_scanner import run_premarket_volume_scan
            results = run_premarket_volume_scan(progress_callback=_progress, index=index)
            # Merge velocity premarket results if available
            try:
                from velocity_scanner import run_premarket_scan as _vpm
                vpm = _vpm(progress_callback=_progress, index=index)
                if vpm:
                    seen = {r.get("ticker") for r in (results or [])}
                    for r in vpm:
                        if r.get("ticker") not in seen:
                            results = (results or []) + [r]
            except Exception:
                pass

        elif scan_key == "watchlist":
            from watchlist_scanner import run_watchlist_scan, run_watchlist_tickers_scan
            use_all = _is_watchlist_all_mode(config.get("watchlist_filter"))
            results = run_watchlist_tickers_scan(progress_callback=_progress, config=config) if use_all else run_watchlist_scan(progress_callback=_progress, config=config)

        if not results or len(results) == 0:
            print(f"   No results from {display_name} scan.", flush=True)
            print(f"[OK] {display_name} scan completed (no candidates). Check reports folder if previous runs wrote files.", flush=True)
            return 0

        _progress(f"Generating PDF report ({len(results)} candidates)...")
        base_path = _generate_report_cli(results, scan_key, display_name, config, index, _progress)
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
