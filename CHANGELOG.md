# Changelog

All notable changes to ClearBlueSky Stock Scanner are documented here.

---

## [7.87] – 2026-02-11

### Fixed — Scanner & report pipeline bugfixes
- **CLI premarket merge** — Velocity premarket results were silently dropped (iterated dict keys instead of `tickers` list).
- **Premarket `price` NameError** — Undefined `price` caused crash in dollar-volume calc; fixed.
- **Premarket direction bias** — Removed `ta_change_u` filter so both gap-up and gap-down are captured.
- **Watchlist rel-volume** — `"1.5x"` strings now parse correctly (stripped `x` suffix).
- **Enhanced dip ticker case** — Stored normalized uppercase ticker for consistent dedup.
- **History leveraged_play crash** — Dict used as Counter key; now extracts ticker string.
- **History smart-money keys** — Fixed wrong keys (`wsb` → `wsb_rank`/`wsb_mentions`, `insider_filings` → `form4_count_90d`); stats were always zero.
- **PDF directive mismatch** — Momentum scans got swing directive in PDF; now uses correct `directive_block`.
- **Leveraged play schema** — Normalized to `{leveraged_ticker, match_type}` dict everywhere; case-insensitive lookup.
- **Premarket metrics in reports** — Gap %, dollar volume, float, vol/float now preserved in report rows.
- **Config passthrough** — Ticker enrichment + market intel now forward user config to Alpaca failover.
- **Price history div-by-zero** — Guarded `pct_change` against `first_close == 0`.

### Changed
- Version labels updated in USER_MANUAL, CLAUDE_AI_GUIDE, DOCKER, INSTALL.bat (were stuck on v7.7).

See **app/CHANGELOG.md** for full details.

---

## [7.86] – 2026-02-10

### Added
- EMA8 support in programmatic TA (`ema8`, `price_vs_ema8`) and report formatting.
- Velocity Trend Growth `vtg_require_above_sma200` (default on) wired in GUI + CLI.
- Watchlist EMA8-aware scoring and overextension penalties.
- Pre-market breakout multi-touch resistance confirmation and EMA8 extension penalty.
- Report metadata for setup quality: `ema8_status`, `invalidation_level`, extension-penalty context.
- Curated leveraged ETF universe expanded to include core bull + bear/inverse symbols.

### Changed
- `emotional_require_above_sma200` default now `true` for new configs.
- Config/docs refreshed for the new scanner controls and TA fields.
- ETF scanner paths now enforce a hard `100k` average-volume floor.
- Pre-market ETF scan scope moved to curated ETFs (no full 2000+ ETF sweeps).
- Earnings parsing fixed so stale month/day values no longer roll into next year; report risk checks now prefer yfinance earnings enrichment and avoid false "today" warnings for historical earnings.

## [7.85] – 2026-02-10

### Fixed — QA and CLI consistency
- **CLI min-score keys** now match GUI/report behavior (Swing uses `emotional_min_score`; normalized scan keys).
- **Clean install test** now uses valid CLI args (`watchlist` + fixture file) and treats no-candidate scans as success (exit 0).
- **Watchlist filter handling** accepts both internal value (`all`) and display label (`All tickers`).
- **Watchlist range parity** runtime now matches documented 0–25% slider behavior.
- **Config loading** app startup now uses `scan_settings.load_config()` defaults/migrations.

### Docs
- Updated README, USER_MANUAL, CLI guide, and in-app Help text to current behavior.

## [7.84] – 2026-02-10

### Changed — Watchlist scanner
- **Filter** — Slider = max of range (0–X% down). Before: X–25%. Now: 0–X%.
- **Labels** — "Down % today" / "All tickers". Slider disabled when All.
- **run_watchlist_10.py** — CLI helper for 10% down scan.

See **app/CHANGELOG.md** for full details.

---

## [7.83] – 2026-02-10

### Added
- **Velocity Trend Growth** — Sector-first momentum scan: ranks sectors by return, scans only leading sectors (~160 tickers vs ~400).
- **Curated ETF list** — ~45 key ETFs instead of full Finviz screener (250+); saves ~1.5 min.
- **New filters** — Optional beat SPY, min volume, volume confirm, MA stack, RSI band (all off by default).

### Changed
- **Broker button removed** — Use IBKR + IBOT for orders; prompt AI to craft IBOT commands. See docs/guidelines/trading-workflow.md.
- **Legacy Trend removed** — Trend - Long-term scanner replaced by Velocity Trend Growth. trend_scan_v2.py deleted.
- **Default scan** — Velocity Trend Growth first in dropdown.
- **Target return** — 1–300%, default 5%.

