#!/usr/bin/env python3
"""
Clean install test — runs a scan with NO API keys (blank config).
Simulates a fresh install to verify everything works without Finviz/OpenRouter/Alpha Vantage/Alpaca.
"""
import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"


def main():
    # 1. Create temp directory (simulated clean install)
    with tempfile.TemporaryDirectory(prefix="cbs_clean_test_") as tmpdir:
        tmp = Path(tmpdir)
        print(f"[1] Temp dir: {tmp}")

        # 2. Copy app folder to temp (we need the full app)
        app_dest = tmp / "app"
        app_dest.mkdir()
        for item in APP.iterdir():
            if item.name in ("__pycache__", "reports", "scanner_output", "rag_store", "update_backups"):
                continue
            if item.is_file():
                shutil.copy2(item, app_dest / item.name)
            elif item.is_dir():
                shutil.copytree(item, app_dest / item.name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

        # 3. Blank config (no API keys)
        config_path = app_dest / "user_config.json"
        example = APP / "user_config.json.example"
        if example.exists():
            with open(example, "r", encoding="utf-8") as f:
                raw = f.read()
            # Remove _comment so it's valid JSON for loading
            import json
            data = json.loads(raw)
            data.pop("_comment", None)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print("[2] Blank config (no API keys) written")
        else:
            print("[2] No user_config.json.example — creating minimal blank config")
            cfg = {
                "finviz_api_key": "",
                "openrouter_api_key": "",
                "alpha_vantage_api_key": "",
                "alpaca_api_key": "",
                "alpaca_secret_key": "",
                "trend_min_score": 70,
                "swing_min_score": 60,
                "watchlist_pct_down_from_open": 5,
            }
            import json
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)

        # 4. Run scan from temp app dir (etfs = smaller universe, faster)
        print("[3] Running scan (trend, etfs — small universe)...")
        result = subprocess.run(
            [sys.executable, "scanner_cli.py", "--scan", "trend", "--index", "etfs"],
            cwd=str(app_dest),
            timeout=300,
            capture_output=True,
            text=True,
        )

        print(f"[4] Exit code: {result.returncode}")
        if result.stdout:
            for line in result.stdout.strip().split("\n")[-15:]:
                print("  ", line)
        if result.returncode != 0 and result.stderr:
            print("STDERR:")
            print(result.stderr[:1000])

        # 5. Check for report
        reports = list((app_dest / "reports").glob("*.pdf")) if (app_dest / "reports").exists() else []
        print(f"[5] PDF reports generated: {len(reports)}")

        if result.returncode == 0 and len(reports) >= 1:
            print("\nCLEAN INSTALL TEST: PASSED")
            return 0
        else:
            print("\nCLEAN INSTALL TEST: FAILED")
            return 1


if __name__ == "__main__":
    sys.exit(main())
