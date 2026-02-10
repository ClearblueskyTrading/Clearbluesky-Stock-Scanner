# ClearBlueSky Stock Scanner — v7.85 Release Notes

**Release Date:** February 10, 2026

---

## QA + Consistency Release

This release focuses on fixing QA findings from the v7.84 review and aligning CLI behavior with GUI behavior.

### 1) CLI min-score parity with GUI

- `scanner_cli.py` now resolves min-score keys by scan type (normalized keys).
- Swing now uses `emotional_min_score` (same as app GUI report path), with backward-compatible fallback to `swing_min_score`.
- Prevents invalid key lookups from display labels with spaces.

### 2) Watchlist filter normalization

- GUI + CLI now accept both:
  - internal value: `all`
  - display value: `All tickers`
- Prevents accidental mode mismatch after manual config edits/imports.

### 3) Watchlist range parity (0–25)

- Runtime clamp now matches the documented slider range: **0–25%**.
- Watchlist scanner docstring and progress messaging updated to reflect 0–X logic.
- Progress strings use Windows-safe ASCII in console output (`0-X`).

### 4) Config loading consistency

- `app.py` now loads configuration through `scan_settings.load_config()`.
- Ensures startup consistently applies defaults/migrations.

### 5) Clean install test fixed

- `scripts/clean_install_test.py` now uses valid CLI arguments:
  - `--scan watchlist --watchlist-file ...`
- Test now correctly treats no-candidate scans (exit code 0) as pass.

---

## Docs updated

- `README.md`
- `USER_MANUAL.md`
- `app/CLI_FOR_CLAUDE.md`
- In-app Help text (`app.py`)
- Changelogs (`CHANGELOG.md`, `app/CHANGELOG.md`)

---

## Upgrade

Drop-in replacement — no config migration required.
Your `user_config.json` remains local and is never overwritten by release artifacts.

---

*ClearBlueSky Stock Scanner — Built with Claude AI*
*GitHub: https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner*
