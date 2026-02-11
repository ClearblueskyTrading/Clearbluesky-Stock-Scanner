# ClearBlueSky Stock Scanner — v7.86 Release Notes

**Release Date:** February 10, 2026

---

## Scanner quality upgrade release

This release tightens setup quality and improves execution context for reports.

### 1) EMA8 added to TA engine

- `ta_engine.py` now computes:
  - `ema8`
  - `price_vs_ema8`
- EMA8 is included in report TA formatting output.

### 2) Velocity Trend Growth: optional SMA200 quality gate

- New config key: `vtg_require_above_sma200` (default: `true`).
- Wired through:
  - GUI/app scan flow (`app.py`)
  - CLI (`scanner_cli.py`)
  - Scanner runtime (`velocity_trend_growth.py`)

This helps filter out weaker momentum names trading below long-term trend support.

### 3) Watchlist scanner: EMA8-aware scoring

- Watchlist scoring now uses a TA snapshot and adds:
  - EMA8 proximity bonus
  - Overextension penalty (for names too far above EMA8)
  - Extra caution for extreme RSI extension

### 4) Velocity pre-market breakout quality improvements

- `velocity_scanner.py` breakout scoring now includes:
  - multi-touch resistance confirmation
  - EMA8 extension penalty for overstretched setups

### 5) Report risk framing improvements

- Reports and JSON analysis package now include:
  - `ema8_status` (`Above` / `Below` / `At` / `N/A`)
  - `invalidation_level` (EMA8/SMA20/ATR-based fallback)
  - setup-quality penalty metadata (`setup_penalty`, reasons, pre-penalty score)
- Report ranking is re-sorted after setup-quality penalties.

### 6) Defaults/docs updates

- `emotional_require_above_sma200` default is now `true` for new configs.
- Updated docs/config templates:
  - `app/SCANNER_CONFIG_PARAMETERS.md`
  - `app/user_config.json.example`
  - `CHANGELOG.md`, `app/CHANGELOG.md`, `README.md`, `README.txt`

### 7) ETF scope + liquidity controls

- Curated ETF universe expanded to include core leveraged **bull + bear/inverse** symbols.
- Scanner ETF paths now enforce a hard minimum average-volume floor of **100,000** shares.
- Pre-market ETF scanning now uses curated ETFs instead of full ETF sweeps, preventing oversized 2000+ ticker runs.

---

## Upgrade

Drop-in replacement — no destructive migration required.
Your local `user_config.json` remains local and is never overwritten by release artifacts.

---

*ClearBlueSky Stock Scanner — Built with Claude AI*
*GitHub: https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner*
