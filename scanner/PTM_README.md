# Paper Trading Manager (PTM) — Cursor project only

**Paper trade only. Swing trade only (no same-day exit).**

## Active Strategies

| Trader | Strategy | Allocation |
|--------|----------|------------|
| **Trader 1** | 3 Stock Rotation | 60% Top 3 + 15% GDX + 15% FCX + 10% cash ($20K) |
| **Trader 2** | Combined | $10K Rotation + $10K Swing ($20K total) |

**Trader 1** — `ptm_mode: single_stock_rotation`. Top 3 leveraged ETFs (weekly momentum), always hold GDX/FCX. 5% stop per rotation position. Run: `python blended_backtest.py --days 780`

**Trader 2** — Combined: $10K per sleeve. **Rotation sleeve:** 60% Top 3 ($6K), 15% GDX ($1.5K), 15% FCX ($1.5K), 10% cash ($1K). **Swing sleeve:** 60% dip ($6K), 15% GDX ($1.5K), 15% FCX ($1.5K), 10% cash ($1K). Combined: $3K GDX, $3K FCX, $2K cash. Rotation: 5% stop. Swing: -2% stop, +3% target, 5d max.

---

## Saved Preset: Hybrid 60/30/10

**Restore via:** `ptm_mode: "rotation"`, `ptm_hybrid_mode: true`

| Sleeve | % | $ at 20K | Strategy |
|--------|---|----------|
| **Swing** | 60% | $12K | Emotional Dip: Tier 1 setups (90+), conviction sizing $2K/$5K/$10K, stop -2%, target +3%, 5d max |
| **Sector** | 30% | $6K | 5-day rotation: 1 pos bull = 100% top sector (leveraged when available). XLU, XLB, XLE have no 3x → use sector ETF |
| **Cash** | 10% | $2K | Dry powder for dips, drawdown buffer |

**Order type:** LIMIT preferred (avoid slippage). Use limit at or near bid/ask.

**Leveraged tickers:** Suggest leveraged alternatives when applicable — NVDA→NVDU/NVDL, AAPL→AAPU, MSFT→MSFU, sector→TQQQ/SOXL/ERX/FAS. Same thesis, amplified. Max 3-day hold for leveraged.

**Backtest (780d):** +199% total, 17.8% max DD, ~$51/day avg at $20K. Run: `python hybrid_backtest.py --days 780`

---

## Quick Start

1. **Enable in config** — Add to `user_config.json`:
   ```json
   "ptm_enabled": true,
   "alpaca_api_key": "your-paper-key",
   "alpaca_secret_key": "your-paper-secret"
   ```

2. **Add to Windows startup** — Run once:
   ```powershell
   powershell -ExecutionPolicy Bypass -File "D:\cursor\scripts\Add-PTMToStartup.ps1"
   ```

3. **Or start manually** — From Desktop Agent, click **PTM Daemon**. Or run:
   ```bash
   cd d:\cursor\scanner
   python ptm_daemon.py
   ```

## Schedule (Trader One — 3 Stock Rotation)

When `ptm_schedule_enabled` is true, PTM runs **only** between **8:00 AM – 8:00 PM ET** on **weekdays** (Mon–Fri). Outside that window it sleeps and re-checks every 5 minutes.

| Time (ET) | Activity |
|-----------|----------|
| **8:00 AM** | First run (pre-market). Weekly re-pick if Monday. Check 5% stops, rebalance. |
| **8:00 AM – 9:30 AM** | Pre-market: runs every 15 min (stops, rebalance; limit orders in extended hours). |
| **9:30 AM – 4:00 PM** | Market hours: runs every 15 min. 5% stops checked; any hit → sell. |
| **4:00 PM – 8:00 PM** | After-hours: runs every 15 min (limit orders in AH). |
| **8:00 PM – 8:00 AM** | Off. Daemon sleeps (re-checks every 5 min). |
| **Weekends** | Off. No runs. |

**Config keys** (user_config.json):

| Key | Default | Description |
|-----|---------|-------------|
| `ptm_schedule_enabled` | true | Enforce 8am–8pm window (false = run 24/7). |
| `ptm_schedule_start_hour` | 8 | Start hour (ET). |
| `ptm_schedule_end_hour` | 20 | End hour (ET). 20 = 8 PM. |
| `ptm_schedule_interval_min` | 15 | Minutes between runs when in window. |
| `ptm_schedule_weekdays_only` | true | Skip Sat/Sun. |
| `ptm_run_times` | — | **Optional.** Specific times only, e.g. `["09:35", "12:00", "15:45"]`. T1/T2 run only at these times (within ±2 min). Use when you want to be at your desk for Cursor review. Leave empty for normal interval. |

