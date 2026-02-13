# ============================================================
# ClearBlueSky - Updater (backup, update, rollback)
# ============================================================
# Update preserves existing user_config.json. Rollback restores
# code from backup but keeps current user_config.json (user choice).

import os
import json
import zipfile
import shutil
import tempfile
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "user_config.json")
MANIFEST_FILE = os.path.join(BASE_DIR, "update_backup_manifest.json")
BACKUP_DIR = os.path.join(BASE_DIR, "update_backups")
import hashlib

# Paths we never overwrite (relative to app dir) - keep existing user config
PRESERVE_ON_UPDATE_AND_ROLLBACK = [
    "user_config.json",
]

GITHUB_RELEASES_API = "https://api.github.com/repos/ClearblueskyTrading/Clearbluesky-Stock-Scanner/releases/latest"
GITHUB_RELEASES_API_TAG = "https://api.github.com/repos/ClearblueskyTrading/Clearbluesky-Stock-Scanner/releases/tags/{tag}"


def _safe_extractall(zf: zipfile.ZipFile, target_dir: str) -> None:
    """Extract zip contents after validating no path traversal (Zip Slip protection)."""
    target_real = os.path.realpath(target_dir)
    for member in zf.namelist():
        member_path = os.path.realpath(os.path.join(target_dir, member))
        if not member_path.startswith(target_real + os.sep) and member_path != target_real:
            raise ValueError(f"Zip path traversal blocked: {member}")
    zf.extractall(target_dir)


def _parse_version(s: str) -> tuple:
    """e.g. '7.0' or 'v7.0' -> (7, 0)."""
    s = (s or "").strip().lstrip("v")
    parts = re.findall(r"\d+", s)
    if not parts:
        return (0, 0)
    return tuple(int(x) for x in parts[:2])


def get_backup_info() -> Optional[Dict[str, Any]]:
    """Return last backup manifest if any: { path, version, timestamp }."""
    if not os.path.isfile(MANIFEST_FILE):
        return None
    try:
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        path = data.get("backup_path") or ""
        if path and os.path.isfile(path):
            return {
                "path": path,
                "version": data.get("version", ""),
                "timestamp": data.get("timestamp", ""),
            }
    except Exception:
        pass
    return None


def backup_app(version: str, progress_callback=None) -> Optional[str]:
    """
    Create a zip backup of the app folder (for rollback).
    Preserved paths are still included in backup; we just don't overwrite them on rollback.
    Returns path to backup zip or None on failure.
    """
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    backup_path = os.path.join(BACKUP_DIR, f"app_backup_{stamp}.zip")
    try:
        if progress_callback:
            progress_callback("Creating backup...")
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(BASE_DIR):
                if "update_backups" in root or "__pycache__" in root:
                    continue
                for f in files:
                    if f.endswith(".zip") and "app_backup_" in f:
                        continue
                    path = os.path.join(root, f)
                    rel = os.path.relpath(path, BASE_DIR)
                    if rel.startswith(".."):
                        continue
                    zf.write(path, rel)
        manifest = {
            "backup_path": os.path.abspath(backup_path),
            "version": version,
            "timestamp": stamp,
        }
        with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        return backup_path
    except Exception:
        if os.path.isfile(backup_path):
            try:
                os.remove(backup_path)
            except Exception:
                pass
        return None