See **app/CHANGELOG.md** for full details.

---

## [7.0] – February 2026

### Added
- **Queue-based scans** – Scans run in a background thread; GUI stays responsive (no hanging).
- **Run all scans** – Checkbox under Run Scan runs all six scanners in sequence with 60-second delays (may take 20+ minutes; rate-limited).
- **Rate-limit safeguard** – 60-second delay between scans when "Run all scans" is used.

### Changed
- **Swing** – Always uses emotional-only dip logic (emotional_dip_scanner). Separate "Emotional Dip" scan type removed.
- **Watchlist** – Single scanner with **Filter**: "Down X% today" (min % in 1–25%) or "All tickers". Config: Min % down (range 1–25%), Filter.
- **Scan types** – Reduced to 6: Trend – Long-term, Swing – Dips, Watchlist, Velocity Barbell, Insider – Latest, Pre-Market.
- **CLI** – Scan types: trend, swing, watchlist, velocity, insider, premarket (no emotional_dip, no watchlist_tickers). Watchlist uses config `watchlist_filter`.
- **Pre-Market** – Removed emoji from "Outside optimal pre-market window" message for Windows encoding.
- **INSTALL.bat** – Updated to v7.0.
- **Reports folder** – Reports path resolved relative to app folder (not cwd); prevents wrong or duplicate reports folders. Settings persist absolute path.

### Added
- **Executive summary in all 3 report outputs** – PDF, JSON instructions, and _ai.txt (OpenRouter prompt + file header) now specify: start with a brief executive summary (context, rationale, key findings) in plain language, then trade recommendations. Same prompt in each file so they work alone or together.

### Docs
- README.md, README.txt (root and app), RELEASE_v7.0.md, NEXT_RELEASE.md, app/CHANGELOG.md, app/RELEASE.md, app/CLI_FOR_CLAUDE.md, app/SCANNER_NAMING_AUDIT.md.

---

## [6.5] – February 2026

### Added
- **CLI for Claude / automation** – `scanner_cli.py` runs scans from the command line (no GUI). Use for automation or with tools like Desktop Commander. Exit 0 on success, 1 on failure; `[OK]` / `[FAIL]` output. See **app/CLI_FOR_CLAUDE.md** for usage.
- **ETFs index** – Index dropdown now includes **ETFs** (Finviz “Exchange Traded Fund” universe). Trend, Swing (Emotional Dip), Pre-Market, and report breadth all support ETFs when “ETFs” is selected.
- **Watchlist 3pm** – Scan watchlist tickers down X% today (slider 1–25%). Best run ~3 PM.
- **Watchlist – All tickers** – Scan all watchlist tickers with no filters.
- **Velocity Barbell** – Foundation + Runner (or Single Shot) from sector signals. Config: min sector % (up or down), theme (auto / barbell / single_shot). Runner Candidate 1 & 2 with RSI/leverage.
- **AI fallback _ai.txt** – If OpenRouter fails or returns empty, app still writes a fallback _ai.txt with error and instructions.
- **user_config.json.example** – Blank template (no API keys); safe to commit.

### Changed
- **Reports – SMA200 status** – Per-stock **SMA200 status** (Above / Below / At / N/A) is now shown in PDF, JSON, and text. SMA50/SMA200 no longer show "null"; missing values display as N/A.
- **Watchlist – Near open** renamed to **Watchlist 3pm**; slider label **% down (1–25%)**.
- **Install** – INSTALL.bat copies app contents to install root; removes any existing `user_config.json` so install starts with blank config; pip uses `--upgrade`.
- **Report min score** – Watchlist 3pm, Watchlist – All tickers, Velocity Barbell, Insider use min_score 0.
- **Update pop-up** – “Later” button and lambda closure fixed.

### Docs
- README, README.txt, RELEASE_v6.5.md, **app/CLI_FOR_CLAUDE.md** (CLI usage for Claude/automation), SCANNER_CONFIG_PARAMETERS.md (Watchlist, Velocity Barbell), GITHUB_PUSH.md (v6.5), CHANGELOG.md. No API keys or user config in repo or release.

---

## [6.4] – February 2026

- JSON analysis package with `instructions` for any AI.
- OpenRouter AI integration, RAG books, TA in report, Alpha Vantage sentiment, SEC insider context, vision charts, backtest feedback loop.
- Help and docs updated.

---

*ClearBlueSky – made with Claude AI*
