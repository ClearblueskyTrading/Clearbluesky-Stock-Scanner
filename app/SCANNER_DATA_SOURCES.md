# Scanner data sources: failover order

Scanner data uses **yfinance > finviz > alpaca** for price/volume, and **yfinance > alpaca** for historical bars (Finviz does not provide bars).

## Failover order

### Price / volume (single data points)

**Order: yfinance → finviz → alpaca**

- **`data_failover.py`** provides `get_price_volume(ticker)` and `get_price_volume_batch(tickers)`.
- Used by: report generator, ticker enrichment, accuracy tracker.
- First tries yfinance; if missing or invalid, tries finviz; if still missing, tries Alpaca.

### Historical bars (OHLCV)

**Order: yfinance → alpaca**

- Finviz does not provide historical bars.
- Used by: price_history, ta_engine, velocity_scanner, backtest_db, chart_engine.
- First tries yfinance; if missing or insufficient, tries Alpaca when keys are set.

## Module summary

| Module | Data type | Failover order |
|--------|-----------|----------------|
| report_generator | price, volume, change % | yfinance → finviz → alpaca |
| ticker_enrichment | price at report | yfinance → finviz → alpaca |
| accuracy_tracker | current prices (batch) | yfinance → finviz → alpaca |
| price_history | 30-day OHLCV | yfinance → alpaca |
| ta_engine | 6mo OHLCV for TA | yfinance → alpaca |
| velocity_scanner | daily bars (SMA, RSI, etc.) | yfinance → alpaca |
| backtest_db | T+1/T+3/T+5/T+10 fills | yfinance → alpaca |
| chart_engine | OHLC for charts | yfinance → alpaca |
| market_intel | SPY/QQQ ETF snapshots | yfinance → alpaca |

## Rate limits

- **Alpaca:** 60 requests/min, 3/sec in `alpaca_data.py` (market data only).
- **Finviz:** Delays and retries in `finviz_safe.py` and report generator.
- **yfinance:** Polite delays between requests to reduce Yahoo rate-limit issues.

## Implementation

- **`data_failover.py`:** `get_price_volume(ticker)` and `get_price_volume_batch(tickers)` with yfinance → finviz → alpaca.
- **`alpaca_data.py`:** `get_bars()`, `get_price_volume()`; rate-limited.
- **`report_generator.py`:** `get_finviz_data()` uses failover for price/volume.
- **`ticker_enrichment.py`:** `_get_current_price()` uses failover.
- **`accuracy_tracker.py`:** `_get_current_prices()` uses failover batch.
