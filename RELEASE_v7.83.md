# ClearBlueSky Stock Scanner — v7.83 Release Notes

**Release Date:** February 10, 2026

---

## Velocity Trend Growth: Sector-First Momentum Scan

### Sector-first logic

1. **Rank sectors** — Fetches 11 sector SPDRs (XLK, XLF, XLE, etc.) and computes N-day return.
2. **Select leading sectors** — Top 4 by momentum.
3. **Build universe** — S&P 500 stocks in those sectors + sector ETFs + index ETFs (SPY, QQQ, TQQQ, etc.).
4. **Scan** — Run momentum scan on ~160 tickers instead of ~400.

### Curated ETF list

- Replaces full Finviz ETF screener (250+ tickers) with ~45 key ETFs.
- Saves ~1.5 min per scan.
- Index: SPY, QQQ, IWM, DIA, TQQQ, QLD, UPRO, SOXL
- Sector: XLF, XLK, XLE, XLV, XLI, XLP, XLY, XLU, XLB, XLRE, XLC
- Commodities: GDX, GLD, SLV, USO

### New filters (all optional, off by default)

| Filter | Default | Description |
|--------|---------|--------------|
| Require beats SPY | Off | Only stocks outperforming SPY |
| Min volume | 100K | Min average volume |
| Volume above 20d avg | Off | Accumulation confirmation |
| MA stack | Off | Price > EMA10 > EMA20 > EMA50 |
| RSI band | 0–100 (off) | Constrain RSI (e.g. 55–80) |

### Target return

- Range: 1–300%
- Default: 5% (weak-market friendly)
- Use 0 for all momentum (min is 1 in GUI)

---

## Removed: Legacy Trend Scanner

- **Trend - Long-term** removed from scan types.
- **trend_scan_v2.py** deleted.
- Velocity Trend Growth is now the default first scan.

---

## Upgrade

Drop-in replacement — no config changes needed. Your `user_config.json` is never overwritten.

If you had `trend_min_score`, `trend_min_quarter_perf`, or `trend_require_ma_stack` in config, they are no longer used (safe to leave or remove).

---

*ClearBlueSky Stock Scanner — Built with Claude AI*
*GitHub: https://github.com/ClearblueskyTrading/Clearbluesky-Stock-Scanner*