def _copy_tree_skip_preserve(src_root: str, dest_root: str, progress_callback=None) -> None:
    """Copy src_root into dest_root; skip files whose relpath is in PRESERVE_ON_UPDATE_AND_ROLLBACK."""
    dest_root = os.path.abspath(dest_root)
    preserve_set = set(p.lower() for p in PRESERVE_ON_UPDATE_AND_ROLLBACK)
    count = 0
    for root, dirs, files in os.walk(src_root):
        rel_root = os.path.relpath(root, src_root)
        if rel_root == ".":
            rel_root = ""
        for d in dirs:
            if d == "__pycache__" or d == "update_backups":
                continue
            dest_dir = os.path.join(dest_root, rel_root, d) if rel_root else os.path.join(dest_root, d)
            os.makedirs(dest_dir, exist_ok=True)
        for f in files:
            rel_path = os.path.join(rel_root, f) if rel_root else f
            if rel_path.replace("\\", "/").lower() in preserve_set:
                continue
            src_path = os.path.join(root, f)
            dest_path = os.path.join(dest_root, rel_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(src_path, dest_path)
            count += 1
            if progress_callback and count % 50 == 0:
                progress_callback(f"Copied {count} files...")


def rollback(progress_callback=None) -> Optional[str]:
    """
    Restore app from last backup. Keeps existing user_config.json (never overwrite).
    Returns None on success; returns error message string on failure.
    """
    info = get_backup_info()
    if not info:
        return "No backup found. Run an update first to create a backup."
    backup_path = info["path"]
    if not os.path.isfile(backup_path):
        return "Backup file missing or moved."
    try:
        if progress_callback:
            progress_callback("Extracting backup...")
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(backup_path, "r") as zf:
                _safe_extractall(zf, tmp)
            # Our backup: flat files in tmp. GitHub zip: one root folder, maybe with scanner/ subdir.
            entries = os.listdir(tmp)
            if len(entries) == 1 and os.path.isdir(os.path.join(tmp, entries[0])):
                single = os.path.join(tmp, entries[0])
                scanner_sub = os.path.join(single, "scanner")
                app_sub = os.path.join(single, "app")  # legacy layout
                src_root = scanner_sub if os.path.isdir(scanner_sub) else (app_sub if os.path.isdir(app_sub) else single)
            else:
                src_root = tmp
            if progress_callback:
                progress_callback("Restoring files (keeping your config)...")
            _copy_tree_skip_preserve(src_root, BASE_DIR, progress_callback)
        if progress_callback:
            progress_callback("Rollback complete.")
        return None
    except Exception as e:
        return str(e)


def fetch_latest_release(tag: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get latest or tagged release from GitHub. Returns dict with tag_name, zipball_url, html_url, etc."""
    try:
        import urllib.request
        url = GITHUB_RELEASES_API_TAG.format(tag=tag) if tag else GITHUB_RELEASES_API
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data
    except Exception:
        return None


def apply_update(version_before: str, tag: Optional[str] = None, progress_callback=None) -> Optional[str]:
    """
    Download release zip from GitHub and apply over app. Never overwrites user_config.json.
    tag: e.g. 'v7.0' or None for latest.
    Returns None on success; returns error message string on failure.
    """
    release = fetch_latest_release(tag)
    if not release:
        return "Could not fetch release from GitHub."
    zip_url = release.get("zipball_url")
    tag_name = release.get("tag_name", "")
    if not zip_url:
        return "Release has no source zip."
    try:
        if progress_callback:
            progress_callback("Downloading update...")
        import urllib.request
        req = urllib.request.Request(zip_url, headers={"Accept": "application/zip"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            zip_data = resp.read()
        if progress_callback:
            progress_callback("Extracting update...")
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, "update.zip")
            with open(zip_path, "wb") as f:
                f.write(zip_data)
            # Integrity check: verify download is a valid zip before applying
            if not zipfile.is_zipfile(zip_path):
                return "Downloaded file is not a valid zip (corrupted download?)."
            with zipfile.ZipFile(zip_path, "r") as zf:
                bad = zf.testzip()
                if bad is not None:
                    return f"Zip integrity check failed on: {bad} (corrupted download?)."
                _safe_extractall(zf, tmp)
            # GitHub zip has one root dir; repo has scanner/ subfolder (or legacy app/)
            entries = [e for e in os.listdir(tmp) if e != "update.zip"]
            if len(entries) == 1 and os.path.isdir(os.path.join(tmp, entries[0])):
                single = os.path.join(tmp, entries[0])
                scanner_sub = os.path.join(single, "scanner")
                app_sub = os.path.join(single, "app")
                src_root = scanner_sub if os.path.isdir(scanner_sub) else (app_sub if os.path.isdir(app_sub) else single)
            else:
                src_root = tmp
            # Stage update in a temporary copy first, then apply (atomic-ish)
            if progress_callback:
                progress_callback("Staging update files...")
            staging_dir = os.path.join(tmp, "_staging")
            os.makedirs(staging_dir, exist_ok=True)
            # Copy current app to staging
            for root_d, dirs_d, files_d in os.walk(BASE_DIR):
                if "update_backups" in root_d or "__pycache__" in root_d:
                    continue
                rel = os.path.relpath(root_d, BASE_DIR)
                for fd in files_d:
                    src_file = os.path.join(root_d, fd)
                    dst_file = os.path.join(staging_dir, rel, fd) if rel != "." else os.path.join(staging_dir, fd)
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                    shutil.copy2(src_file, dst_file)
            # Apply new files over staging (skipping preserved)
            _copy_tree_skip_preserve(src_root, staging_dir, progress_callback)
            # Staging succeeded — now apply staged files to real app dir
            if progress_callback:
                progress_callback("Applying update (keeping your config)...")
            _copy_tree_skip_preserve(staging_dir, BASE_DIR, progress_callback)
        if progress_callback:
            progress_callback("Update complete.")
        return None
    except Exception as e:
        return f"Update failed: {e}. Your backup is intact — use Rollback to restore."


def run_update_flow(version_before: str, tag: Optional[str] = None, progress_callback=None) -> Optional[str]:
    """
    Full flow: backup current state, then apply update. Uses existing user config (never overwrite).
    Returns None on success; returns error message on failure.
    """
    if progress_callback:
        progress_callback("Backing up current version...")
    backup_path = backup_app(version_before, progress_callback=progress_callback)
    if not backup_path:
        return "Backup failed. Update aborted."
    err = apply_update(version_before, tag=tag, progress_callback=progress_callback)
    if err:
        return f"Update failed: {err}. You can use Rollback to restore from backup."
    return None
