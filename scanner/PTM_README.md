# Paper Trading Manager (PTM) — Cursor project only

**Paper trade only. Swing trade only (no same-day exit).**

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

## What It Does

- Runs every **15 minutes**
- **Order type:** Market in regular hours (9:30 AM–4 PM ET); limit + extended_hours in pre-market (4–9:30 AM) and after-hours (4–8 PM) — so orders always execute when possible
- Checks positions with Alpaca (stop/target)
- **Swing rule:** No same-day round trip. Never buy 8 AM–4 PM and sell that day (hold overnight minimum)
- Buys from scan reports (`.md` with frontmatter) when under max positions
- Logs to `scanner/ptm_logs/ptm_daemon.log`

## Config (user_config.json)

| Key | Default | Description |
|-----|---------|-------------|
| `ptm_enabled` | false | Enable PTM |
| `ptm_mode` | "dip" | "rotation" = 5-day sector rotation; "dip" = stop/target from scans |
| `ptm_rotation_cycle_days` | 5 | Rotation cycle length (5 = weekly) |
| `ptm_rotation_capital` | 20000 | Deploy $ per cycle |
| `ptm_rotation_stop_pct` | -15 | Sell loser, replace with top sector |
| `ptm_rotation_positions` | 2 | 1 = 100% top sector; 2 = 60/40 top two |
| `ptm_rotation_bear` | true | Use bear ETFs (SQQQ, FAZ, ERY, SPXU) when sector momentum negative |
| `ptm_stop_pct` | -2 | Sell if down (dip mode) |
| `ptm_target_pct` | 3 | Sell if up (dip mode) |
| `ptm_max_hold_days` | 5 | Max hold dip mode (stocks); leveraged ETFs use 3 |
| `ptm_min_score` | 85 | Min scan score to buy |
| `ptm_max_positions` | 5 | Max open positions |
| `ptm_position_pct` | 5 | % of buying power per position |
| `ptm_max_position_dollars` | 5000 | Max $ per position |

## Remove from Startup

```powershell
powershell -ExecutionPolicy Bypass -File "D:\cursor\scripts\Remove-PTMFromStartup.ps1"
```
