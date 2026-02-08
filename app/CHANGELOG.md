# Changelog

All notable changes to ClearBlueSky Stock Scanner are documented here.

---

## [7.5] – 2026-02-08

### Added
- **30-Day Price History** — New `price_history.py` module fetches fresh 30-day OHLCV data (via yfinance, 8 parallel workers) for all scan tickers + 17 core leveraged/market ETFs every scan run. Injected into AI prompt as "sanity check" table, JSON report (`price_history_30d`), and text report. AI instructions updated to verify entries/targets against recent highs/lows.
- **Scan History (long-term log)** — Every scan appends a slim record to `reports/scan_history.json`: ticker, score, price, change, sector, RSI, SMA200 status, smart money, market breadth, and 30-day price summary. No instructions blob or daily rows — keeps file size manageable.
- **History Report** — New `history_analyzer.py` module + **History** button in GUI. Auto-backfills from all existing JSON report files on first run. Generates comprehensive report: scans by type, score distribution, top 15 most flagged tickers, repeat tickers (3+ appearances), price trends (first scan vs latest), top 20 highest scores ever, sector frequency, market regime history, leveraged plays, smart money overlap, watchlist hit rate.
- **Accuracy Tracker** — New `accuracy_tracker.py` module. Compares past scan picks (1-7 days old) against current prices. Calculates hits (price up), misses (price down), and accuracy %. Breaks down by scan type. Lists best hits and worst misses.
- **Metrics Bar on GUI** — Dark bar below header showing: Accuracy %, Hits, Misses, Picks count. Color coded (green 60%+, amber 40-60%, red <40%). Refreshes on startup (with auto-backfill) and after every scan.
- **History button** — Added to Row 1 of bottom buttons (Broker, Reports, History, Logs, Config). Opens scrollable history report window with Open File / Open Folder buttons.

### Changed
- **Window height** increased from 520→550 to accommodate metrics bar.
- **AI prompt** — Instruction #3 added: "Use the 30-day price history as a SANITY CHECK — verify entries/targets make sense vs recent highs/lows."
- **Release zip** — Only includes last 2 version release notes (v7.4, v7.5). Old RELEASE_v6.x–v7.3.md excluded.

---

## [7.4] – 2026-02-08

### Added
- **Smart Money Signals** — New `smart_money.py` module provides three layers of institutional/social data:
  - **WSB/Reddit sentiment** (apewisdom.io) — top trending tickers with mention count, upvotes, and trend direction. Applied to all scanners.
  - **Institutional 13F holders** (yfinance) — identifies notable funds (Berkshire, BlackRock, Vanguard, etc.) and flags increasing positions. Trend scanner only.
  - **SEC EDGAR Form 4 insider filings** — counts recent insider transactions per ticker via SEC full-text search. Trend scanner only.
- Smart Money data injected into AI prompt, JSON report, and text report alongside Market Intelligence.
- `use_smart_money_signals` toggle in Settings (on by default).

