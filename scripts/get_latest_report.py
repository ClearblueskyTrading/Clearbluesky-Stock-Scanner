#!/usr/bin/env python3
"""Print path to the latest scan report JSON. Use when user asks for AI report from scan files."""
import json
import os
import glob
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent / "app"
CONFIG_FILE = APP_DIR / "user_config.json"
DEFAULT_REPORTS = APP_DIR / "reports"


def get_reports_dir():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                cfg = json.load(f)
            raw = (cfg.get("reports_folder") or "").strip()
            if raw:
                p = Path(raw)
                if not p.is_absolute():
                    p = APP_DIR / raw
                return p.resolve()
        except Exception:
            pass
    return DEFAULT_REPORTS.resolve()


def main():
    reports_dir = get_reports_dir()
    if not reports_dir.exists():
        print(reports_dir, end="")
        return

    pattern = str(reports_dir / "*_Scan_*.json")
    files = glob.glob(pattern)
    if not files:
        print(reports_dir, end="")
        return

    latest = max(files, key=os.path.getmtime)
    print(latest, end="")


if __name__ == "__main__":
    main()
