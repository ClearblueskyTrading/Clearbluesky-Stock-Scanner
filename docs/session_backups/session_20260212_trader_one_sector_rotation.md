# Session Backup — 2026-02-12 (Trader One / Sector Rotation)

## Protocol: Backup for today's session. No personal info, API keys, or account IDs.

---

## Summary

- **Trader One** (AI) assigned control of trades; **Trader Two** (user) as counterpart.
- Sector rotation strategy: 2 positions (60/40), bear ETFs when sector negative.
- Rotated from 1 position (XLU) to 2 positions (XLU 60%, XLB 40%).
- All limit orders executed in extended hours as requested.
- Backtest comparison: 1 pos ~+540%, 2 pos ~+282%, 2 pos+bear ~+170% (780 days).

---

## Code Changes (Safe for GitHub)

### sector_rotation.py
- Added `SECTOR_TO_BEAR` (inverse ETFs: SQQQ, FAZ, ERY, LABD, SPXU).
- Added `get_top_n_rotation_tickers(n=2)` for 60/40 split.
- `get_top_rotation_ticker` supports `use_bear_when_negative`.
- `get_rotation_signal_for_report` reads `ptm_rotation_positions`, `ptm_rotation_bear` from config.

### sector_rotation_backtest.py
- Added `--positions 1|2`, `--bear`, `--compare`.
- `run_backtest` supports `n_positions`, `use_bear`.
- Compare mode: 1pos vs 2pos vs 2pos+bear.

### report_generator.py
- Rotation prompt/body shows 2 tickers when `n_positions=2`.
- MASTER/MOMENTUM directives updated for 2 pos + bear.

### PTM_README.md
- Added `ptm_rotation_positions`, `ptm_rotation_bear` to config table.

### .gitignore
- Added `scanner/ptm_rotation_state.json`.
- `user_config.json`, `alpaca_trades.py`, `paper_trading_manager.py` already excluded.

---

## Files Never Committed (Security)

- `scanner/user_config.json` — API keys, preferences
- `scanner/ptm_rotation_state.json` — position state
- `scanner/alpaca_trades.py` — trading (Cursor only)
- `scanner/paper_trading_manager.py` — trading (Cursor only)
