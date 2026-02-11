# ClearBlueSky Stock Scanner v7.87 — Bugfix Release

**Date:** 2026-02-11

This release fixes 15 bugs across the scanner and report pipeline discovered during a full-codebase audit. No new features; purely stability, data-correctness, and config-plumbing fixes.

---

## Bug Fixes — Scanners

| File | Bug | Impact |
|------|-----|--------|
| `scanner_cli.py` | Velocity premarket merge iterated dict keys (`"context"`, `"tickers"`) instead of the `tickers` list | Velocity premarket candidates were silently dropped in CLI runs |
| `premarket_volume_scanner.py` | `price` was undefined before dollar-volume calculation | `NameError` crash during premarket scan analysis loop |
| `premarket_volume_scanner.py` | Volume filter used only screener snapshot; now takes `max(screener, live quote)` | Earlier-session scans had stale or zero volume, filtering out valid candidates |
| `premarket_volume_scanner.py` | `ta_change_u` screener filter limited results to stocks that were up only | Gap-down premarket activity was never captured |
| `watchlist_scanner.py` | `_parse_num` did not strip `"x"` suffix from Finviz Rel Volume (e.g. `"1.5x"`) | Relative-volume scoring was always zero for every ticker |
| `enhanced_dip_scanner.py` | Stored raw `stock.get('Ticker')` instead of normalized uppercase | Inconsistent deduplication and downstream ticker mismatches |

## Bug Fixes — Reports & History

| File | Bug | Impact |
|------|-----|--------|
| `report_generator.py` | PDF always used `MASTER_TRADING_REPORT_DIRECTIVE` (swing) instead of scan-specific `directive_block` | Momentum/Velocity scans showed wrong trading guidance in PDF |
| `report_generator.py` | `leveraged_play` stored as bare string; downstream expected `{leveraged_ticker, match_type}` dict | Inconsistent JSON schema; `lp['leveraged_ticker']` crashes on string |
| `report_generator.py` | Leveraged map lookup was case-sensitive (`"aapl"` missed) | Leveraged suggestions missed for lowercase tickers |
| `report_generator.py` | Premarket-specific fields (`gap_percent`, `dollar_volume`, `float_category`, `vol_float_ratio`, etc.) were never copied into report rows | Premarket reports lacked scan-specific metrics |
| `history_analyzer.py` | `leveraged_play` dict used directly as `Counter` key | `TypeError: unhashable type: 'dict'` crash in history analysis |
| `history_analyzer.py` | Checked non-existent smart-money keys (`wsb`, `insider_filings`); actual keys are `wsb_rank`, `wsb_mentions`, `form4_count_90d` | WSB and insider counts were always 0 in history reports |

## Bug Fixes — Config & Data Plumbing

| File | Bug | Impact |
|------|-----|--------|
| `ticker_enrichment.py` | `_get_current_price` and `enrich_scan_results` did not accept/forward `config` | Alpaca failover could not use API keys from user config |
| `market_intel.py` | `_fetch_market_snapshot` and `_fetch_overnight_markets` called `has_alpaca_keys()` / `get_price_volume_batch()` without config | Alpaca market data fallback failed when keys were in config (not env) |
| `price_history.py` | `pct_change` division used `if first_close` (truthy check) instead of `!= 0` | Edge-case division-by-zero possible for delisted/zero-price tickers |

## Docs

- Version labels updated: `USER_MANUAL.md`, `CLAUDE_AI_GUIDE.md`, `DOCKER.md`, `INSTALL.bat` were stuck on v7.7; now show v7.87.

---

## Files Changed

```
app/app.py                    – version bump 7.86 → 7.87
app/scanner_cli.py            – premarket merge fix
app/watchlist_scanner.py      – _parse_num "x" suffix
app/enhanced_dip_scanner.py   – ticker normalization
app/premarket_volume_scanner.py – price def, volume source, direction bias
app/history_analyzer.py       – leveraged_play + smart_money keys
app/report_generator.py       – directive, leveraged schema, premarket metrics, config
app/ticker_enrichment.py      – config passthrough
app/market_intel.py           – config passthrough
app/price_history.py          – division guard
USER_MANUAL.md                – v7.7 → v7.87
CLAUDE_AI_GUIDE.md            – v7.7 → v7.87
DOCKER.md                     – v7.7 → v7.87
INSTALL.bat                   – v7.7 → v7.87
README.md                     – v7.87
README.txt                    – v7.87
CHANGELOG.md                  – v7.87 section
app/CHANGELOG.md              – v7.87 section
```

---

*ClearBlueSky Stock Scanner v7.87 — Made with Claude AI*
