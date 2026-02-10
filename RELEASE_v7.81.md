# ClearBlueSky Stock Scanner — v7.81 Release Notes

**Release Date:** February 9, 2026

---

## Data Failover Order

### Price/Volume: yfinance → finviz → alpaca

- **data_failover.py** — New module with `get_price_volume()` and `get_price_volume_batch()`.
- **report_generator.py**, **ticker_enrichment.py**, **accuracy_tracker.py** — Use failover instead of Alpaca-first.

### Bars: yfinance → alpaca

- **price_history.py**, **ta_engine.py**, **velocity_scanner.py**, **backtest_db.py**, **chart_engine.py** — Try yfinance first, then Alpaca when keys set.
- **market_intel.py** — ETF snapshots use yfinance first, then Alpaca.

### Versioning

- Version format: 7.81 → 7.82 → 7.83 onward.

---

*ClearBlueSky Stock Scanner — Built with Claude AI*
*GitHub: https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner*
