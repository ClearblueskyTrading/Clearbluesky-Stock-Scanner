# ClearBlueSky Stock Scanner v7.0

**Release date:** February 2026

---

## What's New in v7.0

- **Queue-based scans** – Scans run in a background thread; GUI stays responsive (no hanging).
- **Run all scans** – Checkbox runs all seven scanners in sequence with 60-second delays (may take 20+ minutes; rate-limited).
- **Swing** – Always uses emotional-only dip logic (separate "Emotional Dip" scan removed). **Index:** S&P 500, Russell 2000, ETFs, or **Velocity (high-conviction)** — emotional dips on the Velocity universe only.
- **Velocity Pre-Market Hunter** – New scanner: pre-market setups (gap recovery, accumulation, breakout, gap-and-go) with grades A+–F. **Not ticker-restricted** when Index is S&P 500 / Russell 2000 / ETFs; uses fixed high-conviction list when Index is Velocity (high-conviction).
- **Watchlist** – Single scanner with **Filter**: "Down X% today" (min % in 1–25%) or "All tickers". Config: Min % down, Filter.
- **Pre-Market** – Fixed Windows encoding when outside optimal scan window.
- **In-app Update & Rollback** – **Update** backs up your version, then applies the latest release from GitHub; **Rollback** restores the previous version. **Your `user_config.json` is never overwritten** on update or rollback. See **UPDATE.md**.
- **Versioning** – From v7.0 onward, strict versioning: **7.1, 7.2**, etc. Each release tagged on GitHub; in-app updater stays in sync.
- **CLI** – Scan types: trend, swing, watchlist, velocity, insider, premarket (no emotional_dip or watchlist_tickers). Watchlist uses config `watchlist_filter`.
- **Reports folder** – Path always resolved relative to app folder; no duplicate or wrong folder. Settings save absolute path.
- **Executive summary in PDF, JSON, and _ai.txt** – All three report outputs now include a short prompt so any AI (used alone or together) produces a brief executive summary (context, market/sector backdrop, scan rationale, key findings) in plain language, then trade recommendations.

See **app/CHANGELOG.md** and **UPDATE.md** for full details.

---

## Release package

- **File:** `ClearBlueSky-v7.0.zip` (tag `v7.0` on GitHub).

**Included (clean):**
- **Root:** INSTALL.bat, README.md, README.txt, LICENSE.txt, CHANGELOG.md, RELEASE_v7.0.md, UPDATE.md, NEXT_RELEASE.md, DOCKER.md, docker-compose.yml, Dockerfile, CLAUDE_AI_GUIDE.md.
- **app/:** All app code (.py), including **updater.py**, **velocity_scanner.py**; README.md, CHANGELOG.md, RELEASE.md, CLI_FOR_CLAUDE.md, WORKFLOW.md, SCANNER_*.md, VELOCITY_PREMARKET_README.md, requirements.txt, RUN.bat, run.sh, START.bat, scan_types.json, scan_presets.json, user_config.json.example, leveraged_tickers.json, velocity_leveraged_arsenal.json, and other docs/data needed to run. No user data.

**Excluded (never in zip):**
- user_config.json (API keys / preferences)
- error_log.txt, __pycache__/, *.pyc
- app/reports/, app/scanner_output/, app/rag_store/, app/scans/, app/update_backups/, app/update_backup_manifest.json
- scanner_presets_export.json, release_notes_v7.md, backtest_signals.db

No API keys or user config in the release. Safe to share.

---

*ClearBlueSky v7.0 – made with Claude AI*
