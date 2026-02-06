# Velocity Pre-Market Hunter

**Single-command morning scanner.** Run manually when ready (typically 9:00–9:30 AM). Scans the fixed universe, scores 4 signal types per ticker, grades A+ to F, and outputs terminal summary + PDF with order tickets.

---

## Command

```bash
python velocity_scanner.py --scan premarket
```

Run from the `app/` folder. No other options. Takes about 45–60 seconds (or less when APIs are fast).

---

## What It Does (in order)

1. **Market context** – Fetches SPY, QQQ, SMH (SOX proxy), VIX. Shows prior close, pre-market % (if available), regime (LOW FEAR / NORMAL / ELEVATED FEAR), bias (LONG SETUPS FAVORED / CAUTIOUS).
2. **Universe scan** – Scans all 17 tickers (see `SCAN_UNIVERSE` in `velocity_scanner.py`). For each: prior close/volume, pre-market price/volume, prior-day SMA20/50/200, RSI, ATR, Bollinger Bands.
3. **Unified pattern scoring** – Every ticker is scored 0–100 on all 4 signal types; the **highest** score becomes that ticker’s primary signal:
   - **Emotional Gap Recovery** – Gap down 1.5–4%, pre-market recovery, PM volume, above 50 SMA.
   - **Institutional Accumulation** – Small/no gap, PM volume, prior close in top of range, RSI 40–60.
   - **Breakout Pre-Load** – Price near resistance, PM volume.
   - **Gap-and-Go Momentum** – Gap up 2%+, retention, PM volume.
4. **Risk & grading** – Final score = max(signal scores) minus volatility/liquidity/earnings/trend penalties. Grade: A+ (85+), A (75+), B (65+), C (55+), F (&lt;55).
5. **Entry plan** – For A+/A/B: entry zone, position size ($5K / $4K / $3K), target %, stop %, R:R, and **order ticket** (limit + OCO).

---

## Output

- **Terminal** – ASCII summary: market context, Tier 1 (A+ with full detail + order tickets), Tier 2 (A/B), Watchlist (C), Disqualified (F), summary + PDF path.
- **PDF** – Saved to `app/scanner_output/YYYYMMDD_HHMM_premarket.pdf` with same info in print-friendly form.

---

## Configuration (in `velocity_scanner.py`)

- **SCAN_UNIVERSE** – List of 17 tickers (TQQQ, SOXL, SPXL, NVDL, NVDA, TSLA, AMD, META, NFLX, AMZN, GOOGL, COIN, MSTR, AAPL, MSFT, JPM, V). Edit to change universe.
- **POSITION_SIZES** – A+ $5,000, A $4,000, B $3,000.
- **TARGETS** – By signal: gap_recovery 3%, accumulation 2.5%, breakout 4%, gap_go 5%.
- **MIN_STOP_PCT / MAX_STOP_PCT** – 1.5% / 3%.
- **ACCOUNT_SIZE / MAX_RISK_PER_TRADE** – Used for risk sizing (20K / 3%).

---

## Data

- **yfinance** – Pre-market and prior-day data (no API key). Uses `prepost=True` for pre-market when available.
- **Earnings** – Not wired to a calendar yet; earnings penalty is 0 unless you add a calendar (e.g. Alpha Vantage or another source).

---

## Windows

Terminal output uses ASCII only (no Unicode box-drawing or arrows) so it works in the default Windows console (cp1252).

---

*ClearBlueSky – Velocity Pre-Market Hunter*
