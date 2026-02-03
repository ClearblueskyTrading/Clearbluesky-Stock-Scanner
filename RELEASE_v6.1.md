# ClearBlueSky v6.1 Release

**Release date:** February 2026

## What's in v6.1

- **Docker & cross-platform:** Run on any OS without the Windows installer. Use Docker (`docker compose up`) or run natively on Linux/macOS with `./app/run.sh`. See [DOCKER.md](DOCKER.md).
- **Cross-platform sound:** Beeps work on Windows (winsound), Linux, and macOS (pygame).
- Everything from v6.0: two scanners (Trend, Swing), PDF reports, watchlist (200 tickers, 2 beeps + ★ WATCHLIST), Finviz CSV import, scan config. No API key in code; optional key in `user_config.json` only.

## Release zip

- **File:** `ClearBlueSky-6.1.zip` (in project root).
- **Excluded from zip:** `user_config.json`, `error_log.txt`, `__pycache__/`, contents of `app/reports/` and `app/scans/`.
- Safe to share; no API keys or user data included.

---

*ClearBlueSky v6.1 – made with Claude AI*
