# Changelog

All notable changes to ClearBlueSky Stock Scanner are documented here.

---

## [7.0] – 2026-02-06

### Added
- **Queue-based scans** – Scans run in a background thread; GUI stays responsive (no hanging).
- **Run all scans** – Checkbox under Run Scan runs all seven scanners in sequence with rate-limit delays (60s between scans). Note: "May take 20+ minutes due to API rate limits."
- **Rate-limit safeguard** – 60-second delay between scans when "Run all scans" is used to respect API limits.
- **Velocity Pre-Market Hunter** – New scan type: pre-market setups (gap recovery, accumulation, breakout, gap-and-go) with grades A+–F. Index: S&P 500 / Russell 2000 / ETFs (not ticker-restricted; up to 200 tickers) or fixed high-conviction list. Scanner: `velocity_scanner.run_premarket_scan`.
- **Swing + Velocity universe** – Index option **Velocity (high-conviction)** runs emotional dip logic on the Velocity ticker list only (same filters; smaller universe).
- **In-app Update & Rollback** – **Update** backs up current version, then downloads and applies latest release from GitHub. **Rollback** restores from last backup. **user_config.json is never overwritten** on update or rollback. See root **UPDATE.md**.
- **Versioning** – From v7.0 onward: strict 7.1, 7.2, …; tagged on GitHub; updater stays in sync.
- **Executive summary in all 3 report outputs** – PDF directive, JSON `instructions`, and _ai.txt (system prompt + file header) now tell any AI to start with a brief executive summary (context, market/sector backdrop, scan rationale, key findings) in plain language—not only trade recommendations. Applies whether each file is used alone or together.

### Changed
- **Swing** – Now always uses emotional-only dip logic (emotional_dip_scanner). Separate "Emotional Dip" scan type removed. Index can be S&P 500, Russell 2000, ETFs, or **Velocity (high-conviction)**.
- **Watchlist** – Single scanner with **Filter**: "Down X% today" (min % in 1–25% range) or "All tickers". Config: **Min % down (range 1–25%)**, **Filter**.
- **Scan types** – Seven: Trend – Long-term, Swing – Dips, Watchlist, Velocity Barbell, Insider – Latest, Pre-Market, **Velocity Pre-Market Hunter**.
- **CLI** – `--scan` choices: trend, swing, watchlist, velocity, premarket, insider (no emotional_dip, no watchlist_tickers). Watchlist uses config `watchlist_filter` (all vs down_pct).
- **Pre-Market** – Removed emoji from "Outside optimal pre-market window" message for Windows console encoding.

### Fixed
- Pre-Market scanner encoding on Windows (`'charmap' codec` when printing Unicode).
- **Reports folder** – Reports path is always resolved relative to the app folder (not cwd). Prevents wrong or duplicate reports folders when config has a relative path; GUI and CLI use the same logic. Settings save the resolved absolute path.

---

## [6.5]

- Watchlist 3pm, Watchlist – All tickers, Velocity Barbell (Foundation + Runner / Single Shot), AI fallback _ai.txt, install/upgrade fixes.

---

## [6.x] and earlier

See repository history for earlier release notes.
