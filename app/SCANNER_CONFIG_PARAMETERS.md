# ClearBlueSky – Scanner config parameters (all scans)

Single reference of every config parameter used by each scan. Use this for AI refinement or tuning.

---

## Global / shared (used by multiple scans)

| Key | Description | Default | Used by |
|-----|-------------|---------|---------|
| `min_price` | Minimum stock price ($) | 5.0 | Velocity Trend Growth, Swing, Emotional, Pre-Market |
| `max_price` | Maximum stock price ($) | 500.0 | Velocity Trend Growth, Swing, Emotional, Pre-Market |
| `min_avg_volume` | Minimum average volume (stored in thousands in UI; app uses ×1000) | 500000 | Swing, Emotional, Pre-Market |

**Note:** News and analyst ratings are always fetched (Finviz) for all scans that do per-ticker analysis; there are no toggles.

---

## 1. Velocity Trend Growth (`velocity_trend_growth`)

**Purpose:** Momentum scan (sector-first). Ranks sectors by N-day return, then scans S&P 500 stocks + ETFs in leading sectors only. Best run after market close.

| Key | Label | Type | Min | Max | Default | Description |
|-----|-------|------|-----|-----|---------|-------------|
| `vtg_trend_days` | Trend Days | choice | — | — | 20 | 20 or 50 trading days. |
| `vtg_target_return_pct` | Target Return % | float | 1 | 300 | 5 | Minimum N-day return. 5–8% weak markets; 12–15% strong. |
| `vtg_risk_pct` | Risk % of Account | float | 5 | 50 | 30 | Position sizing. |
| `vtg_max_tickers` | Max Tickers | int | 5 | 50 | 20 | Max results returned. |
| `vtg_min_price` | Min Price $ | float | 1 | 100 | 25 | Min price filter. |
| `vtg_max_price` | Max Price $ | float | 50 | 2000 | 600 | Max price filter. |
| `vtg_require_beats_spy` | Require beats SPY | bool | — | — | false | Only stocks outperforming SPY. |
| `vtg_min_volume` | Min Avg Volume (K) | int | 0 | 10000 | 100 | Min average volume (K; app uses ×1000). |
| `vtg_require_volume_confirm` | Volume above 20d avg | bool | — | — | false | Accumulation confirmation. |
| `vtg_require_ma_stack` | Require MA stack | bool | — | — | false | Price > EMA10 > EMA20 > EMA50. |
| `vtg_rsi_min` | RSI min (0=off) | int | 0 | 100 | 0 | RSI filter lower bound. |
| `vtg_rsi_max` | RSI max (100=off) | int | 0 | 100 | 100 | RSI filter upper bound. |

**Data:** Sector-first: ranks 11 sector SPDRs by return, then fetches S&P 500 + curated ETFs. Universe: ~160 tickers (top 4 sectors + index ETFs). Scanner: `velocity_trend_growth.run_velocity_trend_growth_scan`.

---

## 2. Swing – Dips (`swing`)

**Purpose:** Oversold dips with news/analyst check. Uses enhanced dip scanner; best run ~2:30–4:00 PM.

| Key | Label | Type | Min | Max | Default | Description |
|-----|-------|------|-----|-----|---------|-------------|
| `swing_min_score` | Min Score | int | 40 | 90 | 60 | Minimum score for report inclusion. |
| `dip_min_percent` | Min Dip % | float | 0 | 10 | 1.0 | Minimum drop % to count as a dip. |
| `dip_max_percent` | Max Dip % | float | 0 | 15 | 5.0 | Maximum drop % (avoid crashes). |
| `min_price` | Min Price $ | float | 1 | 50 | 5 | Min price. |
| `max_price` | Max Price $ | float | 100 | 1000 | 500 | Max price. |

**Also used (from global):** `min_avg_volume`.  
**In code (no UI slider):** `swing_min_relative_volume` (default 1.0) filters raw dip list by relative volume.  
**Always on:** Per-ticker news and analyst check via `analyze_dip_quality()` (Finviz).

---

## 3. Emotional Dip – Bounce (`emotional`)

**Purpose:** Dips from sentiment only (bounce in 1–2 days). Run ~3:30 PM, buy by 4 PM.

