#!/usr/bin/env python3
"""
Build a clean release zip for ClearBlueSky v7.0 (and future 7.1, 7.2).
Excludes user data, __pycache__, reports, update_backups, etc.
Run from repo root: python build_release_zip.py
Output: ClearBlueSky-v7.0.zip (or version from app/app.py VERSION)
"""

import os
import re
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
    "GITHUB_PUSH.md",
    "TESTING_v7.0.md",
    "NEXT_RELEASE.md",
    # Old release notes (keep only last 2 versions: 7.89, 7.90)
    "RELEASE_v6.2.md", "RELEASE_v6.3.md", "RELEASE_v6.4.md", "RELEASE_v6.5.md",
    "RELEASE_v7.0.md", "RELEASE_v7.1.md", "RELEASE_v7.2.md", "RELEASE_v7.3.md",
    "RELEASE_v7.4.md", "RELEASE_v7.5.md", "RELEASE_v7.6.md", "RELEASE_v7.7.md",
    "RELEASE_v7.8.md", "RELEASE_v7.81.md", "RELEASE_v7.82.md", "RELEASE_v7.83.md",
    "RELEASE_v7.84.md", "RELEASE_v7.85.md", "RELEASE_v7.86.md", "RELEASE_v7.87.md", "RELEASE_v7.88.md",
    "CURSOR_RAG_KNOWLEDGE_ARCHITECTURE.md",
}
EXCLUDE_SUFFIXES = (".pyc", ".pyo", ".zip")
EXCLUDE_PATTERNS = [
    re.compile(r"ClearBlueSky-\d+\.\d+\.zip", re.I),
    re.compile(r".*_Scan_Report_.*\.pdf", re.I),
    re.compile(r"^_test_", re.I),
    re.compile(r"\.env\.", re.I),  # .env.local, .env.prod, etc.
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
            if pat.search(name):
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

    # Remove old zip if present
    if out_path.exists():
        out_path.unlink()

    added = 0
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for base in [ROOT]:
            for dirpath, dirnames, filenames in os.walk(base):
                # Don't descend into excluded dirs
                dirnames[:] = [d for d in dirnames if not should_exclude(os.path.relpath(os.path.join(dirpath, d), ROOT), True)]
                for f in filenames:
                    full = os.path.join(dirpath, f)
                    try:
                        rel = os.path.relpath(full, ROOT)
                    except ValueError:
                        continue
                    if rel.startswith("..") or "\\.." in rel or "/.." in rel:
                        continue
                    if should_exclude(rel, False):
                        continue
                    # Skip build script itself in zip if we're at root
                    if rel == "build_release_zip.py":
                        continue
                    zf.write(full, rel)
                    added += 1

    print(f"Created {out_path} with {added} files (version {version}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
