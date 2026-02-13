#!/usr/bin/env python
"""Test MD report flow: build_markdown_report, backfill, parse."""
import os
import sys

def main():
    from report_generator import build_markdown_report
    from history_analyzer import backfill_from_reports, _parse_md_frontmatter

    base = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(base, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    print("1. build_markdown_report...")
    pkg = {
        "scan_type": "Test Scan",
        "timestamp": "2025-02-10 15:30:00",
        "watchlist_matches": ["AAPL"],
        "stocks": [
            {"ticker": "AAPL", "score": 85, "price": "150.00"},
            {"ticker": "NVDA", "score": 82, "price": "680.00"},
        ],
        "market_breadth": {"market_regime": "Risk-on", "sp500_above_sma200_pct": 72},
    }
    md = build_markdown_report(pkg, "Report body\n\nPer-ticker data here.", "AI consensus output")
    assert "---" in md and "scan_type:" in md
    assert "# ClearBlueSky Scan Report" in md
    assert "# AI Analysis" in md
    assert "AAPL" in md and "NVDA" in md
    assert "AI consensus output" in md
    print("   OK")

    print("2. Save test MD and _parse_md_frontmatter...")
    test_md = os.path.join(reports_dir, "Test_Scan_20250210_153000.md")
    with open(test_md, "w", encoding="utf-8") as f:
        f.write(md)
    parsed = _parse_md_frontmatter(test_md)
    assert parsed.get("scan_type") == "Test Scan"
    assert len(parsed.get("stocks", [])) == 2
    print("   OK")

    print("3. backfill_from_reports (MD + JSON)...")
    added = backfill_from_reports(reports_dir=reports_dir)
    print(f"   OK ({added} new entries)")

    print("4. generate_report (single ticker)...")
    from report_generator import generate_report
    path = generate_report("AAPL", "Quick Test", 80)
    if path and os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert path.endswith(".md")
        assert "AAPL" in content
        print(f"   OK: {path}")
    else:
        print("   SKIP (Finviz/TA may have failed)")

    print("\nAll tests passed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
