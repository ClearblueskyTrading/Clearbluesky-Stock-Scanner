# ClearBlueSky v6.2 Release

**Release date:** February 2026

## What's in v6.2

- **Update notice** – On startup, the app checks for a newer version and shows a notice with a link to download from GitHub.
- **Watchlist scanner** – Third scan type: watchlist tickers that are down 1–25% today (today's Change %). Config: "% down today" slider. Good for big-name dips that often bounce in a few days.
- **Docker & cross-platform** – Run on any OS without the Windows installer. Use Docker (`docker compose up`) or run natively on Linux/macOS with `./app/run.sh`. See [DOCKER.md](DOCKER.md).
- **Cross-platform sound** – Beeps work on Windows (winsound), Linux, and macOS (pygame).
- Two scanners (Trend, Swing), plus Watchlist scanner; PDF reports; watchlist (200 tickers, 2 beeps + ★ WATCHLIST); Finviz CSV import; scan config. No API key in code; optional Finviz key in `user_config.json` only.

## Release zip

- **File:** `ClearBlueSky-6.2.zip` (in project root).
- **Excluded from zip:** `user_config.json`, `error_log.txt`, `__pycache__/`, contents of `app/reports/` and `app/scans/`.
- Safe to share; no API keys or user data included.

---

*ClearBlueSky v6.2 – made with Claude AI*