### Fixed
- **Emotional Dip scanner returned 0 results** — Six stacked filters were too strict:
  - SMA200 requirement disabled by default (stocks that just dipped are naturally below SMA200).
  - Buy/Strong Buy rating requirement disabled by default (still boosts score).
  - Min relative volume lowered from 1.8x → 1.2x; handles `None` gracefully (Finviz doesn't always return it).
  - Min upside lowered from 10% → 5%.
  - Dip range widened from 1.5–4% → 1–5%.
  - "Unclear" dip type now passes (only "fundamental" is blocked). No news ≠ fundamental problem.
  - Scanner now returns ~30 candidates vs 0 previously.
- **Config auto-migration** — Existing `user_config.json` with old strict emotional dip values auto-migrates to loosened defaults on load.

---

## [7.3] – 2026-02-08

### Added
- **Market Intelligence** — New `market_intel.py` module gathers live market context before AI analysis: Google News RSS headlines (~24), Finviz curated news (~24), sector performance table (11 sectors, today/week/month/quarter/YTD), market snapshot (SPY, QQQ, DIA, IWM, GLD, USO, TLT, VIX with daily change). All fetched in parallel (~3-5 sec). Injected into AI prompt, JSON package, and text report. Toggle in Settings (on by default). No API key needed.
- **RunPod / Multi-LLM deployment guide** — USER_MANUAL.md now includes a full section on running ClearBlueSky JSON output through self-hosted LLMs on RunPod, with architecture diagram, vLLM/Ollama setup, Python script for multi-model consensus, and cost comparison.
- **`feedparser` dependency** — Added to requirements.txt for Google News RSS parsing.

### Changed
- **"Velocity" → "Leveraged" in UI** — Index dropdown renamed from "Velocity (high-conviction)" to "Leveraged (high-conviction)". Help text and docs updated. Scanner internal IDs unchanged.
- **Button layout overhaul** — Bottom buttons reorganized into equal-width grid (3 rows × 4 columns). Window height increased from 460→520 to prevent cutoff. Emoji clutter removed from button labels.
- **Manual button** — Renamed from "README" to "Manual"; now opens USER_MANUAL.md (with fallback to README.md).
- **AI prompt updated** — Instruction #2 changed from "Search for recent news" to "Use the MARKET INTELLIGENCE above to understand today's market context, sector rotation, and breaking news."
- **README.md** — Rewritten: added Market Intelligence bullet, cleaned up velocity references, added `market_intel.py` to project layout.
- **USER_MANUAL.md** — Added Market Intelligence section (§9), RunPod/multi-LLM section (§14), updated all scanner descriptions and config tables.

---

## [7.2] – 2026-02-06

### Fixed (CRITICAL)
- **Zip Slip vulnerability** in updater.py — path traversal protection on all zip extractions.
- **Download integrity** — update zips validated with `is_zipfile()` + `testzip()` before applying.

### Fixed (HIGH — Scanner Accuracy)
- **ATR calculation** (velocity_scanner) — correct True Range formula using `pd.concat().max(axis=1)`.
- **Gap Recovery scoring** — was always 0 due to circular math; now uses `prior_low` + ATR floor.
- **Market context SMA50/200** — period changed from "5d" to "1y" so SMAs have enough data.
- **Trend scoring `get_pct()`** — removed broken `< 1` heuristic; finvizfinance decimals always *100.
- **Gap-and-Go retention** — was hardcoded 100; now computed from `prior_high` vs `pm_price`.

### Fixed (HIGH — Performance)
- **Quick Lookup threaded** — no longer freezes GUI during report generation.
- **462 lines dead code removed** — six unused `_run_*_scan` methods.
- **Velocity scanner parallelized** — `ThreadPoolExecutor(8)` for tickers, `(4)` for market context.
- **Emotional dip scanner** — 3 Finviz calls per ticker → 1 (reuses cached quote).
- **Report generator** — leveraged mapping loaded once instead of per-ticker.

### Fixed (MEDIUM)
- **Race conditions** — `threading.Event` for cancellation, result queue cleared, update/rollback concurrency guard.
- **OpenRouter retry** — 3 retries with backoff on connection errors, 429, 5xx. Better error messages.
- **Bare `except:` replaced** — 10 instances → `except Exception:` across 4 files.
- **Transactional updates** — staging directory before applying; real app untouched if staging fails.
- **`_derive_sma200_status`** — non-numeric values no longer crash report generation.

### Changed
- **INSTALL.bat** updated to v7.2.
- **scan_presets.json** cleaned: removed stale "Emotional Dip - Bounce", added "Velocity Pre-Market Hunter", updated Swing to `emotional_*` keys.
- **requirements.txt** tightened: `pandas>=2.0,<3.0`, `yfinance>=0.2.36`, `pandas-ta>=0.3.14b0`, `chromadb>=0.4,<1.0`.
- **Legacy config keys** commented for clarity (`dip_*` vs `emotional_*`).

### Added
- **USER_MANUAL.md** — Comprehensive user manual covering all scanners, settings, config options, scoring system, and troubleshooting.
- **OpenRouter credit display** — Shows remaining balance and model name below scan button.
- **Claude model removed** — Only Gemini 3 Pro Preview (credits) and DeepSeek R1 T2 Chimera (free). Auto-migrates existing Claude users to Gemini.
- **Keyboard shortcuts** — Enter = Run Scan, Escape = Stop, F1 = Help.
- **Scrollable Help window** — replaced messagebox with Toplevel + Text widget.
- **Cross-platform file open** — `_open_path()` helper for Windows/macOS/Linux.
- **Auto report cleanup** — reports older than 30 days removed on startup.
- **OpenRouter usage tracking** — token counts logged after each API call.

### Removed
- Orphaned `fundamentals_helper.py` (never imported).
- `ClearBlueSkyWin/` added to .gitignore.

---

## [7.1] – 2026-02-06

### Added
- **Elite Swing Trader System Prompt** – Replaced Master Trading Report Directive with focused swing methodology: 1-5 day max hold (optimal 1-2 days), S&P 500 + leveraged ETFs, specific entry/exit windows (8AM-8AM cycle), The 1-2-5 exit framework, leveraged ETF 3-day max, weekend management, T+1 settlement rules.
- **Quick Lookup (1-5 tickers)** – Quick Lookup now accepts 1-5 ticker symbols at once (comma or space separated). Enter "AAPL, MSFT, NVDA" → generates instant multi-ticker report.
- **Import/Export Config** – New **💾 Config** button exports/imports full `user_config.json` (all settings + API keys) for backup or transfer to new PC. Includes security warning.
- **GitHub attribution** – All reports (PDF footer, AI directive, JSON, _ai.txt) include: "This report was generated by ClearBlueSky Stock Scanner. GitHub: https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner/releases"

### Changed
- **AI prompt strategy** – Focus shifted from velocity-heavy to **swing trade + long trend** methodology (1-5 day holds, not velocity-specific).
- **Header subtitle** – Changed to "AI Stock Research Tool · works best with Claude AI".

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