---

## What It Does

- Runs every **15 minutes** (when in schedule window)
- **Order type:** When `ptm_use_limits` true (default): LIMIT orders with extended_hours for AH execution. Otherwise: market in regular hours.
- Checks positions with Alpaca (stop/target)
- **Swing rule:** No same-day round trip. Never buy 8 AM–4 PM and sell that day (hold overnight minimum)
- Buys from scan reports (`.md` with frontmatter) when under max positions
- Logs to `scanner/ptm_logs/ptm_daemon.log`

## Config (user_config.json)

| Key | Default | Description |
|-----|---------|-------------|
| `ptm_enabled` | false | Enable PTM |
| `ptm_mode` | "single_stock_rotation" | "single_stock_rotation" = 3 Stock Rotation (60% Top 3 + 15% GDX + 15% FCX + 10% cash); "rotation" = 5-day sector; "dip" = stop/target from scans |
| `ptm_rotation_cycle_days` | 5 | Rotation cycle length (5 = weekly) |
| `ptm_rotation_capital` | 20000 | Deploy $ per cycle. **Trader One cap: $20K total** (60/30/10 = $12K/$6K/$2K). |
| `ptm_rotation_stop_pct` | -15 | Sell loser, replace with top sector |
| `ptm_rotation_positions` | 2 | 1 = 100% top sector; 2 = 60/40 top two |
| `ptm_rotation_bear` | true | Use bear ETFs (SQQQ, FAZ, ERY, SPXU) when sector momentum negative |
| `ptm_hybrid_mode` | false | When true: 60% swing, 30% sector, 10% cash. Overrides rotation/dip split. |
| `ptm_use_limits` | true | Prefer limit orders over market (set limit at/near bid for buys, ask for sells). |
| `ptm_extended_hours` | true | Allow AH execution for limit orders (pre-market, after-hours). |
| `ptm_stop_pct` | -2 | Sell if down (dip mode) |
| `ptm_target_pct` | 3 | Sell if up (dip mode) |
| `ptm_max_hold_days` | 5 | Max hold dip mode (stocks); leveraged ETFs use 3 |
| `ptm_min_score` | 85 | Min scan score to buy |
| `ptm_max_positions` | 5 | Max open positions |
| `ptm_position_pct` | 5 | % of buying power per position |
| `ptm_max_position_dollars` | 5000 | Max $ per position |
| `ptm_single_stock_stop_pct` | 5 | Stop loss % (single_stock_rotation mode) |
| `ptm_single_stock_top_n` | 3 | Number of positions (1=100%, 2=60/40, 3=40/35/25) |
| `ptm_schedule_enabled` | true | Only run 8am–8pm ET weekdays |
| `ptm_schedule_start_hour` | 8 | Start hour ET |
| `ptm_schedule_end_hour` | 20 | End hour ET (20 = 8 PM) |
| `ptm_schedule_interval_min` | 15 | Minutes between runs in window |
| `ptm_schedule_weekdays_only` | true | Skip weekends |
| `ptm_trader1_enabled` | true | Run Trader 1 cycle (set false to run only Trader 2) |
| `ptm_trader2_enabled` | true | Run Trader 2 cycle (same schedule) |
| `ptm_trader2_dry_run` | true | **No Trader 2 trades** until set to false |
| `ptm_trader2_capital` | 20000 | Trader 2 allocation base ($) |
| `ptm_notify_before_trade` | false | When true: before each order, write to ptm_logs/pending_trade.txt, play alarm, wait ptm_pre_trade_delay_sec (lets you copy) |
| `ptm_pre_trade_delay_sec` | 15 | Seconds to wait after notification before executing (0 = no wait) |
| `ptm_pre_trade_ai_check` | false | When true: call OpenRouter for OK/CAUTION/ABORT before each order. Uses full context (consensus, rotation, news). ABORT blocks the trade. |
| `ptm_ai_reasoning_enabled` | true | When true: at start of each cycle, AI recommends actions from report + rotation + positions. Logged to ptm_logs/ai_recommendation.txt |
| `alpaca_api_key_trader2` | — | Trader 2 Alpaca key |
| `alpaca_secret_key_trader2` | — | Trader 2 Alpaca secret |

**To enable Trader 2 live trades:** Set `ptm_trader2_dry_run` to `false` in user_config.json.

## Remove from Startup

```powershell
powershell -ExecutionPolicy Bypass -File "D:\cursor\scripts\Remove-PTMFromStartup.ps1"
```
