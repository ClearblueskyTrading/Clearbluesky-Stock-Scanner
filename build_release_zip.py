#!/usr/bin/env python3
"""
Build a clean release zip for ClearBlueSky v7.0 (and future 7.1, 7.2).
Uses git ls-files so zip = repo contents only (no Cursor project filesystem pollution).
Excludes user data, Cursor/trading docs, etc.
Run from repo root: python build_release_zip.py
Output: ClearBlueSky-v7.0.zip (or version from app/app.py VERSION)
"""

import os
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = ROOT / "app"

# Exclude patterns (relative to root or app)
EXCLUDE_DIRS = {
    "__pycache__",
    ".git",
    ".cursor",
    "update_backups",
    "reports",
    "scanner_output",
    "rag_store",
    "scans",
    "ClearBlueSkyWin",
    "backup-v6.4",
    "scripts",  # Cursor agent tooling — scanner-only on GitHub
}
EXCLUDE_FILES = {
    "user_config.json",      # user API keys, preferences
    "mcp.json",             # user MCP config
    ".env", ".env.local",  # env vars, API keys
    "error_log.txt",
    "update_backup_manifest.json",
    "scanner_presets_export.json",   # user exports
    "release_notes_v7.md",
    "backtest_signals.db",
    # Old release notes (only RELEASE_v7.90 kept)
    "CURSOR_RAG_KNOWLEDGE_ARCHITECTURE.md",
    # Cursor project only — not scanner release
    "CURSOR_AI_GUIDE.md",
    "CURSOR_AGENT_SYSTEM.md",
    "CURSOR_OPENROUTER_SETUP.md",
    "DESKTOP_AGENT_PANEL.md",
    # Trading (Cursor project only)
    "alpaca_trades.py",
    "paper_trading_manager.py",
    "alpaca_swing_dip_strategy.py",
    "PaperTradingManager.bat",
    # Cursor/trading docs in repo
    "ALPACA_PAPER_TRADE_FEATURE_PLAN.md",
    "MARKET_STRATEGY_DRAFT.md",
    "NON_DAYTRADE_STRATEGY.md",
    "mcp.json.example",
}
EXCLUDE_SUFFIXES = (".pyc", ".pyo", ".zip")
EXCLUDE_PATTERNS = [
    re.compile(r"ClearBlueSky-\d+\.\d+\.zip", re.I),
    re.compile(r".*_Scan_Report_.*\.pdf", re.I),
    re.compile(r"^_test_", re.I),
    re.compile(r"\.env\.", re.I),  # .env.local, .env.prod, etc.
    re.compile(r"docs[/\\]docs[/\\]", re.I),  # nested docs/docs duplicate
    re.compile(r"docs[/\\]strategy[/\\]", re.I),  # trading strategy docs
    re.compile(r"docs[/\\]CURSOR_AGENT", re.I),  # Cursor agent spec
]


def should_exclude(rel_path: str, is_dir: bool) -> bool:
    parts = Path(rel_path).parts
    if any(p in EXCLUDE_DIRS for p in parts):
        return True
    if not is_dir:
        name = parts[-1] if parts else ""
        if name in EXCLUDE_FILES:
            return True
        if name.endswith(EXCLUDE_SUFFIXES):
            return True
        for pat in EXCLUDE_PATTERNS:
            if pat.search(rel_path.replace("\\", "/")):
                return True
    return False


def get_version() -> str:
    try:
        with open(APP / "app.py", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("VERSION"):
                    # VERSION = "7.0"
                    m = re.search(r'["\']([\d.]+)["\']', line)
                    if m:
                        return m.group(1)
    except Exception:
        pass
    return "7.0"


def main():
    version = get_version()
    out_name = f"ClearBlueSky-v{version}.zip"
    out_path = ROOT / out_name

    # Use git ls-files so zip = repo only (no filesystem pollution from Cursor project)
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            raise RuntimeError("git ls-files failed")
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except Exception as e:
        raise SystemExit(f"Build requires git. Run from repo root. Error: {e}")

    if not files:
        raise SystemExit("No files from git ls-files. Run from repo root.")

    # Remove old zip if present
    if out_path.exists():
        out_path.unlink()

    added = 0
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in files:
            rel = rel.replace("/", os.sep)
            if should_exclude(rel, False):
                continue
            if rel == "build_release_zip.py":
                continue
            full = ROOT / rel
            if not full.is_file():
                continue
            zf.write(full, rel)
            added += 1

    print(f"Created {out_path} with {added} files (version {version}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