| Key | Label | Type | Min | Max | Default | Description |
|-----|-------|------|-----|-----|---------|-------------|
| `emotional_min_score` | Min Score | int | 50 | 90 | 65 | Minimum score for report. |
| `emotional_dip_min_percent` | Min Dip % | float | 0 | 5 | 1.5 | Min drop % for emotional dip. |
| `emotional_dip_max_percent` | Max Dip % | float | 1 | 10 | 4.0 | Max drop % for emotional dip. |
| `emotional_min_volume_ratio` | Min Rel Vol | float | 1.0 | 5.0 | 1.8 | Minimum relative volume. |
| `emotional_min_upside_to_target` | Min Upside % | float | 5 | 30 | 10.0 | Minimum upside % to analyst target. |
| `emotional_require_above_sma200` | Above SMA200 | bool | — | — | true | Require price above SMA200. |
| `emotional_require_buy_rating` | Require Buy rating | bool | — | — | true | Require Buy/Strong Buy/Outperform/Overweight. |

**Also used (from global):** `min_price`, `max_price`, `min_avg_volume`.  
**Always on:** News + analyst via dip pipeline.

---

## 4. Watchlist 3pm (`watchlist`)

**Purpose:** Watchlist tickers that are down within 0–X% today (slider = max of range). Best run ~3 PM.

| Key | Label | Type | Min | Max | Default | Description |
|-----|-------|------|-----|-----|---------|-------------|
| `watchlist_filter` | Filter | choice | — | — | down_pct | `down_pct` (Down % today) or `all` (All tickers). |
| `watchlist_pct_down_from_open` | Max % down (0–25% range) | float | 0 | 25 | 5 | Max % down for range. Only used when filter is Down % today. Slider disabled when All tickers. |

**Data:** Uses `config["watchlist"]` (list of tickers). Scanner: `watchlist_scanner.run_watchlist_scan`.

---

## 5. Watchlist – All tickers (`watchlist_tickers`)

**Purpose:** Scan all watchlist tickers with no filters. Returns current data for every ticker on the watchlist.

No config parameters (empty `SCAN_PARAM_SPECS["watchlist_tickers"]`). Scanner: `watchlist_scanner.run_watchlist_tickers_scan`.

---

## 6. Velocity Barbell (`velocity_leveraged`)

**Purpose:** Foundation + Runner (or Single Shot) from sector proxy signals. Uses sector ETFs (QQQ, SMH, SPY, etc.) to pick leading theme.

| Key | Label | Type | Min | Max | Default | Description |
|-----|-------|------|-----|-----|---------|-------------|
| `velocity_min_sector_pct` | Min sector % (up or down) | float | -5 | 5 | 0 | Only recommend when leading sector’s Change % is at least this. |
| `velocity_barbell_theme` | Theme | choice | — | — | auto | `auto` \| `barbell` \| `single_shot`. |

**Data:** `velocity_leveraged_arsenal.json` (barbell_combos, single_shot_combos, sector_proxies). Scanner: `velocity_leveraged_scanner.run_velocity_leveraged_scan`.

---

## 7. Pre-Market Volume (`premarket`)

**Purpose:** Unusual pre-market activity (7:00 AM – 9:25 AM). Gap, volume, float, dollar volume.

| Key | Label | Type | Min | Max | Default | Description |
|-----|-------|------|-----|-----|---------|-------------|
| `premarket_min_score` | Min Score | int | 50 | 95 | 70 | Minimum score for report. |
| `premarket_min_volume` | Min PM Vol (K) | int_vol_k | 50 | 500 | 100 | Min pre-market volume (stored as 100000 in config). |
| `premarket_min_relative_volume` | Min Rel Vol | float | 1.0 | 5.0 | 2.0 | Min relative volume. |
| `premarket_min_gap_percent` | Min Gap % | float | 0 | 10 | 2.0 | Min gap % (current vs prior close). |
| `premarket_max_gap_percent` | Max Gap % | float | 5 | 30 | 15.0 | Max gap %. |
| `premarket_min_dollar_volume` | Min $ Vol (K) | int_vol_k | 100 | 5000 | 500 | Min dollar volume (volume × price); stored as 500000. |
| `premarket_min_vol_float_ratio` | Vol/Float | float | 0 | 0.1 | 0.01 | Min volume / float ratio. |
| `premarket_track_sector_heat` | Track sector heat | bool | — | — | true | Aggregate volume by sector. |

**Also used (from global):** `min_price`, `max_price`, `min_avg_volume`.  
**In code but not in slider UI:** `premarket_max_spread_percent` (default 1.0) in `load_config()`.

