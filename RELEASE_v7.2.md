# ClearBlueSky Stock Scanner v7.2

**Release date:** February 6, 2026

---

## What's New in v7.2 — Quality & Performance Release

28 fixes across security, scanner accuracy, performance, and UX. Full audit by Opus 4.6.

### CRITICAL — Security
1. **Zip Slip vulnerability fixed** — `updater.py` now validates all zip paths before extraction (both update + rollback).
2. **Download integrity verification** — Update zips are validated with `is_zipfile()` + `testzip()` before applying.

### HIGH — Scanner Accuracy
3. **ATR calculation fixed** (velocity_scanner) — True Range now uses correct `pd.concat().max(axis=1)` formula instead of broken `Series.combine(max)`.
4. **Gap Recovery scoring fixed** — Was always returning 0 due to circular `gap_low` calculation. Now uses `prior_low` + ATR-based floor.
5. **Market context SMA50/200 fixed** — Changed `period="5d"` to `"1y"` so SMA calculations actually have enough data.
6. **Trend scoring `get_pct()` fixed** — Removed broken `< 1` heuristic; all numeric values now correctly multiplied by 100 (finvizfinance returns decimals).
7. **Gap-and-Go retention fixed** — Was hardcoded to 100; now computed from `prior_high` vs `pm_price`.

### HIGH — Performance
8. **Quick Lookup threaded** — No longer blocks the GUI during report generation.
9. **462 lines of dead code removed** — Six unused `_run_*_scan` methods (all scans go through queue-based `_scan_worker_loop`).
10. **Velocity scanner parallelized** — `ThreadPoolExecutor(max_workers=8)` for ticker scanning, `max_workers=4` for market context. ~8x faster on large universes.
11. **Emotional dip scanner: 3x Finviz calls → 1x** — Reuses cached quote from `analyze_dip_quality()` for SMA200 and RSI checks.
12. **Report generator: leveraged mapping loaded once** — Was loading `leveraged_tickers.json` per-ticker; now loaded once before the loop.

### HIGH — Reliability
13. **Race conditions fixed** — `scan_cancelled` backed by `threading.Event`; result queue cleared between runs; update/rollback guarded against double-click.

### MEDIUM — Robustness
14. **OpenRouter retry logic** — 3 retries with exponential backoff on connection errors, timeouts, 429, 5xx. Error messages now include API error detail.
15. **Bare `except:` → `except Exception:`** — 10 instances across 4 files. No longer swallows `KeyboardInterrupt`/`SystemExit`.
16. **Transactional updates** — Updater now stages files in a temp directory before applying; if staging fails, the real app is untouched.
17. **`_derive_sma200_status` crash-proofed** — Non-numeric `price_vs_sma200` values no longer crash report generation.

### MEDIUM — Config & Project
18. **INSTALL.bat updated to v7.2**.
19. **Legacy config keys clarified** — Comment distinguishing `dip_*` (legacy) from `emotional_*` (active).
20. **Stale presets cleaned** — Removed "Emotional Dip - Bounce"; added "Velocity Pre-Market Hunter"; updated Swing preset to `emotional_*` keys.
21. **Orphaned `fundamentals_helper.py` removed**.
22. **`ClearBlueSkyWin/` added to `.gitignore`**.
23. **requirements.txt tightened** — `pandas>=2.0,<3.0`, `yfinance>=0.2.36`, `pandas-ta>=0.3.14b0`, `chromadb>=0.4,<1.0`.

### LOW — UX Polish
24. **Help is now a scrollable window** — Replaced `messagebox.showinfo` with a proper Toplevel + Text widget.
25. **Keyboard shortcuts** — Enter = Run Scan, Escape = Stop, F1 = Help.
26. **Cross-platform file open** — `os.startfile` replaced with platform-aware helper (Windows/macOS/Linux).
27. **Auto report cleanup** — Reports older than 30 days are auto-removed on startup.
28. **OpenRouter usage tracking** — Token counts logged to console after each API call.

---

### Other
29. **Claude model removed** from OpenRouter options. Models: Gemini 3 Pro Preview (credits) or DeepSeek R1 T2 Chimera (free).
30. **OpenRouter credit display** — Shows remaining balance, model name, and key status below the scan button.
31. **Auto-migration** — Users with Claude selected are auto-switched to Gemini on config load.
32. **USER_MANUAL.md** — Comprehensive manual covering all scanners, settings, config options, scoring, and troubleshooting. Included in the release zip.

---

All v7.0 and v7.1 features included.

*ClearBlueSky v7.2 – made with Claude AI*
