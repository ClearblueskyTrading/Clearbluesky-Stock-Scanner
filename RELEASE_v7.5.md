# ClearBlueSky Stock Scanner v7.5 — Release Notes

**Release date:** 2026-02-08

---

## What's New

### Metrics Bar + Accuracy Tracking
A new dark metrics bar sits below the header showing live accuracy stats:

- **Accuracy %** — What percentage of past picks went up (color coded: green/amber/red)
- **Hits** — Stocks that went up from flagged price
- **Misses** — Stocks that went down
- **Picks** — Total evaluated over the last 7 days

Updates automatically on startup and after every scan.

### Scan History (Long-Term Log)
Every scan now appends a slim record to `reports/scan_history.json`. Over time this builds a searchable dataset of every stock the scanner ever flagged — with scores, prices, sectors, smart money signals, and market conditions at that moment.

### History Report
Click the **History** button to generate a comprehensive report:

- Scans by type and day of week
- Score distribution (Elite/Strong/Good/Decent/Skip)
- Top 15 most flagged tickers with average scores
- Repeat tickers (3+ appearances — persistent signals)
- Price trends: first scan price vs latest price (did it go up?)
- Top 20 highest scores ever recorded
- Sector frequency, market regime history
- Leveraged play suggestions, smart money overlap
- Accuracy rating with best hits and worst misses

Auto-backfills from all existing JSON report files — instant history from day one.

### 30-Day Price History
Fresh 30-day OHLCV data fetched every scan for all your tickers plus 17 core leveraged/market ETFs. Included in the AI prompt as a "sanity check" so the AI can verify entry/target prices make sense vs recent highs and lows.

---

## Upgrade Notes

- **From v7.4:** Drop-in replacement. Your `user_config.json` is preserved. Existing JSON reports are auto-backfilled into scan history on first run.
- **No new dependencies.** All new modules use `yfinance`, `requests`, and stdlib (already installed).

---

*ClearBlueSky v7.5 — Made with Claude AI*