---

## Report / PDF behavior (all scans)

| Concept | Source | Description |
|---------|--------|-------------|
| Min score for PDF | `{scan}_min_score` | From config: `swing_min_score`, `emotional_min_score`, `premarket_min_score`. Velocity Trend Growth uses 0. |

| Max tickers in PDF | Hardcoded | Top 15 tickers (by score) included in each PDF (`qualifying = qualifying[:15]` in `report_generator.py`). |

Config key used for report min score in `app.py`: `self.config.get(f'{scan_type.lower()}_min_score', 65)`. Scans that use **min_score 0** (no filter): Watchlist, Watchlist 3pm, Watchlist – All tickers, Insider, Velocity Barbell.

---

## Other app settings (not scan-type specific)

- `reports_folder` – Where PDFs are saved (default: `reports` under app dir).
- `play_alarm_on_complete` – Play sound when scan finishes (default: true).
- `alarm_sound_choice` – `"beep"` \| `"asterisk"` \| `"exclamation"` (system-style beeps).
- `finviz_api_key` – Optional Finviz API key.
- **OpenRouter API (AI analysis):** `openrouter_api_key` – API key for OpenRouter (optional; used when sending analysis package to AI). `openrouter_model` – Model: `"google/gemini-3-pro-preview"` or `"anthropic/claude-sonnet-4.5"` (use credits), or `"tngtech/deepseek-r1t2-chimera:free"` (free, no credits). Selectable in Settings under “OpenRouter API (AI analysis)”.
- **Technical analysis in report:** `include_ta_in_report` – When true (default), each ticker in the PDF gets programmatic TA from `ta_engine` (yfinance + pandas-ta): SMAs (20/50/200), RSI, MACD histogram, Bollinger Bands, ATR, OBV, Fib 38/50/62. Set to false in Settings to skip TA and speed up report generation.
- Risk/position (legacy Settings tab): `account_size`, `risk_per_trade_percent`, `max_position_dollars`, `max_daily_loss_dollars`, `max_concurrent_positions`.

---

## File locations

- **Param specs (sliders):** `scan_settings.py` → `SCAN_PARAM_SPECS`.
- **Default values:** `scan_settings.py` → `load_config()` defaults.
- **Stored config:** `user_config.json`.
- **Scan type definitions (dropdown):** `scan_types.json` (or `DEFAULT_SCAN_TYPES` in `scan_settings.py`).

---

## Summary table (config key → scan)

| Key | Trend Growth | Swing | Emotional | Watchlist | Velocity | Pre-Market |
|-----|---------------|-------|-----------|-----------|----------|------------|
| `vtg_trend_days` | ✓ | | | | | |
| `vtg_target_return_pct` | ✓ | | | | | |
| `vtg_min_price` | ✓ | | | | | |
| `vtg_max_price` | ✓ | | | | | |
| `swing_min_score` | | ✓ | | | | |
| `dip_min_percent` | | ✓ | | | | |
| `dip_max_percent` | | ✓ | | | | |
| `emotional_min_score` | | | ✓ | | | |
| `emotional_dip_min_percent` | | | ✓ | | | |
| `emotional_dip_max_percent` | | | ✓ | | | |
| `emotional_min_volume_ratio` | | | ✓ | | | |
| `emotional_min_upside_to_target` | | | ✓ | | | |
| `emotional_require_above_sma200` | | | ✓ | | | |
| `emotional_require_buy_rating` | | | ✓ | | | |
| `watchlist_pct_down_from_open` | | | | ✓ | | |
| `velocity_min_sector_pct` | | | | | ✓ | |
| `velocity_barbell_theme` | | | | | ✓ | |
| `premarket_min_score` | | | | | | ✓ |
| `premarket_min_volume` | | | | | | ✓ |
| `premarket_min_relative_volume` | | | | | | ✓ |
| `premarket_min_gap_percent` | | | | | | ✓ |
| `premarket_max_gap_percent` | | | | | | ✓ |
| `premarket_min_dollar_volume` | | | | | | ✓ |
| `premarket_min_vol_float_ratio` | | | | | | ✓ |
| `premarket_track_sector_heat` | | | | | | ✓ |
| `min_price` | ✓ | ✓ | ✓ | | | ✓ |
| `max_price` | ✓ | ✓ | ✓ | | | ✓ |
| `min_avg_volume` | | ✓ | ✓ | | | ✓ |
