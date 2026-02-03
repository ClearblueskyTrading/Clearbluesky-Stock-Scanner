# ClearBlueSky v6.0 Release

**Release date:** February 2026

## What's in v6.0

- **Two scanners:** Trend (long-term) and Swing (dips). Emotional Dip and Pre-Market options removed from the default scan types.
- **PDF reports only** – Date/time stamped, with Master Trading Report Directive for AI. Charts: use Yahoo Finance (link in report).
- **Watchlist** – Add up to 200 tickers. When a watchlist stock appears in a scan: 2 beeps + listed at top of report with ★ WATCHLIST.
- **Import watchlist from Finviz CSV** – Watchlist → Import CSV (Ticker or Symbol column).
- **Scan Config** – Adjust min score, dip %, price, volume per scan type (Config button).
- **No API key in code** – Optional Finviz API key is stored only in `app/user_config.json` on your PC. That file is not included in the source or in the release zip.

## GitHub

1. Create a new repo (e.g. `ClearBlueSky`).
2. Add remote: `git remote add origin https://github.com/YOUR_USERNAME/ClearBlueSky.git`
3. Commit and push (`.gitignore` ensures `user_config.json` and `error_log.txt` are not committed).
4. Create a release tag: `git tag v6.0` then `git push origin v6.0`.
5. In GitHub → Releases → “Draft a new release”, choose tag `v6.0`, upload `ClearBlueSky-6.0.zip` as the release asset, publish.

## Release zip

- **File:** `ClearBlueSky-6.0.zip` (in project root).
- **Excluded from zip:** `user_config.json`, `error_log.txt`, `__pycache__/`, contents of `app/reports/` and `app/scans/`.
- Safe to share; no API keys or user data included.

---

*ClearBlueSky v6.0 – made with Claude AI*
